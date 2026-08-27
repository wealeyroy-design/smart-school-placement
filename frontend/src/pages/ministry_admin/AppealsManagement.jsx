import { useState } from "react";
import api from "../../api/client";

const STATUS_BADGE = {
  pending: "badge-pending",
  under_review: "badge-review",
  approved: "badge-approved",
  rejected: "badge-rejected",
};

export default function AppealsManagement({ appeals, onChanged }) {
  const [notesById, setNotesById] = useState({});
  const [busyId, setBusyId] = useState(null);

  async function resolve(id, status) {
    setBusyId(id);
    try {
      await api.post(`appeals/${id}/resolve/`, {
        status,
        resolution_notes: notesById[id] || "",
      });
      onChanged();
    } finally {
      setBusyId(null);
    }
  }

  if (!appeals) return <p className="muted">Loading appeals...</p>;
  if (appeals.length === 0) return <p className="muted">No appeals have been submitted.</p>;

  return (
    <table>
      <thead>
        <tr>
          <th>Student</th>
          <th>Reason</th>
          <th>Status</th>
          <th>Resolution notes</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {appeals.map((a) => (
          <tr key={a.id}>
            <td>{a.student_name}</td>
            <td style={{ maxWidth: 260 }}>{a.reason}</td>
            <td>
              <span className={`badge ${STATUS_BADGE[a.status] || ""}`}>{a.status.replace("_", " ")}</span>
            </td>
            <td>
              {a.status === "pending" || a.status === "under_review" ? (
                <input
                  placeholder="Optional note"
                  value={notesById[a.id] || ""}
                  onChange={(e) => setNotesById((m) => ({ ...m, [a.id]: e.target.value }))}
                  style={{ width: "100%" }}
                />
              ) : (
                a.resolution_notes || "—"
              )}
            </td>
            <td>
              {(a.status === "pending" || a.status === "under_review") && (
                <div style={{ display: "flex", gap: "0.4rem" }}>
                  <button className="btn-secondary" disabled={busyId === a.id} onClick={() => resolve(a.id, "approved")}>
                    Approve
                  </button>
                  <button className="btn-danger" disabled={busyId === a.id} onClick={() => resolve(a.id, "rejected")}>
                    Reject
                  </button>
                </div>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
