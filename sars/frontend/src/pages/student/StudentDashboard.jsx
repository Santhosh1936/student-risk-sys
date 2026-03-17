// frontend/src/pages/student/StudentDashboard.jsx
import { Routes, Route, Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import DashboardLayout from "../../components/DashboardLayout";
import { studentAPI } from "../../services/api";
import { useAuth } from "../../context/AuthContext";
import api from "../../services/api";
import UploadMarksPage from "./UploadMarksPage";
import SemestersPage from "./SemestersPage";
import RiskPage from "./RiskPage";import AdvisoryPage from './AdvisoryPage';
import AttendancePage from './AttendancePage';
// ── Nav configuration ─────────────────────────────────────────────────────
const NAV = [
  { label: "Overview",     icon: "🏠",  path: "/student/overview" },
  { label: "Upload Marks", icon: "📤",  path: "/student/upload" },
  { label: "Performance",  icon: "📊",  path: "/student/performance" },
  { label: "My Risk",      icon: "⚠️",  path: "/student/risk" },
  { label: "Advisory",     icon: "💬",  path: "/student/advisory" },
  { label: "Attendance",   icon: "📋",  path: "/student/attendance" },
];

export default function StudentDashboard() {
  return (
    <DashboardLayout navItems={NAV} role="student">
      <Routes>
        <Route index          element={<Navigate to="/student/overview" replace />} />
        <Route path="overview"    element={<Overview />} />
        <Route path="upload"      element={<UploadMarksPage />} />
        <Route path="performance" element={<SemestersPage />} />
        <Route path="risk"        element={<RiskPage />} />
        <Route path="advisory"    element={<AdvisoryPage />} />
        <Route path="attendance"  element={<AttendancePage />} />
        <Route path="*"           element={<Navigate to="/student/overview" replace />} />
      </Routes>
    </DashboardLayout>
  );
}

// ── Shared placeholder card ───────────────────────────────────────────────
function PlaceholderCard({ icon, title, description, goal, color = "#38bdf8" }) {
  return (
    <div style={{
      background: "#111827", border: `1px solid #1e293b`,
      borderRadius: "14px", padding: "32px",
      display: "flex", flexDirection: "column", alignItems: "center",
      textAlign: "center", gap: "12px", maxWidth: "480px", margin: "0 auto",
    }}>
      <div style={{ fontSize: "48px" }}>{icon}</div>
      <h3 style={{ color: "#f1f5f9", fontSize: "18px", fontWeight: "600" }}>{title}</h3>
      <p style={{ color: "#64748b", fontSize: "14px", lineHeight: "1.6" }}>{description}</p>
      <span style={{
        background: `rgba(${color === "#38bdf8" ? "56,189,248" : "52,211,153"},0.12)`,
        border: `1px solid ${color}33`, color,
        borderRadius: "6px", padding: "4px 12px",
        fontSize: "12px", fontWeight: "600",
      }}>
        {goal}
      </span>
    </div>
  );
}

// ── Page: Overview ────────────────────────────────────────────────────────
function Overview() {
  const { user } = useAuth();
  const [profile, setProfile]     = useState(null);
  const [semesters, setSemesters] = useState([]);
  const [loading, setLoading]     = useState(true);
  const [riskData, setRiskData]   = useState(null);

  useEffect(() => {
    Promise.all([
      studentAPI.getProfile().then(r => setProfile(r.data)).catch(() => {}),
      api.get('/student/semesters').then(r => setSemesters(r.data)).catch(() => {}),
      api.get('/student/risk-score').then(r => setRiskData(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  const totalBacklogs = semesters
    .flatMap(s => s.subjects || [])
    .filter(sub => sub.is_backlog).length;

  // Use profile CGPA if available, fall back to value computed by risk engine
  const displayCgpa = profile?.cgpa ?? riskData?.factor_breakdown?.cgpa;

  return (
    <div className="fade-up">
      {/* Page header */}
      <div style={{ marginBottom: "32px" }}>
        <h1 style={{ fontSize: "24px", fontWeight: "700", color: "#f1f5f9", marginBottom: "4px" }}>
          Welcome back, {user?.full_name?.split(" ")[0]} 👋
        </h1>
        <p style={{ color: "#64748b", fontSize: "14px" }}>
          Here is your academic overview. Upload your marksheets to get started.
        </p>
      </div>

      {/* Quick stats grid */}
      <div style={grid}>
        <StatCard
          label="Current CGPA"
          value={loading ? "—" : (displayCgpa != null ? Number(displayCgpa).toFixed(2) : "—")}
          sub={displayCgpa != null ? "Cumulative GPA" : "Upload marks to compute"}
          icon="◈" color="#38bdf8"
        />
        <StatCard
          label="Risk Score"
          value={loading ? "—" : (riskData?.sars_score != null ? riskData.sars_score.toFixed(1) : "—")}
          sub={riskData?.risk_level ?? "Not computed"}
          icon={riskData?.risk_level === 'HIGH' ? '🔴'
              : riskData?.risk_level === 'MODERATE' ? '🟠'
              : riskData?.risk_level === 'WATCH' ? '🟡'
              : riskData?.risk_level === 'LOW' ? '🟢'
              : '◉'}
          color={riskData?.risk_level === 'HIGH' ? '#f87171'
               : riskData?.risk_level === 'MODERATE' ? '#fb923c'
               : riskData?.risk_level === 'WATCH' ? '#fbbf24'
               : riskData?.risk_level === 'LOW' ? '#34d399'
               : '#fb923c'}
        />
        <StatCard
          label="Semesters Uploaded"
          value={loading ? "—" : semesters.length}
          sub="of 8 semesters"
          icon="↑" color="#34d399"
        />
        <StatCard
          label="Active Backlogs"
          value={loading ? "—" : totalBacklogs}
          sub={totalBacklogs > 0 ? "Subjects to clear" : "No backlogs"}
          icon="⚠" color={totalBacklogs > 0 ? "#f87171" : "#fbbf24"}
        />
      </div>

      {/* Getting started card (only shown before first upload) */}
      {!loading && semesters.length === 0 && (
        <div style={{ marginTop: "32px" }}>
          <PlaceholderCard
            icon="📄"
            title="Start by uploading your marksheets"
            description="Upload your semester marksheet PDFs. The system will automatically extract your grades, compute your SARS risk score, and provide personalized advisory insights."
            goal="→ Go to Upload Marks to begin"
          />
        </div>
      )}
    </div>
  );
}

// ── Reusable small components ─────────────────────────────────────────────
function StatCard({ label, value, sub, icon, color }) {
  return (
    <div style={{
      background: "#111827", border: "1px solid #1e293b",
      borderRadius: "12px", padding: "20px 22px",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
        <span style={{ fontSize: "12px", color: "#64748b", fontWeight: "600", letterSpacing: "0.05em", textTransform: "uppercase" }}>{label}</span>
        <span style={{ color, fontSize: "18px" }}>{icon}</span>
      </div>
      <div style={{ fontSize: "28px", fontWeight: "700", fontFamily: "'Space Mono', monospace", color: "#f1f5f9" }}>{value}</div>
      <div style={{ fontSize: "12px", color: "#475569", marginTop: "4px" }}>{sub}</div>
    </div>
  );
}

const grid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
  gap: "16px",
};
