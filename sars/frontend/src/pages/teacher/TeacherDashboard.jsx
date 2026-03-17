// frontend/src/pages/teacher/TeacherDashboard.jsx
import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import DashboardLayout from "../../components/DashboardLayout";
import api from "../../services/api";
import RiskMonitorPage from "./RiskMonitorPage";
import StudentDetailPage from "./StudentDetailPage";
import InterventionsPage from "./InterventionsPage";
import AnalyticsPage from "./AnalyticsPage";

const NAV = [
  { label: "My Students",    icon: "👥",  path: "/teacher/students" },
  { label: "Risk Monitor",   icon: "🚨",  path: "/teacher/risk-monitor" },
  { label: "Interventions",  icon: "✅",  path: "/teacher/interventions" },
  { label: "Analytics",      icon: "📊",  path: "/teacher/analytics" },
];

export default function TeacherDashboard() {
  return (
    <DashboardLayout navItems={NAV} role="teacher">
      <Routes>
        <Route index             element={<Navigate to="/teacher/students" replace />} />
        <Route path="students"    element={<MyStudents />} />
        <Route path="students/:studentId" element={<StudentDetailPage />} />
        <Route path="risk-monitor" element={<RiskMonitorPage />} />
        <Route path="interventions" element={<InterventionsPage />} />
        <Route path="analytics"   element={<AnalyticsPage />} />
        <Route path="*"           element={<Navigate to="/teacher/students" replace />} />
      </Routes>
    </DashboardLayout>
  );
}

function PlaceholderCard({ icon, title, description, goal, color = "#a78bfa" }) {
  return (
    <div style={{
      background: "#111827", border: "1px solid #1e293b",
      borderRadius: "14px", padding: "32px",
      display: "flex", flexDirection: "column", alignItems: "center",
      textAlign: "center", gap: "12px", maxWidth: "480px", margin: "0 auto",
    }}>
      <div style={{ fontSize: "48px" }}>{icon}</div>
      <h3 style={{ color: "#f1f5f9", fontSize: "18px", fontWeight: "600" }}>{title}</h3>
      <p style={{ color: "#64748b", fontSize: "14px", lineHeight: "1.6" }}>{description}</p>
      <span style={{
        background: "rgba(167,139,250,0.12)", border: "1px solid rgba(167,139,250,0.3)", color,
        borderRadius: "6px", padding: "4px 12px",
        fontSize: "12px", fontWeight: "600",
      }}>
        {goal}
      </span>
    </div>
  );
}

// ── My Students ───────────────────────────────────────────────────────────
function MyStudents() {
  const [students, setStudents] = useState([]);
  const [profile, setProfile]   = useState(null);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/teacher/profile').then(r => setProfile(r.data)).catch(() => {});
    api.get('/teacher/risk-overview')
      .then(r => setStudents(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const riskColor = (level) => ({
    HIGH:     "#f87171",
    MODERATE: "#fb923c",
    WATCH:    "#fbbf24",
    LOW:      "#34d399",
  })[level] || "#475569";

  const q = search.trim().toLowerCase();
  const visible = q
    ? students.filter(s =>
        s.full_name?.toLowerCase().includes(q) ||
        s.roll_number?.toLowerCase().includes(q) ||
        s.branch?.toLowerCase().includes(q)
      )
    : students;

  return (
    <div className="fade-up">
      <div style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "22px", fontWeight: "700", color: "#f1f5f9", marginBottom: "4px" }}>My Students</h1>
        <p style={{ color: "#64748b", fontSize: "14px" }}>
          {profile
            ? `${profile.department || "Faculty"} · ${profile.total_students} student${profile.total_students !== 1 ? "s" : ""} assigned — click a row to view full profile`
            : "All assigned students sorted by risk level (highest first) — click a row to view full profile"}
        </p>
      </div>

      {loading ? (
        <p style={{ color: "#475569" }}>Loading students...</p>
      ) : students.length === 0 ? (
        <PlaceholderCard
          icon="👥"
          title="No students assigned yet"
          description="Students will appear here once they register and are assigned to you. Contact your administrator to assign students."
          goal="Students self-register with their credentials"
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {/* Search input */}
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by name, roll no, or branch…"
            style={{
              background: "#0a0f1e", border: "1px solid #1e293b",
              borderRadius: "8px", padding: "10px 14px",
              color: "#f1f5f9", fontSize: "13px", outline: "none",
              marginBottom: "4px",
            }}
          />
          {/* Table header */}
          <div style={tableHeader}>
            {["Student", "Roll No.", "Branch", "Semester", "CGPA", "Risk"].map(h => (
              <span key={h} style={{ fontSize: "11px", fontWeight: "600", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em" }}>{h}</span>
            ))}
          </div>
          {visible.length === 0 ? (
            <p style={{ color: "#475569", fontSize: 13, padding: "16px 0" }}>
              No students match "{search}".
            </p>
          ) : visible.map((s) => (
            <div
              key={s.student_id}
              onClick={() => navigate(`/teacher/students/${s.student_id}`)}
              style={{ ...tableRow, transition: "border-color 0.15s, background 0.15s" }}
              onMouseEnter={e => e.currentTarget.style.borderColor = "#38bdf8"}
              onMouseLeave={e => e.currentTarget.style.borderColor = "#1e293b"}
            >
              <span style={{ color: "#f1f5f9", fontWeight: "500", fontSize: "14px" }}>{s.full_name}</span>
              <span style={{ color: "#94a3b8", fontSize: "13px", fontFamily: "monospace" }}>{s.roll_number || "—"}</span>
              <span style={{ color: "#94a3b8", fontSize: "13px" }}>{s.branch ? s.branch.split(" ").slice(0, 2).join(" ") : "—"}</span>
              <span style={{ color: "#94a3b8", fontSize: "13px" }}>Sem {s.current_semester}</span>
              <span style={{ color: "#f1f5f9", fontSize: "14px", fontFamily: "monospace", fontWeight: "600" }}>{s.cgpa?.toFixed(2) || "—"}</span>
              <span style={{
                fontSize: "11px", fontWeight: "700", padding: "3px 10px",
                borderRadius: "99px", background: `${riskColor(s.risk_level)}22`,
                color: riskColor(s.risk_level), border: `1px solid ${riskColor(s.risk_level)}44`,
              }}>
                {s.risk_level || "No Data"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const tableHeader = {
  display: "grid",
  gridTemplateColumns: "2fr 1fr 2fr 0.8fr 0.8fr 1fr",
  padding: "8px 20px",
  gap: "12px",
};
const tableRow = {
  display: "grid",
  gridTemplateColumns: "2fr 1fr 2fr 0.8fr 0.8fr 1fr",
  padding: "14px 20px", gap: "12px",
  background: "#111827", border: "1px solid #1e293b",
  borderRadius: "10px", alignItems: "center",
  transition: "border-color 0.15s",
  cursor: "pointer",
};
