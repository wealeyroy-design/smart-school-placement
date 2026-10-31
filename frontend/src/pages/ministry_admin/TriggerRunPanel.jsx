import { useState } from "react";
import api from "../../api/client";
import BaselineComparison from "../../components/BaselineComparison";

export default function TriggerRunPanel({ onCompleted }) {
  const [meritWeight, setMeritWeight] = useState(0.6);
  const [maxDistance, setMaxDistance] = useState(300);
  const [maxCandidates, setMaxCandidates] = useState(15);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function handleTrigger() {
    setRunning(true);
    setError("");
    setResult(null);
    try {
      const { data } = await api.post("placement-runs/trigger/", {
        merit_weight: meritWeight,
        proximity_weight: Math.round((1 - meritWeight) * 100) / 100,
        max_distance_km: maxDistance,
        max_candidates: maxCandidates,
      });
      setResult(data);
      onCompleted?.();
    } catch (err) {
      setError(err?.response?.data?.detail || err?.response?.data?.error_message || "Placement run failed.");
    } finally {
      setRunning(false);
    }
  }

  const proximity = 1 - meritWeight;

  return (
    <div>
      <p className="muted">
        Runs the proximity-weighted Gale-Shapley matching engine (Module 3) against every student with
        exam results on file. This replaces the current allocation.
      </p>

      <div className="weight-panel">
        <div className="weight-labels">
          <span>
            Merit weight <strong>{meritWeight.toFixed(2)}</strong>
          </span>
          <span>
            Proximity weight <strong>{proximity.toFixed(2)}</strong>
          </span>
        </div>
        <input
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={meritWeight}
          aria-label="Merit weight"
          onChange={(e) => setMeritWeight(parseFloat(e.target.value))}
        />
        <div className="weight-split" aria-hidden="true">
          <div className="weight-merit" style={{ width: `${meritWeight * 100}%` }}>Merit</div>
          <div className="weight-proximity" style={{ width: `${proximity * 100}%` }}>Proximity</div>
        </div>
      </div>

      <div className="grid-2">
        <label>
          Max search distance (km)
          <input type="number" value={maxDistance} onChange={(e) => setMaxDistance(Number(e.target.value))} />
        </label>
        <label>
          Candidate schools per student
          <input type="number" value={maxCandidates} onChange={(e) => setMaxCandidates(Number(e.target.value))} />
        </label>
      </div>
      <button className="btn-primary" onClick={handleTrigger} disabled={running} style={{ marginTop: "1rem" }}>
        {running ? "Running placement..." : "Run placement algorithm"}
      </button>

      {error && <div className="alert alert-error" style={{ marginTop: "1rem" }}>{error}</div>}

      {result && (
        <div className="run-result">
          <div className="alert alert-success">
            Run #{result.id} completed: {result.students_placed} of {result.students_considered} students placed.
          </div>
          <div className="stat-row">
            <div className="stat-tile">
              <div className="value">{result.students_placed}/{result.students_considered}</div>
              <div className="label">Students placed</div>
            </div>
            <div className="stat-tile">
              <div className="value">{result.average_distance_km} km</div>
              <div className="label">Avg. distance</div>
            </div>
            <div className="stat-tile">
              <div className="value">{(result.proportion_within_threshold * 100).toFixed(1)}%</div>
              <div className="label">Within 50km</div>
            </div>
            <div className="stat-tile">
              <div className="value">{result.is_stable ? "Yes" : "No"}</div>
              <div className="label">Stable matching</div>
            </div>
          </div>
          <BaselineComparison run={result} />
        </div>
      )}
    </div>
  );
}
