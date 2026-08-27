import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

/** Guards a route: redirects to /login if not authenticated, and to the
 * user's own portal home if their role doesn't match what's required
 * (rather than showing a bare "forbidden" page). */
export default function ProtectedRoute({ roles, children }) {
  const { user, loading } = useAuth();

  if (loading) return <div className="page-loading">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) {
    return <Navigate to={roleHome(user.role)} replace />;
  }
  return children;
}

export function roleHome(role) {
  switch (role) {
    case "student":
    case "parent":
      return "/student";
    case "school_admin":
      return "/school-admin";
    case "ministry_admin":
      return "/ministry-admin";
    default:
      return "/login";
  }
}
