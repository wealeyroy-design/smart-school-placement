export default function AnalyticsDashboard({ analytics }) {
  if (!analytics) return <p className="muted">Loading analytics...</p>;

  const { latest_run, total_students, students_with_results, total_schools, total_placements, pending_appeals } = analytics;

  return (
    <div>
      <div className="stat-row">
        <div className="stat-tile">
          <div className="value">{total_students}</div>
          <div className="label">Registered students</div>
        </div>
        <div className="stat-tile">
          <div className="value">{students_with_results}</div>
          <div className="label">With results uploaded</div>
        </div>
        <div className="stat-tile">
          <div className="value">{total_schools}</div>
          <div className="label">Registered schools</div>
        </div>
        <div className="stat-tile">
          <div className="value">{total_placements}</div>
          <div className="label">Total placements</div>
        </div>
        <div className="stat-tile">
          <div className="value">{pending_appeals}</div>
          <div className="label">Pending appeals</div>
        </div>
      </div>

      {latest_run && (
        <div className="stat-row">
          <div className="stat-tile">
            <div className="value">{latest_run.average_distance_km} km</div>
            <div className="label">Latest run: avg. distance</div>
          </div>
          <div className="stat-tile">
            <div className="value">{(latest_run.proportion_within_threshold * 100).toFixed(0)}%</div>
            <div className="label">Within 50km</div>
          </div>
          <div className="stat-tile">
            <div className="value">{(latest_run.overall_slot_utilization * 100).toFixed(1)}%</div>
            <div className="label">Slot utilization</div>
          </div>
        </div>
      )}

      <div className="grid-2">
        <div>
          <h3>By school category</h3>
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th>Schools</th>
                <th>Filled / Capacity</th>
                <th>Utilization</th>
              </tr>
            </thead>
            <tbody>
              {analytics.by_school_category.map((row) => (
                <tr key={row.category}>
                  <td>{row.category.replace("_", "-")}</td>
                  <td>{row.schools}</td>
                  <td>{row.filled_slots} / {row.total_capacity}</td>
                  <td>{(row.utilization * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div>
          <h3>By student county (equity view)</h3>
          <table>
            <thead>
              <tr>
                <th>County</th>
                <th>Placements</th>
                <th>Avg. distance</th>
              </tr>
            </thead>
            <tbody>
              {analytics.by_student_county.map((row) => (
                <tr key={row.student__county}>
                  <td>{row.student__county}</td>
                  <td>{row.placements}</td>
                  <td>{row.avg_distance_km.toFixed(1)} km</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
