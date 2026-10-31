import { useCallback, useEffect, useState } from "react";
import api from "../api/client";
import { useAuth } from "../auth/AuthContext";
import OfflineMap from "./OfflineMap";

/* Nearby schools, measured from the student's REGISTERED HOME.
 *
 * The placement algorithm ranks schools by distance from a student's home,
 * so this view starts from that same home location (loaded from the
 * student's own profile). The browser's Geolocation API is still available
 * as an optional, temporary alternative -- "Use my current location
 * instead" -- but it only changes this view. It never changes the saved
 * home or any placement. A manual entry box covers devices where location
 * is blocked. No map account, API key or internet connection is needed.
 */

const MAX_CANDIDATES = 6;

function describeGeolocationError(error) {
  if (!error) return "Could not determine your location.";
  if (error.code === 1) {
    return "Location permission was blocked. Allow location for this site from your browser's address bar, or type your coordinates below.";
  }
  if (error.code === 2) {
    return "Your device could not determine a position. Type your coordinates below instead.";
  }
  if (error.code === 3) {
    return "Locating took too long. Try again, or type your coordinates below.";
  }
  return "Could not determine your location. Type your coordinates below.";
}

function osmLink(lat, lon) {
  return `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=13/${lat}/${lon}`;
}

function originDescription(origin, home) {
  if (!origin) return "";
  if (origin.kind === "home") {
    return `Showing schools near your registered home${home?.county ? ` (${home.county})` : ""}.`;
  }
  if (origin.kind === "device") {
    return "Showing schools near your current device location - this is not your registered home.";
  }
  return "Showing schools near the coordinates you entered - this is not your registered home.";
}

export default function LocationFinder() {
  const { user } = useAuth();
  const isStudent = user?.role === "student";
  const [home, setHome] = useState(null); // { latitude, longitude, county } from the student's profile
  const [origin, setOrigin] = useState(null); // { latitude, longitude, kind: home | device | manual }
  const [results, setResults] = useState(null);
  const [status, setStatus] = useState(isStudent ? "loading" : "idle"); // loading | idle | locating
  const [error, setError] = useState("");
  const [manual, setManual] = useState({ latitude: "", longitude: "" });

  const lookup = useCallback((point, kind) => {
    setError("");
    setStatus("locating");
    return api
      .post("distance/", {
        latitude: point.latitude,
        longitude: point.longitude,
        max_candidates: MAX_CANDIDATES,
      })
      .then((res) => {
        setResults(res.data);
        setOrigin({ latitude: point.latitude, longitude: point.longitude, kind });
      })
      .catch(() => {
        setError("Could not calculate distances from that point. Please try again.");
      })
      .finally(() => setStatus("idle"));
  }, []);

  // On first load, start from the student's registered home.
  useEffect(() => {
    let cancelled = false;
    // Only student accounts have a registered home; other roles start from GPS / manual entry.
    if (!isStudent) return undefined;
    api
      .get("students/me/")
      .then((res) => {
        if (cancelled) return;
        const { home_latitude, home_longitude, county } = res.data;
        if (home_latitude == null || home_longitude == null) {
          setStatus("idle");
          return;
        }
        const homePoint = {
          latitude: Number(home_latitude),
          longitude: Number(home_longitude),
          county,
        };
        setHome(homePoint);
        lookup(homePoint, "home");
      })
      .catch(() => {
        // No student profile (for example a parent account): fall back to GPS / manual entry.
        if (!cancelled) setStatus("idle");
      });
    return () => {
      cancelled = true;
    };
  }, [lookup, isStudent]);

  function useMyLocation() {
    if (!("geolocation" in navigator)) {
      setError("This browser cannot share a location. Type your coordinates below instead.");
      return;
    }
    setError("");
    setStatus("locating");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        lookup(
          { latitude: position.coords.latitude, longitude: position.coords.longitude },
          "device"
        );
      },
      (geoError) => {
        setStatus("idle");
        setError(describeGeolocationError(geoError));
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 }
    );
  }

  function submitManual(event) {
    event.preventDefault();
    const latitude = Number.parseFloat(manual.latitude);
    const longitude = Number.parseFloat(manual.longitude);
    if (Number.isNaN(latitude) || Number.isNaN(longitude)) {
      setError("Enter both a latitude and a longitude as numbers.");
      return;
    }
    if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
      setError("Latitude must be between -90 and 90, longitude between -180 and 180.");
      return;
    }
    lookup({ latitude, longitude }, "manual");
  }

  const busy = status !== "idle";
  const fromHome = origin?.kind === "home";

  return (
    <div className="location-finder">
      {origin && results && <p className="origin-note"><strong>{originDescription(origin, home)}</strong></p>}

      {!home && status === "idle" && !origin && (
        <p className="muted">
          No home location is saved for this account. Use your current location or type coordinates
          below to look up nearby schools.
        </p>
      )}

      <div className="finder-actions">
        {home && !fromHome && (
          <button type="button" className="btn-primary" onClick={() => lookup(home, "home")} disabled={busy}>
            Back to my home
          </button>
        )}
        <button
          type="button"
          className={home && !fromHome ? "btn-secondary" : home ? "btn-secondary" : "btn-primary"}
          onClick={useMyLocation}
          disabled={busy}
        >
          {status === "locating"
            ? "Locating..."
            : home
              ? "Use my current location instead"
              : "Use my current location"}
        </button>
      </div>

      {home && (
        <p className="muted">
          Using your current location only changes this view. Your saved home and your placement are
          not affected.
        </p>
      )}

      {error && <div className="alert alert-error">{error}</div>}

      {status === "loading" && <p className="muted">Loading your home location...</p>}
      {status === "locating" && <p className="muted">Finding nearby schools...</p>}

      {origin && results && (
        <>
          <div className="stat-row">
            <div className="stat-tile">
              <div className="value">{origin.latitude.toFixed(4)}</div>
              <div className="label">{fromHome ? "Home latitude" : "Latitude"}</div>
            </div>
            <div className="stat-tile">
              <div className="value">{origin.longitude.toFixed(4)}</div>
              <div className="label">{fromHome ? "Home longitude" : "Longitude"}</div>
            </div>
            <div className="stat-tile">
              <div className="value">{results.length}</div>
              <div className="label">Schools within reach</div>
            </div>
          </div>

          <OfflineMap origin={origin} schools={results} />

          <div className="school-list">
            {results.map((school) => (
              <div className="school-list-item" key={school.school_id}>
                <span>
                  {school.name} <span className="muted">({school.category.replace("_", "-")})</span>
                  {school.county ? <span className="muted"> &middot; {school.county}</span> : null}
                </span>
                <span>
                  {school.distance_km} km
                  <a
                    className="map-link"
                    href={osmLink(school.latitude, school.longitude)}
                    target="_blank"
                    rel="noreferrer"
                    title="Open this school in OpenStreetMap (no sign-in required)"
                  >
                    map
                  </a>
                </span>
              </div>
            ))}
          </div>

          {results.length === 0 && <p className="muted">No schools were found near that point.</p>}
        </>
      )}

      <details className="manual-coordinates">
        <summary>Enter coordinates manually</summary>
        <form onSubmit={submitManual}>
          <label>
            Latitude
            <input
              type="number"
              step="any"
              value={manual.latitude}
              placeholder="-1.2864"
              onChange={(e) => setManual({ ...manual, latitude: e.target.value })}
            />
          </label>
          <label>
            Longitude
            <input
              type="number"
              step="any"
              value={manual.longitude}
              placeholder="36.8835"
              onChange={(e) => setManual({ ...manual, longitude: e.target.value })}
            />
          </label>
          <button type="submit" className="btn-primary" disabled={busy}>
            Find schools
          </button>
        </form>
      </details>
    </div>
  );
}
