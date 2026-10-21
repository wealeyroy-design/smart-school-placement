import { useState } from "react";
import api from "../api/client";
import OfflineMap from "./OfflineMap";

/* "Use my current location" without any map account.
 *
 * The browser's own Geolocation API reports the device's position after a
 * single permission prompt - no Google Maps sign-in, no API key, no cost.
 * The coordinates go straight to POST /api/distance/, which reuses the
 * placement algorithm's own distance maths to rank the nearest schools.
 * A manual entry box is provided for devices where location is blocked.
 */

const LAST_LOCATION_KEY = "ssp_last_location";
const MAX_CANDIDATES = 6;

function readLastLocation() {
  try {
    const raw = localStorage.getItem(LAST_LOCATION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

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

export default function LocationFinder() {
  const [origin, setOrigin] = useState(readLastLocation);
  const [results, setResults] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | locating
  const [error, setError] = useState("");
  const [manual, setManual] = useState({ latitude: "", longitude: "" });

  function lookup(point) {
    setError("");
    setStatus("locating");
    api
      .post("distance/", {
        latitude: point.latitude,
        longitude: point.longitude,
        max_candidates: MAX_CANDIDATES,
      })
      .then((res) => {
        setResults(res.data);
        setOrigin(point);
        localStorage.setItem(LAST_LOCATION_KEY, JSON.stringify(point));
      })
      .catch(() => {
        setStatus("idle");
        setError("Could not calculate distances from that point. Please try again.");
      });
  }

  function useMyLocation() {
    if (!("geolocation" in navigator)) {
      setError("This browser cannot share a location. Type your coordinates below instead.");
      return;
    }
    setError("");
    setStatus("locating");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        lookup({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: Math.round(position.coords.accuracy),
        });
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
    lookup({ latitude, longitude });
  }

  return (
    <div className="location-finder">
      <div className="finder-actions">
        <button type="button" className="btn-primary" onClick={useMyLocation} disabled={status === "locating"}>
          {status === "locating" ? "Locating..." : "Use my current location"}
        </button>
        {origin && (
          <button type="button" className="btn-secondary" onClick={() => lookup(origin)} disabled={status === "locating"}>
            Use last location
          </button>
        )}
      </div>

      <p className="muted">
        Your browser will ask permission to share a location once. No map account, no sign-in and no
        internet connection are required.
      </p>

      {error && <div className="alert alert-error">{error}</div>}

      {status === "locating" && <p className="muted">Working out where you are...</p>}

      {origin && results && (
        <>
          <div className="stat-row">
            <div className="stat-tile">
              <div className="value">{origin.latitude.toFixed(4)}</div>
              <div className="label">Your latitude</div>
            </div>
            <div className="stat-tile">
              <div className="value">{origin.longitude.toFixed(4)}</div>
              <div className="label">Your longitude</div>
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

          {results.length === 0 && (
            <p className="muted">No schools were found near that point.</p>
          )}
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
          <button type="submit" className="btn-primary">
            Find schools
          </button>
        </form>
      </details>
    </div>
  );
}
