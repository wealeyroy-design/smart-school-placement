import { useAuth } from "../auth/AuthContext";

const ROLE_LABELS = {
  student: "Student",
  parent: "Parent/Guardian",
  school_admin: "School Administrator",
  ministry_admin: "Ministry Administrator",
};

/** Title bar at the top of each role-based portal (Module 4). */
export default function PageHeader({ title, subtitle }) {
  const { user } = useAuth();
  const today = new Date().toLocaleDateString(undefined, {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  return (
    <header className="page-header">
      <div>
        <div className="page-eyebrow">{ROLE_LABELS[user?.role] || "Portal"}</div>
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      <div className="page-header-date">{today}</div>
    </header>
  );
}
