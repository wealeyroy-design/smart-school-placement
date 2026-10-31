import { useCallback, useEffect, useState } from "react";
import api from "../../api/client";
import LocationFinder from "../../components/LocationFinder";
import PageHeader from "../../components/PageHeader";
import AnalyticsDashboard from "./AnalyticsDashboard";
import AppealsManagement from "./AppealsManagement";
import RunHistory from "./RunHistory";
import StudentResults from "./StudentResults";
import TriggerRunPanel from "./TriggerRunPanel";

export default function MinistryAdminPortal() {
  const [analytics, setAnalytics] = useState(undefined);
  const [appeals, setAppeals] = useState(undefined);
  const [runs, setRuns] = useState(undefined);

  const loadAnalytics = useCallback(() => {
    api.get("analytics/").then((res) => setAnalytics(res.data));
  }, []);

  const loadAppeals = useCallback(() => {
    api.get("appeals/?page_size=200").then((res) => setAppeals(res.data.results ?? res.data));
  }, []);

  const loadRuns = useCallback(() => {
    api.get("placement-runs/?page_size=10").then((res) => setRuns(res.data.results ?? res.data));
  }, []);

  useEffect(() => {
    loadAnalytics();
    loadAppeals();
    loadRuns();
  }, [loadAnalytics, loadAppeals, loadRuns]);

  return (
    <>
      <PageHeader
        title="Ministry Administrator Portal"
        subtitle="Run placements, manage exam results, monitor national placement analytics and resolve appeals."
      />

      <div className="card">
        <h2 id="run">Run placement algorithm</h2>
        <TriggerRunPanel
          onCompleted={() => {
            loadAnalytics();
            loadRuns();
          }}
        />
      </div>

      <div className="card">
        <h2 id="history">Placement run history</h2>
        <RunHistory runs={runs} />
      </div>

      <div className="card">
        <h2 id="results">Students &amp; exam results</h2>
        <StudentResults onChanged={loadAnalytics} />
      </div>

      <div className="card">
        <h2 id="analytics">Placement analytics</h2>
        <AnalyticsDashboard analytics={analytics} />
      </div>

      <div className="card">
        <h2 id="appeals">Appeals</h2>
        <AppealsManagement
          appeals={appeals}
          onChanged={() => {
            loadAppeals();
            loadAnalytics();
          }}
        />
      </div>

      <div className="card">
        <h2 id="locate">Distance checker</h2>
        <p className="muted">
          "Calculate distance to schools" from any point, using the placement algorithm's own
          distance scoring.
        </p>
        <LocationFinder />
      </div>
    </>
  );
}
