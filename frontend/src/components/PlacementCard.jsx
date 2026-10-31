export default function PlacementCard({ placement, loading }) {
  if (loading) return <p className="muted">Loading placement...</p>;

  if (!placement) {
    return (
      <div className="alert alert-info">
        No placement result yet. This appears once the Ministry Administrator has run the placement
        algorithm and results have been uploaded.
      </div>
    );
  }

  const { school, distance_km, composite_score } = placement;
  return (
    <div>
      <div className="placement-head">
        <div>
          <h3>{school.name}</h3>
          <p className="muted" style={{ marginTop: -8 }}>
            {school.county} County &middot; {school.category.replace("_", "-")} school
          </p>
        </div>
        <span className="badge badge-approved">Placed</span>
      </div>
      <div className="stat-row">
        <div className="stat-tile">
          <div className="value">{distance_km.toFixed(1)} km</div>
          <div className="label">Distance from home</div>
        </div>
        <div className="stat-tile">
          <div className="value">{(composite_score * 100).toFixed(0)}%</div>
          <div className="label">Composite match score</div>
        </div>
        <div className="stat-tile">
          <div className="value">{school.performance_rating.toFixed(0)}</div>
          <div className="label">School performance rating</div>
        </div>
      </div>
      <p className="muted">
        The composite match score combines your exam performance with how close the school is to your
        registered home, using the weights set by the Ministry of Education.
      </p>
    </div>
  );
}
