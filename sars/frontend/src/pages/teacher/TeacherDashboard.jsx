// frontend/src/pages/teacher/TeacherDashboard.jsx
import { Routes, Route, Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import DashboardLayout from "../../components/DashboardLayout";
import { teacherAPI } from "../../services/api";
import { useAuth } from "../../context/AuthContext";
import RiskMonitorPage from "./RiskMonitorPage";

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
        <Route path="risk-monitor" element={<RiskMonitorPage />} />
        <Route path="interventions" element={<Interventions />} />
        <Route path="analytics"   element={<Analytics />} />
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

function PageHeader({ title, subtitle }) {
  return (
    <div style={{ marginBottom: "28px" }}>
      <h1 style={{ fontSize: "22px", fontWeight: "700", color: "#f1f5f9", marginBottom: "4px" }}>{title}</h1>
      <p style={{ color: "#64748b", fontSize: "14px" }}>{subtitle}</p>
    </div>
  );
}

// ── Overview ──────────────────────────────────────────────────────────────
function TeacherOverview() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [students, setStudents] = useState([]);

  useEffect(() => {
    teacherAPI.getProfile().then(r => setProfile(r.data)).catch(() => {});
    teacherAPI.getStudents().then(r => setStudents(r.data)).catch(() => {});
  }, []);

  const highRisk = students.filter(s => s.risk_level === "HIGH").length;
  const moderate = students.filter(s => s.risk_level === "MODERATE").length;
  const noRisk   = students.filter(s => s.risk_level === null).length;

  return (
    <div className="fade-up">
      <div style={{ marginBottom: "32px" }}>
        <h1 style={{ fontSize: "24px", fontWeight: "700", color: "#f1f5f9", marginBottom: "4px" }}>
          Faculty Dashboard 👨‍🏫
        </h1>
        <p style={{ color: "#64748b", fontSize: "14px" }}>
          Welcome {user?.full_name} · {profile?.department || "Department not set"}
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "16px", marginBottom: "32px" }}>
        <StatCard label="Total Students" value={profile?.total_students ?? "—"} icon="◎" color="#a78bfa" />
        <StatCard label="High Risk"      value={highRisk || "—"} icon="◉" color="#f87171" sub="Needs immediate action" />
        <StatCard label="Moderate Risk"  value={moderate || "—"} icon="◉" color="#fb923c" sub="Monitor closely" />
        <StatCard label="Pending Scores" value={noRisk}  icon="?" color="#fbbf24" sub="No marks uploaded yet" />
      </div>

      <PlaceholderCard
        icon="🎓"
        title="Student risk monitoring activates after Goal 3"
        description="Once students upload their marksheets and SARS scores are computed, you will see your students ranked by risk level here, with alerts for those needing immediate intervention."
        goal="→ Go to My Students to see your roster"
      />
    </div>
  );
}

// ── My Students ───────────────────────────────────────────────────────────
function MyStudents() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    teacherAPI.getStudents()
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

  return (
    <div className="fade-up">
      <PageHeader
        title="My Students"
        subtitle="All assigned students sorted by risk level (highest first)"
      />

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
          {/* Table header */}
          <div style={tableHeader}>
            {["Student", "Roll No.", "Branch", "Semester", "CGPA", "Risk"].map(h => (
              <span key={h} style={{ fontSize: "11px", fontWeight: "600", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em" }}>{h}</span>
            ))}
          </div>
          {students.map((s) => (
            <div key={s.user_id} style={tableRow}>
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

// ── Risk Monitor ──────────────────────────────────────────────────────────
function RiskMonitor() {
  return (
    <div className="fade-up">
      <PageHeader title="Risk Monitor" subtitle="Real-time risk alerts and student tracking" />
      <PlaceholderCard
        icon="◉"
        title="Risk monitoring activates in Goal 3 & 5"
        description="Once students upload their marksheets, this panel will show auto-generated alerts for students approaching attendance thresholds, increasing backlogs, or declining GPA trends."
        goal="Implemented in: Goal 3 + Goal 5 (G5.8)"
      />
    </div>
  );
}

// ── Interventions ─────────────────────────────────────────────────────────
function Interventions() {
  return (
    <div className="fade-up">
      <PageHeader title="Interventions" subtitle="Log and track academic interventions for your students" />
      <PlaceholderCard
        icon="✦"
        title="Intervention tracking coming in Goal 5"
        description="Log tutoring sessions, counseling referrals, and course load adjustments. The system will automatically measure whether the student's SARS score improved after each intervention."
        goal="Implemented in: Goal 5 (G5.6, G5.7)"
      />
    </div>
  );
}

// ── Analytics ─────────────────────────────────────────────────────────────
function Analytics() {
  return (
    <div className="fade-up">
      <PageHeader title="Cohort Analytics" subtitle="Branch-level trends, subject difficulty, and intervention effectiveness" />
      <PlaceholderCard
        icon="↗"
        title="Analytics dashboard coming in Goal 5"
        description="View CGPA distribution histograms, most-failed subjects, semester-wise cohort trends, and which types of interventions produced the best outcomes."
        goal="Implemented in: Goal 5 (G5.7)"
      />
    </div>
  );
}

function StatCard({ label, value, sub = "", icon, color }) {
  return (
    <div style={{
      background: "#111827", border: "1px solid #1e293b",
      borderRadius: "12px", padding: "20px 22px",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
        <span style={{ fontSize: "11px", color: "#64748b", fontWeight: "600", letterSpacing: "0.05em", textTransform: "uppercase" }}>{label}</span>
        <span style={{ color, fontSize: "18px" }}>{icon}</span>
      </div>
      <div style={{ fontSize: "28px", fontWeight: "700", fontFamily: "'Space Mono', monospace", color: "#f1f5f9" }}>{value}</div>
      {sub && <div style={{ fontSize: "12px", color: "#475569", marginTop: "4px" }}>{sub}</div>}
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
