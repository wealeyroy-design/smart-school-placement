import { useState } from "react";
import api from "../../api/client";

export default function StudentRegistrationForm({ onRegistered }) {
  const [form, setForm] = useState({ county: "", home_latitude: "", home_longitude: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function update(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
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
        <p className="muted">
          Tip: you can find your coordinates by right-clicking your location on Google Maps.
        </p>
        <button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : "Complete registration"}
        </button>
      </form>
    </div>
  );
}
