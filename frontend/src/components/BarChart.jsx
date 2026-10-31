/** Lightweight horizontal bar chart built from plain HTML/CSS, so the
 * analytics views need no extra charting dependency.
 *
 * rows: [{ label, value, display?, tone? }] -- tone: "primary" | "accent" | "danger" | "muted"
 */
export default function BarChart({ rows, max, unit = "", emptyText = "No data yet." }) {
  if (!rows || rows.length === 0) return <p className="muted">{emptyText}</p>;
  const top = max ?? Math.max(...rows.map((r) => r.value), 0) ?? 1;
  return (
    <div className="bar-chart">
      {rows.map((r) => {
        const pct = top > 0 ? Math.max(0, Math.min(100, (r.value / top) * 100)) : 0;
        return (
          <div className="bar-row" key={r.label}>
            <div className="bar-label" title={r.label}>{r.label}</div>
            <div className="bar-track">
              <div className={`bar-fill tone-${r.tone || "primary"}`} style={{ width: `${pct}%` }} />
            </div>
            <div className="bar-value">{r.display ?? `${r.value}${unit}`}</div>
          </div>
        );
      })}
    </div>
  );
}
