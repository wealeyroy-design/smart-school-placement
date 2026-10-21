import { useCallback, useEffect, useState } from "react";
import api from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
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

  return (
    <>
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
        <div className="grid-2">
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
              <table>
                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Distance</th>
                  </tr>
                </thead>
                <tbody>
                  {placedStudents.map((p) => (
                    <tr key={p.id}>
                      <td>{p.student_name}</td>
                      <td>{p.distance_km.toFixed(1)} km</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </>
  );
}
