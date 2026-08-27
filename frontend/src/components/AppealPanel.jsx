import { useState } from "react";
import api from "../api/client";

const STATUS_BADGE = {
  pending: "badge-pending",
  under_review: "badge-review",
  approved: "badge-approved",
  rejected: "badge-rejected",
};

export default function AppealPanel({ studentId, appeals, onSubmitted, canSubmit = true }) {
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await api.post("appeals/", { student: studentId, reason });
      setReason("");
      onSubmitted?.();
    } catch (err) {
      setError(err?.response?.data?.detail || "Could not submit appeal.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      {appeals && appeals.length > 0 && (
        <table style={{ marginBottom: "1rem" }}>
          <thead>
            <tr>
              <th>Submitted</th>
              <th>Reason</th>
              <th>Status</th>
              <th>Resolution</th>
            </tr>
          </thead>
          <tbody>
            {appeals.map((a) => (
              <tr key={a.id}>
                <td>{new Date(a.created_at).toLocaleDateString()}</td>
                <td>{a.reason}</td>
                <td>
                  <span className={`badge ${STATUS_BADGE[a.status] || ""}`}>{a.status.replace("_", " ")}</span>
                </td>
                <td>{a.resolution_notes || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {canSubmit && (
        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert-error">{error}</div>}
          <label>
            Submit a new appeal
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why you're appealing this placement..."
              required
            />
          </label>
          <button type="submit" disabled={submitting || !reason.trim()}>
            {submitting ? "Submitting..." : "Submit appeal"}
          </button>
        </form>
      )}
    </div>
  );
}
