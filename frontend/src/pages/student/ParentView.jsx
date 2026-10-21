import { useCallback, useEffect, useState } from "react";
import api from "../../api/client";
import AppealPanel from "../../components/AppealPanel";
import PlacementCard from "../../components/PlacementCard";

export default function ParentView() {
  const [children, setChildren] = useState(undefined);
  const [selectedId, setSelectedId] = useState(null);
  const [placement, setPlacement] = useState(undefined);
  const [appeals, setAppeals] = useState([]);

  useEffect(() => {
    api.get("students/").then((res) => {
      const list = res.data.results ?? res.data;
      setChildren(list);
      if (list.length > 0) setSelectedId(list[0].id);
    });
  }, []);

  const loadPlacement = useCallback(() => {
    if (!selectedId) return;
    setPlacement(undefined);
    api
      .get("placements/")
      .then((res) => {
        const all = res.data.results ?? res.data;
        setPlacement(all.find((p) => p.student === selectedId) || null);
      })
      .catch(() => setPlacement(null));
  }, [selectedId]);

  const loadAppeals = useCallback(() => {
    if (!selectedId) return;
    api.get("appeals/").then((res) => {
      const all = res.data.results ?? res.data;
      setAppeals(all.filter((a) => a.student === selectedId));
    });
  }, [selectedId]);

  useEffect(() => {
    loadPlacement();
    loadAppeals();
  }, [selectedId, loadPlacement, loadAppeals]);

  if (children === undefined) return <p className="page-loading">Loading...</p>;

  if (children.length === 0) {
    return (
      <div className="alert alert-info">
        No children are linked to your account yet. Ask your child to select you as their parent/guardian
        when they register, or contact a Ministry Administrator.
      </div>
    );
  }

  const selected = children.find((c) => c.id === selectedId);

  return (
    <>
      <div className="card">
        <h2 id="children">Your children</h2>
        <select value={selectedId ?? ""} onChange={(e) => setSelectedId(Number(e.target.value))}>
          {children.map((c) => (
            <option key={c.id} value={c.id}>
              {c.full_name} ({c.county})
            </option>
          ))}
        </select>
      </div>

      {selected && (
        <div className="card">
          <h2 id="placement">{selected.full_name}'s placement</h2>
          <PlacementCard placement={placement} loading={placement === undefined} />
        </div>
      )}

      {placement && (
        <div className="card">
          <h2 id="appeals">Appeals</h2>
          <AppealPanel studentId={selectedId} appeals={appeals} onSubmitted={loadAppeals} />
        </div>
      )}
    </>
  );
}
