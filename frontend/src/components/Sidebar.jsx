import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const ROLE_LABELS = {
  student: "Student",
  parent: "Parent/Guardian",
  school_admin: "School Administrator",
  ministry_admin: "Ministry Administrator",
};

const LINKS = {
  student: [["profile", "Profile"], ["placement", "Placement"], ["nearby", "Nearby schools"], ["appeals", "Appeals"]],
  parent: [["children", "My children"], ["placement", "Placement"], ["appeals", "Appeals"]],
  school_admin: [["schools", "My schools"], ["details", "Capacity & details"], ["placed", "Placed students"]],
  ministry_admin: [["run", "Run placement"], ["analytics", "Analytics"], ["appeals", "Appeals"]],
};

export default function Sidebar({ open, onClose }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const name = user.first_name || user.username;

  function go(id) {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
    onClose();
  }

  return (
    <aside className={`sidebar ${open ? "open" : ""}`}>
      <div className="sidebar-brand">Smart School Placement</div>
      <nav className="sidebar-nav">
        <div className="sidebar-heading">Overview</div>
        {(LINKS[user.role] || []).map(([id, label]) => (
          <button key={id} className="sidebar-link" onClick={() => go(id)}>{label}</button>
        ))}
      </nav>
      <div className="sidebar-user">
        <div className="avatar">{name[0]?.toUpperCase()}</div>
        <div className="sidebar-user-text">
          <strong>{name}</strong>
          <span>{ROLE_LABELS[user.role] || user.role}</span>
        </div>
        <button className="sidebar-logout" onClick={() => { logout(); navigate("/login"); }}>Log out</button>
      </div>
    </aside>
  );
}
