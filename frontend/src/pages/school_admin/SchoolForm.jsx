import { useState } from "react";
import api from "../../api/client";

const CATEGORIES = [
  { value: "national", label: "National" },
  { value: "extra_county", label: "Extra-County" },
  { value: "county", label: "County" },
  { value: "sub_county", label: "Sub-County" },
];

export default function SchoolForm({ school, onSaved }) {
  const isEdit = Boolean(school);
  const [form, setForm] = useState({
    name: school?.name ?? "",
    category: school?.category ?? "county",
    county: school?.county ?? "",
    latitude: school?.latitude ?? "",
    longitude: school?.longitude ?? "",
    capacity: school?.capacity ?? "",
    performance_rating: school?.performance_rating ?? "",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function update(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    const payload = {
      ...form,
      latitude: parseFloat(form.latitude),
      longitude: parseFloat(form.longitude),
      capacity: parseInt(form.capacity, 10),
      performance_rating: parseFloat(form.performance_rating),
    };
    try {
      if (isEdit) {
        await api.patch(`schools/${school.id}/`, payload);
      } else {
        await api.post("schools/", payload);
      }
      onSaved();
    } catch (err) {
      setError(JSON.stringify(err?.response?.data) || "Could not save school.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="alert alert-error">{error}</div>}
      <label>
        School name
        <input value={form.name} onChange={update("name")} required />
      </label>
      <div className="grid-2">
        <label>
          Category
          <select value={form.category} onChange={update("category")}>
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          County
          <input value={form.county} onChange={update("county")} required />
        </label>
      </div>
      <div className="grid-2">
        <label>
          Latitude
          <input type="number" step="any" value={form.latitude} onChange={update("latitude")} required />
        </label>
        <label>
          Longitude
          <input type="number" step="any" value={form.longitude} onChange={update("longitude")} required />
        </label>
      </div>
      <div className="grid-2">
        <label>
          Capacity (slots)
          <input type="number" min="1" value={form.capacity} onChange={update("capacity")} required />
        </label>
        <label>
          Performance rating (0-100)
          <input
            type="number"
            min="0"
            max="100"
            step="any"
            value={form.performance_rating}
            onChange={update("performance_rating")}
            required
          />
        </label>
      </div>
      <button type="submit" disabled={submitting}>
        {submitting ? "Saving..." : isEdit ? "Save changes" : "Add school"}
      </button>
    </form>
  );
}
