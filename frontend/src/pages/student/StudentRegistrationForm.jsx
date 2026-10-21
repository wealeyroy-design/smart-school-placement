import { useState } from "react";
import api from "../../api/client";

export default function StudentRegistrationForm({ onRegistered }) {
  const [form, setForm] = useState({ county: "", home_latitude: "", home_longitude: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [locating, setLocating] = useState(false);

  function update(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  function fillMyLocation() {
    setError("");
    if (!("geolocation" in navigator)) {
      setError("This browser cannot share a location. Type your coordinates below instead.");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setForm((f) => ({
          ...f,
          home_latitude: position.coords.latitude.toFixed(6),
          home_longitude: position.coords.longitude.toFixed(6),
        }));
        setLocating(false);
      },
      (geoError) => {
        setLocating(false);
        if (geoError.code === 1) {
          setError(
            "Location permission was blocked. Allow location for this site from your browser's address bar, or type your coordinates below."
          );
        } else {
          setError("Could not determine your location. Type your coordinates below instead.");
        }
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 }
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await api.post("students/me/", {
        county: form.county,
        home_latitude: parseFloat(form.home_latitude),
        home_longitude: parseFloat(form.home_longitude),
      });
      onRegistered();
    } catch (err) {
      setError(err?.response?.data?.detail || "Could not save your registration.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card">
      <h2>Complete your registration</h2>
      <p className="muted">
        Provide your home location so the placement algorithm can weigh proximity alongside your exam
        results (Module 1: Student Registration).
      </p>
      {error && <div className="alert alert-error">{error}</div>}
      <form onSubmit={handleSubmit}>
        <label>
          County
          <input value={form.county} onChange={update("county")} required placeholder="e.g. Nairobi" />
        </label>
        <div className="grid-2">
          <label>
            Home latitude
            <input
              type="number"
              step="any"
              value={form.home_latitude}
              onChange={update("home_latitude")}
              required
              placeholder="e.g. -1.2921"
            />
          </label>
          <label>
            Home longitude
            <input
              type="number"
              step="any"
              value={form.home_longitude}
              onChange={update("home_longitude")}
              required
              placeholder="e.g. 36.8219"
            />
          </label>
        </div>
        <div className="finder-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={fillMyLocation}
            disabled={locating}
          >
            {locating ? "Locating..." : "Fill in my current location"}
          </button>
        </div>
        <p className="muted">
          Your browser asks permission once - no map account, no sign-in, no internet connection
          needed. You can also type the coordinates manually.
        </p>
        <button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : "Complete registration"}
        </button>
      </form>
    </div>
  );
}
