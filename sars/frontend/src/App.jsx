// frontend/src/App.jsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import StudentDashboard from "./pages/student/StudentDashboard";
import TeacherDashboard from "./pages/teacher/TeacherDashboard";
import "./styles/global.css";

// Root redirect: if logged in → correct dashboard; if not → login
function RootRedirect() {
  const { user, loading } = useAuth();
  if (loading) return (
    <div style={{
      display: 'flex', alignItems: 'center',
      justifyContent: 'center', minHeight: '100vh',
      background: '#0f172a',
    }}>
      <div style={{
        width: 40, height: 40,
        border: '3px solid #334155',
        borderTop: '3px solid #3b82f6',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
  if (!user)   return <Navigate to="/login" replace />;
  return <Navigate to={user.role === "student" ? "/student" : "/teacher"} replace />;
}

function NotFoundPage() {
  return (
    <div style={{
      minHeight: "100vh", display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      background: "#0a0f1e", color: "#f1f5f9", textAlign: "center",
    }}>
      <div style={{ fontSize: 72, marginBottom: 16 }}>404</div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8, color: "#f1f5f9" }}>Page Not Found</h2>
      <p style={{ color: "#64748b", fontSize: 14, marginBottom: 32 }}>
        The page you are looking for does not exist.
      </p>
      <a href="/" style={{
        background: "#38bdf8", color: "#0a0f1e", borderRadius: 8,
        padding: "11px 28px", fontSize: 14, fontWeight: 700,
        textDecoration: "none",
      }}>
        Go to Home
      </a>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/"       element={<RootRedirect />} />
          <Route path="/login"  element={<LoginPage />} />

          {/* Student routes — all nested under /student/* */}
          <Route
            path="/student/*"
            element={
              <ProtectedRoute role="student">
                <StudentDashboard />
              </ProtectedRoute>
            }
          />

          {/* Teacher routes — all nested under /teacher/* */}
          <Route
            path="/teacher/*"
            element={
              <ProtectedRoute role="teacher">
                <TeacherDashboard />
              </ProtectedRoute>
            }
          />

          {/* Unknown URLs → 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
