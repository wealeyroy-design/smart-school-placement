import { Navigate, Route, Routes } from "react-router-dom";
import { useState } from "react";
import Sidebar from "./components/Sidebar";
import { useAuth } from "./auth/AuthContext";
import ProtectedRoute, { roleHome } from "./auth/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import StudentPortal from "./pages/student/StudentPortal";
import SchoolAdminPortal from "./pages/school_admin/SchoolAdminPortal";
import MinistryAdminPortal from "./pages/ministry_admin/MinistryAdminPortal";

function Home() {
  const { user } = useAuth();
  return <Navigate to={roleHome(user.role)} replace />;
}

export default function App() {
  const { user } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <div className={user ? "app-shell with-sidebar" : "app-shell"}>
      {user && <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />}
      {user && (
        <button className="menu-toggle" aria-label="Menu" onClick={() => setMenuOpen((v) => !v)}>☰</button>
      )}
      <div className="page-content">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Home />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student"
            element={
              <ProtectedRoute roles={["student", "parent"]}>
                <StudentPortal />
              </ProtectedRoute>
            }
          />
          <Route
            path="/school-admin"
            element={
              <ProtectedRoute roles={["school_admin"]}>
                <SchoolAdminPortal />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ministry-admin"
            element={
              <ProtectedRoute roles={["ministry_admin"]}>
                <MinistryAdminPortal />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </div>
  );
}
