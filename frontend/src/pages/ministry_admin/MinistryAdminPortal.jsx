import { useCallback, useEffect, useState } from "react";
import api from "../../api/client";
import AnalyticsDashboard from "./AnalyticsDashboard";
import AppealsManagement from "./AppealsManagement";
import TriggerRunPanel from "./TriggerRunPanel";

export default function MinistryAdminPortal() {
  const [analytics, setAnalytics] = useState(undefined);
  const [appeals, setAppeals] = useState(undefined);

  const loadAnalytics = useCallback(() => {
    api.get("analytics/").then((res) => setAnalytics(res.data));
  }, []);

  const loadAppeals = useCallback(() => {
    api.get("appeals/?page_size=200").then((res) => setAppeals(res.data.results ?? res.data));
  }, []);

  useEffect(() => {
    loadAnalytics();
    loadAppeals();
  }, [loadAnalytics, loadAppeals]);

  return (
    <>
      <div className="card">
        <h2 id="run">Run placement algorithm</h2>
        <TriggerRunPanel
          onCompleted={() => {
            loadAnalytics();
          }}
        />
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
    </>
  );
}
