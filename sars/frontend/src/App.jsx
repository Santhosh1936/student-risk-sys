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
  if (loading) return null;
  if (!user)   return <Navigate to="/login" replace />;
  return <Navigate to={user.role === "student" ? "/student" : "/teacher"} replace />;
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

          {/* Any unknown URL → home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
