import BarChart from "./BarChart";

/** Section 2.3's evaluation: the same cohort allocated by the
 * proximity-weighted engine versus the merit-only, geography-blind
 * baseline that simulates the current placement process. */
export default function BaselineComparison({ run }) {
  if (!run || run.baseline_average_distance_km == null) return null;
  const ours = run.average_distance_km;
  const base = run.baseline_average_distance_km;
  const reduction = base > 0 ? ((base - ours) / base) * 100 : 0;
  return (
    <div className="comparison">
      <div className="comparison-head">
        <h3>Proximity-weighted vs. merit-only baseline</h3>
        <span className="reduction-pill">{reduction.toFixed(1)}% shorter average distance</span>
      </div>
      <div className="grid-2">
        <div>
          <div className="chart-title">Average placement distance (km)</div>
          <BarChart
            rows={[
              { label: "Proximity-weighted", value: ours, display: `${ours.toFixed(1)} km` },
              { label: "Merit-only baseline", value: base, display: `${base.toFixed(1)} km`, tone: "danger" },
            ]}
          />
        </div>
        <div>
          <div className="chart-title">Students placed within 50 km</div>
          <BarChart
            max={100}
            rows={[
              {
                label: "Proximity-weighted",
                value: run.proportion_within_threshold * 100,
                display: `${(run.proportion_within_threshold * 100).toFixed(1)}%`,
              },
              {
                label: "Merit-only baseline",
                value: run.baseline_proportion_within_threshold * 100,
                display: `${(run.baseline_proportion_within_threshold * 100).toFixed(1)}%`,
                tone: "danger",
              },
            ]}
          />
        </div>
      </div>
    </div>
  );
}
