import { useCallback, useEffect, useState } from "react";
import api from "../../api/client";
import AppealPanel from "../../components/AppealPanel";
import LocationFinder from "../../components/LocationFinder";
import NearbySchools from "../../components/NearbySchools";
import PageHeader from "../../components/PageHeader";
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
      <PageHeader
        title={`Welcome, ${profile.full_name}`}
        subtitle="View your exam results and secondary school placement, explore nearby schools and track appeals."
      />

      <div className="card">
        <h2 id="profile">Your profile</h2>
        <div className="profile-grid">
          <div>
            <span>Full name</span>
            <strong>{profile.full_name}</strong>
          </div>
          <div>
            <span>Username</span>
            <strong>{profile.username}</strong>
          </div>
          <div>
            <span>Home county</span>
            <strong>{profile.county}</strong>
          </div>
          <div>
            <span>Home coordinates</span>
            <strong>
              {Number(profile.home_latitude).toFixed(4)}, {Number(profile.home_longitude).toFixed(4)}
            </strong>
          </div>
        </div>
        <div className="stat-row">
          <div className="stat-tile">
            <div className="value">{profile.has_results ? Number(profile.exam_score).toFixed(1) : "—"}</div>
            <div className="label">Exam score (out of 500)</div>
          </div>
          <div className="stat-tile">
            <div className="value">{profile.has_results ? "Uploaded" : "Pending"}</div>
            <div className="label">Results status</div>
          </div>
          <div className="stat-tile">
            <div className="value">{placement ? "Placed" : placement === null ? "Awaiting" : "…"}</div>
            <div className="label">Placement status</div>
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

      <div className="card">
        <h2 id="locate">Find schools near my location</h2>
        <LocationFinder />
      </div>

      {placement && (
        <div className="card">
          <h2 id="appeals">Appeals</h2>
          <AppealPanel studentId={profile.id} appeals={appeals} onSubmitted={loadAppeals} />
        </div>
      )}
    </>
  );
}
