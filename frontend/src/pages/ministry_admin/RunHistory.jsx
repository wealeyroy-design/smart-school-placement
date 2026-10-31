const STATUS_BADGE = {
  completed: "badge-approved",
  failed: "badge-rejected",
  running: "badge-review",
  pending: "badge-pending",
};

/** Every placement run is recorded as an auditable PlacementRun row. */
export default function RunHistory({ runs }) {
  if (!runs) return <p className="muted">Loading run history...</p>;
  if (runs.length === 0) return <p className="muted">No placement runs yet.</p>;
  const fmt = (v, d = 1) => (v == null ? "—" : Number(v).toFixed(d));
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Run</th>
            <th>Date</th>
            <th>Weights (merit / proximity)</th>
            <th>Placed</th>
            <th>Avg. distance</th>
            <th>Baseline avg.</th>
            <th>Within 50 km</th>
            <th>Stable</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((r) => (
            <tr key={r.id}>
              <td><strong>#{r.id}</strong></td>
              <td>{new Date(r.started_at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}</td>
              <td>{fmt(r.merit_weight, 2)} / {fmt(r.proximity_weight, 2)}</td>
              <td>{r.students_placed}/{r.students_considered}</td>
              <td>{fmt(r.average_distance_km)} km</td>
              <td>{fmt(r.baseline_average_distance_km)} km</td>
              <td>{r.proportion_within_threshold == null ? "—" : `${(r.proportion_within_threshold * 100).toFixed(1)}%`}</td>
              <td>{r.is_stable == null ? "—" : r.is_stable ? "Yes" : "No"}</td>
              <td><span className={`badge ${STATUS_BADGE[r.status] || ""}`}>{r.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
