import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const ROLE_LABELS = {
  student: "Student",
  parent: "Parent/Guardian",
  school_admin: "School Administrator",
  ministry_admin: "Ministry Administrator",
};

const LINKS = {
  student: [
    ["profile", "Profile"],
    ["placement", "Placement"],
    ["nearby", "Nearby schools"],
    ["locate", "Find near me"],
    ["appeals", "Appeals"],
  ],
  parent: [
    ["children", "My children"],
    ["placement", "Placement"],
    ["locate", "Find near me"],
    ["appeals", "Appeals"],
  ],
  school_admin: [
    ["schools", "My schools"],
    ["overview", "School overview"],
    ["details", "Capacity & details"],
    ["placed", "Placed students"],
  ],
  ministry_admin: [
    ["run", "Run placement"],
    ["history", "Run history"],
    ["results", "Students & results"],
    ["analytics", "Analytics"],
    ["appeals", "Appeals"],
    ["locate", "Distance checker"],
  ],
};

export default function Sidebar({ open, onClose }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const name = [user.first_name, user.last_name].filter(Boolean).join(" ") || user.username;
  const links = LINKS[user.role] || [];
  const [active, setActive] = useState(links[0]?.[0]);

  function go(id) {
    setActive(id);
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
    onClose();
  }

  return (
    <aside className={`sidebar ${open ? "open" : ""}`}>
      <div className="sidebar-brand">Smart School Placement</div>
      <nav className="sidebar-nav">
        <div className="sidebar-heading">Overview</div>
        {links.map(([id, label]) => (
          <button key={id} className={`sidebar-link ${active === id ? "active" : ""}`} onClick={() => go(id)}>
            {label}
          </button>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="avatar">{name[0]?.toUpperCase()}</div>
          <div className="sidebar-user-text">
            <strong>{name}</strong>
            <span>{ROLE_LABELS[user.role] || user.role}</span>
          </div>
        </div>
        <button className="sidebar-logout" onClick={() => { logout(); navigate("/login"); }}>
          <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          <span>Log out</span>
        </button>
      </div>
    </aside>
  );
}
