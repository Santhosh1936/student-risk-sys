// frontend/src/components/ProtectedRoute.jsx
//
// Wraps any route that requires authentication.
// If not logged in → redirect to /login.
// If wrong role → redirect to correct dashboard.
// While loading → show spinner (prevents flash of wrong page).
//
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children, role }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "center",
        height: "100vh", background: "#0f172a",
      }}>
        <div style={{
          width: 40, height: 40, border: "3px solid #334155",
          borderTop: "3px solid #38bdf8", borderRadius: "50%",
          animation: "spin 0.8s linear infinite",
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  // If a specific role is required and user has the wrong one, redirect them home
  if (role && user.role !== role) {
    return <Navigate to={user.role === "student" ? "/student" : "/teacher"} replace />;
  }

  return children;
}
