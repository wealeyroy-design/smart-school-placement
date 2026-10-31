import { useCallback, useEffect, useState } from "react";
import api from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import BarChart from "../../components/BarChart";
import PageHeader from "../../components/PageHeader";
import SchoolForm from "./SchoolForm";

export default function SchoolAdminPortal() {
  const { user } = useAuth();
  const [schools, setSchools] = useState(undefined);
  const [selectedId, setSelectedId] = useState(null);
  const [placedStudents, setPlacedStudents] = useState(undefined);
  const [showAddForm, setShowAddForm] = useState(false);

  const loadSchools = useCallback(() => {
    api.get("schools/?page_size=200").then((res) => {
      const all = res.data.results ?? res.data;
      const mine = all.filter((s) => s.administrator === user.id);
      setSchools(mine);
      if (mine.length > 0 && !selectedId) setSelectedId(mine[0].id);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.id]);

  useEffect(() => {
    loadSchools();
  }, [loadSchools]);

  useEffect(() => {
    if (!selectedId) return;
    setPlacedStudents(undefined);
    api.get(`schools/${selectedId}/placed_students/`).then((res) => setPlacedStudents(res.data));
  }, [selectedId]);

  if (schools === undefined) return <p className="page-loading">Loading...</p>;

  const selected = schools.find((s) => s.id === selectedId);
  const utilization = selected && selected.capacity ? (selected.filled_slots / selected.capacity) * 100 : 0;
  const avgDistance =
    placedStudents && placedStudents.length
      ? placedStudents.reduce((sum, p) => sum + p.distance_km, 0) / placedStudents.length
      : null;
  const within50 = placedStudents ? placedStudents.filter((p) => p.distance_km <= 50).length : 0;

  return (
    <>
      <PageHeader
        title="School Administrator Portal"
        subtitle="Manage your school's details and capacity, and view the students placed in it."
      />

      <div className="card">
        <h2 id="schools">Your schools</h2>
        {schools.length === 0 ? (
          <p className="muted">You don't manage any schools yet. Add one below.</p>
        ) : (
          <select value={selectedId ?? ""} onChange={(e) => setSelectedId(Number(e.target.value))}>
            {schools.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.filled_slots}/{s.capacity} filled)
              </option>
            ))}
          </select>
        )}
        <div style={{ marginTop: "0.9rem" }}>
          <button className="btn-secondary" onClick={() => setShowAddForm((v) => !v)}>
            {showAddForm ? "Cancel" : "+ Add a school"}
          </button>
        </div>
        {showAddForm && (
          <div style={{ marginTop: "1rem" }}>
            <SchoolForm
              onSaved={() => {
                setShowAddForm(false);
                loadSchools();
              }}
            />
          </div>
        )}
      </div>

      {selected && (
        <div className="card">
          <h2 id="overview">{selected.name}</h2>
          <p className="muted" style={{ marginTop: "-0.4rem" }}>
            {selected.county} County &middot; {selected.category.replace("_", "-")} school &middot; performance
            rating {selected.performance_rating.toFixed(1)}
          </p>
          <div className="stat-row">
            <div className="stat-tile">
              <div className="value">{selected.capacity}</div>
              <div className="label">Total capacity</div>
            </div>
            <div className="stat-tile">
              <div className="value">{selected.filled_slots}</div>
              <div className="label">Slots filled</div>
            </div>
            <div className="stat-tile">
              <div className="value">{selected.available_slots}</div>
              <div className="label">Slots available</div>
            </div>
            <div className="stat-tile">
              <div className="value">{avgDistance == null ? "—" : `${avgDistance.toFixed(1)} km`}</div>
              <div className="label">Avg. student distance</div>
            </div>
          </div>
          <BarChart
            max={100}
            rows={[{ label: "Capacity used", value: utilization, display: `${utilization.toFixed(0)}%` }]}
          />
        </div>
      )}

      {selected && (
        <div className="grid-2 school-grid">
          <div className="card">
            <h2 id="details">Capacity & details</h2>
            <SchoolForm school={selected} onSaved={loadSchools} />
          </div>

          <div className="card">
            <h2 id="placed">Placed students ({placedStudents?.length ?? "…"})</h2>
            {placedStudents === undefined ? (
              <p className="muted">Loading...</p>
            ) : placedStudents.length === 0 ? (
              <p className="muted">No students placed here yet.</p>
            ) : (
              <>
                <p className="muted" style={{ marginTop: 0 }}>
                  {within50} of {placedStudents.length} placed students live within 50 km of the school.
                </p>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Student</th>
                        <th>Home county</th>
                        <th>Score</th>
                        <th>Distance</th>
                        <th>Match</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...placedStudents]
                        .sort((a, b) => (b.student_exam_score ?? 0) - (a.student_exam_score ?? 0))
                        .map((p) => (
                          <tr key={p.id}>
                            <td className="nowrap">{p.student_name}</td>
                            <td>{p.student_county}</td>
                            <td>{p.student_exam_score?.toFixed(1)}</td>
                            <td>{p.distance_km.toFixed(1)} km</td>
                            <td>{(p.composite_score * 100).toFixed(0)}%</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
