// frontend/src/pages/student/StudentDashboard.jsx
import { Routes, Route, Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import DashboardLayout from "../../components/DashboardLayout";
import { studentAPI } from "../../services/api";
import { useAuth } from "../../context/AuthContext";
import api from "../../services/api";
import UploadMarksPage from "./UploadMarksPage";
import SemestersPage from "./SemestersPage";

// ── Nav configuration ─────────────────────────────────────────────────────
const NAV = [
  { label: "Overview",     icon: "🏠",  path: "/student/overview" },
  { label: "Upload Marks", icon: "📤",  path: "/student/upload" },
  { label: "Performance",  icon: "📊",  path: "/student/performance" },
  { label: "My Risk",      icon: "⚠️",  path: "/student/risk" },
  { label: "Advisory",     icon: "💬",  path: "/student/advisory" },
];

export default function StudentDashboard() {
  return (
    <DashboardLayout navItems={NAV} role="student">
      <Routes>
        <Route index          element={<Navigate to="/student/overview" replace />} />
        <Route path="overview"    element={<Overview />} />
        <Route path="upload"      element={<UploadMarksPage />} />
        <Route path="performance" element={<SemestersPage />} />
        <Route path="risk"        element={<MyRisk />} />
        <Route path="advisory"    element={<Advisory />} />
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

  useEffect(() => {
    Promise.all([
      studentAPI.getProfile().then(r => setProfile(r.data)).catch(() => {}),
      api.get('/student/semesters').then(r => setSemesters(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  const totalBacklogs = semesters
    .flatMap(s => s.subjects || [])
    .filter(sub => sub.is_backlog).length;

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
          value={loading ? "—" : (profile?.cgpa != null ? profile.cgpa.toFixed(2) : "—")}
          sub={profile?.cgpa != null ? "Cumulative GPA" : "Upload marks to compute"}
          icon="◈" color="#38bdf8"
        />
        <StatCard
          label="Risk Score"
          value="—"
          sub="Computed in Goal 3"
          icon="◉" color="#fb923c"
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

// ── Page: My Risk ─────────────────────────────────────────────────────────
function MyRisk() {
  return (
    <div className="fade-up">
      <PageHeader
        title="My Risk Assessment"
        subtitle="Your SARS score with full factor breakdown and peer comparison"
      />
      <div style={{ display: "flex", flexDirection: "column", gap: "16px", maxWidth: "480px", margin: "0 auto" }}>
        {/* Risk gauge placeholder */}
        <div style={{
          background: "#111827", border: "1px solid #1e293b",
          borderRadius: "14px", padding: "32px", textAlign: "center",
        }}>
          <div style={{
            width: "120px", height: "120px", borderRadius: "50%",
            border: "6px solid #1e293b", margin: "0 auto 16px",
            display: "flex", alignItems: "center", justifyContent: "center",
            position: "relative",
          }}>
            <span style={{ fontSize: "28px", color: "#475569" }}>—</span>
          </div>
          <p style={{ color: "#475569", fontSize: "13px" }}>
            Upload marksheets to compute your SARS score
          </p>
        </div>
        <PlaceholderCard
          icon="◉"
          title="SARS Risk Engine coming in Goal 3"
          description="Your Student Academic Risk Score (0.0 – 1.0) will appear here with a full chain-of-thought breakdown: which factors contributed, by how much, and what specific evidence supports each factor."
          goal="Implemented in: Goal 3 (G3.1 – G3.6)"
          color="#fb923c"
        />
      </div>
    </div>
  );
}

// ── Page: Advisory ────────────────────────────────────────────────────────
function Advisory() {
  return (
    <div className="fade-up">
      <PageHeader
        title="Advisory Chat"
        subtitle="Ask any question about your academic performance in English or Hindi"
      />
      {/* Chat shell placeholder */}
      <div style={{
        background: "#111827", border: "1px solid #1e293b",
        borderRadius: "14px", height: "400px",
        display: "flex", flexDirection: "column",
        overflow: "hidden", maxWidth: "720px", margin: "0 auto",
      }}>
        {/* Chat header */}
        <div style={{
          padding: "16px 20px", borderBottom: "1px solid #1e293b",
          display: "flex", alignItems: "center", gap: "10px",
        }}>
          <div style={{
            width: "32px", height: "32px", borderRadius: "50%",
            background: "rgba(56,189,248,0.15)", display: "flex", alignItems: "center", justifyContent: "center",
            color: "#38bdf8", fontSize: "16px",
          }}>◎</div>
          <div>
            <div style={{ fontSize: "14px", fontWeight: "600", color: "#f1f5f9" }}>SARS Advisor</div>
            <div style={{ fontSize: "11px", color: "#475569" }}>Goal 4 — Coming soon</div>
          </div>
          <div style={{
            marginLeft: "auto", fontSize: "11px", padding: "3px 8px",
            background: "rgba(71,85,105,0.3)", borderRadius: "99px", color: "#64748b",
          }}>Offline</div>
        </div>

        {/* Empty chat body */}
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div style={{ textAlign: "center", color: "#475569" }}>
            <div style={{ fontSize: "36px", marginBottom: "12px" }}>◎</div>
            <p style={{ fontSize: "14px" }}>Advisory chat activates after marking Goal 4 complete</p>
            <p style={{ fontSize: "12px", marginTop: "6px" }}>Ask: "What if I score 85 next semester?" · "Am I at risk?"</p>
          </div>
        </div>

        {/* Input bar */}
        <div style={{
          padding: "12px 16px", borderTop: "1px solid #1e293b",
          display: "flex", gap: "10px",
        }}>
          <input
            placeholder="Ask anything about your academic performance..."
            disabled
            style={{
              flex: 1, background: "#0a0f1e", border: "1px solid #1e293b",
              borderRadius: "8px", padding: "10px 14px",
              color: "#475569", fontSize: "13px", cursor: "not-allowed",
            }}
          />
          <button disabled style={{
            background: "#1e293b", border: "none", borderRadius: "8px",
            color: "#475569", padding: "10px 16px", fontSize: "13px",
            cursor: "not-allowed",
          }}>→</button>
        </div>
      </div>
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

function PageHeader({ title, subtitle }) {
  return (
    <div style={{ marginBottom: "28px" }}>
      <h1 style={{ fontSize: "22px", fontWeight: "700", color: "#f1f5f9", marginBottom: "4px" }}>{title}</h1>
      <p style={{ color: "#64748b", fontSize: "14px" }}>{subtitle}</p>
    </div>
  );
}

const grid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
  gap: "16px",
};
