import { useEffect, useState } from "react";
import api from "../api/client";

/** Student/Ministry Administrator use case: "calculate distance to
 * schools". Backed by POST /api/distance/, which itself reuses the
 * placement_algorithm package's eligible_schools() directly. */
export default function NearbySchools({ studentId }) {
  const [schools, setSchools] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!studentId) return;
    api
      .post("distance/", { student_id: studentId, max_candidates: 5 })
      .then((res) => setSchools(res.data))
      .catch(() => setError("Could not calculate distances."));
  }, [studentId]);

  if (error) return <div className="alert alert-error">{error}</div>;
  if (!schools) return <p className="muted">Calculating nearby schools...</p>;

  return (
    <div>
      {schools.map((s) => (
        <div className="school-list-item" key={s.school_id}>
          <span>
            {s.name} <span className="muted">({s.category.replace("_", "-")})</span>
          </span>
          <span>{s.distance_km} km</span>
        </div>
      ))}
    </div>
  );
}
