import { useCallback, useEffect, useState } from "react";
import api from "../../api/client";
import AppealPanel from "../../components/AppealPanel";
import NearbySchools from "../../components/NearbySchools";
import PlacementCard from "../../components/PlacementCard";
import StudentRegistrationForm from "./StudentRegistrationForm";

export default function StudentSelfView() {
  const [profile, setProfile] = useState(undefined); // undefined = loading, null = not registered
  const [placement, setPlacement] = useState(undefined);
  const [appeals, setAppeals] = useState([]);

  const loadProfile = useCallback(() => {
    api
      .get("students/me/")
      .then((res) => setProfile(res.data))
      .catch(() => setProfile(null));
  }, []);

  const loadPlacement = useCallback(() => {
    api
      .get("placements/me/")
      .then((res) => setPlacement(res.data))
      .catch(() => setPlacement(null));
  }, []);

  const loadAppeals = useCallback(() => {
    api.get("appeals/").then((res) => setAppeals(res.data.results ?? res.data));
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  useEffect(() => {
    if (profile) {
      loadPlacement();
      loadAppeals();
    }
  }, [profile, loadPlacement, loadAppeals]);

  if (profile === undefined) return <p className="page-loading">Loading...</p>;
  if (profile === null) return <StudentRegistrationForm onRegistered={loadProfile} />;

  return (
    <>
      <div className="card">
        <h2 id="profile">Your profile</h2>
        <div className="stat-row">
          <div className="stat-tile">
            <div className="value">{profile.county}</div>
            <div className="label">County</div>
          </div>
          <div className="stat-tile">
            <div className="value">{profile.has_results ? profile.exam_score : "—"}</div>
            <div className="label">Exam score</div>
          </div>
        </div>
        {!profile.has_results && (
          <div className="alert alert-info">
            Your exam results haven't been uploaded yet. Placement can't run until an administrator
            uploads your score.
          </div>
        )}
      </div>

      <div className="card">
        <h2 id="placement">Your placement</h2>
        <PlacementCard placement={placement} loading={placement === undefined} />
      </div>

      {profile.has_results && (
        <div className="card">
          <h2 id="nearby">Nearby schools</h2>
          <NearbySchools studentId={profile.id} />
        </div>
      )}

      {placement && (
        <div className="card">
          <h2 id="appeals">Appeals</h2>
          <AppealPanel studentId={profile.id} appeals={appeals} onSubmitted={loadAppeals} />
        </div>
      )}
    </>
  );
}
