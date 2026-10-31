import BarChart from "../../components/BarChart";
import BaselineComparison from "../../components/BaselineComparison";

const CATEGORY_ORDER = ["national", "extra_county", "county", "sub_county"];
const APPEAL_TONES = { pending: "accent", under_review: "muted", approved: "primary", rejected: "danger" };

function label(category) {
  return category.replace("_", "-").replace(/^\w/, (c) => c.toUpperCase());
}

export default function AnalyticsDashboard({ analytics }) {
  if (!analytics) return <p className="muted">Loading analytics...</p>;

  const { latest_run, total_students, students_with_results, total_schools, total_placements, pending_appeals } = analytics;
  const categories = [...analytics.by_school_category].sort(
    (a, b) => CATEGORY_ORDER.indexOf(a.category) - CATEGORY_ORDER.indexOf(b.category)
  );
  const counties = [...analytics.by_student_county].sort((a, b) => b.avg_distance_km - a.avg_distance_km);

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
        <div className="stat-tile tile-accent">
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
            <div className="value">{latest_run.median_distance_km} km</div>
            <div className="label">Median distance</div>
          </div>
          <div className="stat-tile">
            <div className="value">{(latest_run.proportion_within_threshold * 100).toFixed(1)}%</div>
            <div className="label">Within 50km</div>
          </div>
          <div className="stat-tile">
            <div className="value">{(latest_run.overall_slot_utilization * 100).toFixed(1)}%</div>
            <div className="label">Slot utilization</div>
          </div>
        </div>
      )}

      {latest_run && <BaselineComparison run={latest_run} />}

      <div className="grid-2 analytics-grid">
        <div className="panel">
          <h3>Slot utilization by school category</h3>
          <BarChart
            max={100}
            rows={categories.map((row) => ({
              label: label(row.category),
              value: row.utilization * 100,
              display: `${(row.utilization * 100).toFixed(1)}%`,
            }))}
          />
          <table className="compact">
            <thead>
              <tr>
                <th>Category</th>
                <th>Schools</th>
                <th>Filled / Capacity</th>
                <th>Avg. rating</th>
              </tr>
            </thead>
            <tbody>
              {categories.map((row) => (
                <tr key={row.category}>
                  <td>{label(row.category)}</td>
                  <td>{row.schools}</td>
                  <td>{row.filled_slots} / {row.total_capacity}</td>
                  <td>{row.avg_rating?.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="panel">
          <h3>Average distance by student county (equity view)</h3>
          <BarChart
            rows={counties.map((row) => ({
              label: row.student__county,
              value: row.avg_distance_km,
              display: `${row.avg_distance_km.toFixed(1)} km · ${row.placements}`,
              tone: row.avg_distance_km > 50 ? "danger" : row.avg_distance_km > 25 ? "accent" : "primary",
            }))}
          />
          <p className="muted chart-note">
            Bar = average home-to-school distance; number after the dot = students placed. Counties above
            50 km are highlighted for follow-up.
          </p>
        </div>
      </div>

      <div className="panel">
        <h3>Appeals by status</h3>
        <BarChart
          emptyText="No appeals have been submitted."
          rows={analytics.appeals_by_status.map((row) => ({
            label: row.status.replace("_", " ").replace(/^\w/, (c) => c.toUpperCase()),
            value: row.count,
            tone: APPEAL_TONES[row.status] || "primary",
          }))}
        />
      </div>
    </div>
  );
}
