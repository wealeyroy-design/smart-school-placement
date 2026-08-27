import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const ROLE_LABELS = {
  student: "Student",
  parent: "Parent/Guardian",
  school_admin: "School Administrator",
  ministry_admin: "Ministry Administrator",
};

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="navbar">
      <div className="navbar-brand">Smart School Placement</div>
      {user && (
        <div className="navbar-right">
          <span>
            {user.first_name || user.username} &middot; {ROLE_LABELS[user.role] || user.role}
          </span>
          <button onClick={handleLogout}>Log out</button>
        </div>
      )}
    </div>
  );
}
