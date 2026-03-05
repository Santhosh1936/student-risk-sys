// frontend/src/pages/LoginPage.jsx
//
// Handles both Login and Register in one component (tab-switch).
// On success: redirects to /student or /teacher based on role.
//
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const BRANCHES = [
  "Computer Science Engineering",
  "Information Technology",
  "Electronics & Communication Engineering",
  "Electrical Engineering",
  "Mechanical Engineering",
  "Civil Engineering",
  "Chemical Engineering",
];

export default function LoginPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [tab, setTab]       = useState("login");  // "login" | "register"
  const [role, setRole]     = useState("student");
  const [error, setError]   = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [loading, setLoading] = useState(false);

  // Shared fields
  const [email, setEmail]     = useState("");
  const [password, setPassword] = useState("");
  // Register-only fields
  const [fullName, setFullName]   = useState("");
  const [rollNumber, setRollNumber] = useState("");
  const [branch, setBranch]       = useState(BRANCHES[0]);
  const [enrollYear, setEnrollYear] = useState(new Date().getFullYear());
  const [department, setDepartment] = useState("");
  const [employeeId, setEmployeeId] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    setLoading(true);
    try {
      if (tab === "login") {
        const res = await login(email, password);
        if (!res.success) {
          setError(res.error || "Login failed. Please try again.");
        } else {
          navigate(res.role === "student" ? "/student" : "/teacher", { replace: true });
        }
      } else {
        const payload = {
          email, password, role, full_name: fullName,
          ...(role === "student"
            ? { roll_number: rollNumber, branch, enrollment_year: parseInt(enrollYear) }
            : { department, employee_id: employeeId }),
        };
        const res = await register(payload);
        if (!res.success) {
          setError(res.error || "Registration failed. Please try again.");
        } else {
          setSuccessMsg("Account created! Please login.");
          setTab("login");
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      {/* Background grid */}
      <div style={styles.grid} />

      {/* Glow blobs */}
      <div style={{ ...styles.blob, top: "10%", left: "20%", background: "rgba(56,189,248,0.08)" }} />
      <div style={{ ...styles.blob, bottom: "15%", right: "15%", background: "rgba(52,211,153,0.06)" }} />

      <div style={styles.card} className="fade-up">
        {/* Header */}
        <div style={styles.cardHeader}>
          <div style={styles.logo}>
            <span style={styles.logoIcon}>◈</span>
            <span style={styles.logoText}>SARS</span>
          </div>
          <p style={styles.tagline}>Student Academic Risk Assessment System</p>
        </div>

        {/* Tab switcher */}
        <div style={styles.tabs}>
          {["login", "register"].map((t) => (
            <button
              key={t}
              onClick={() => { setTab(t); setError(""); setSuccessMsg(""); }}
              style={{
                ...styles.tab,
                ...(tab === t ? styles.tabActive : {}),
              }}
            >
              {t === "login" ? "Sign In" : "Create Account"}
            </button>
          ))}
        </div>

        {/* Role toggle (register only) */}
        {tab === "register" && (
          <div style={styles.roleToggle} className="fade-up">
            {["student", "teacher"].map((r) => (
              <button
                key={r}
                onClick={() => setRole(r)}
                style={{ ...styles.roleBtn, ...(role === r ? styles.roleBtnActive : {}) }}
              >
                {r === "student" ? "🎓 Student" : "👨‍🏫 Faculty"}
              </button>
            ))}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={styles.form}>
          {tab === "register" && (
            <Field label="Full Name" value={fullName} onChange={setFullName}
              placeholder="Santhosh Kethavath" required />
          )}

          <Field label="Email Address" type="email" value={email} onChange={setEmail}
            placeholder="you@university.edu" required />

          <Field label="Password" type="password" value={password} onChange={setPassword}
            placeholder={tab === "register" ? "Min. 6 characters" : "••••••••"} required />

          {/* Student-only register fields */}
          {tab === "register" && role === "student" && (
            <>
              <Field label="Roll Number" value={rollNumber} onChange={setRollNumber}
                placeholder="2021BTCS001" />
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Branch</label>
                <select
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  style={styles.select}
                >
                  {BRANCHES.map((b) => <option key={b}>{b}</option>)}
                </select>
              </div>
              <Field label="Enrollment Year" type="number" value={enrollYear}
                onChange={setEnrollYear} placeholder="2021" min="2015" max="2025" />
            </>
          )}

          {/* Teacher-only register fields */}
          {tab === "register" && role === "teacher" && (
            <>
              <Field label="Department" value={department} onChange={setDepartment}
                placeholder="Computer Science" />
              <Field label="Employee ID" value={employeeId} onChange={setEmployeeId}
                placeholder="FAC2024001" />
            </>
          )}

          {successMsg && (
            <div style={styles.success} className="fade-up">
              ✓ {successMsg}
            </div>
          )}

          {error && (
            <div style={styles.error} className="fade-up">
              ⚠ {error}
            </div>
          )}

          <button type="submit" style={styles.submitBtn} disabled={loading}>
            {loading ? (
              <span style={styles.spinner} />
            ) : (
              tab === "login" ? "Sign In →" : "Create Account →"
            )}
          </button>
        </form>

        <p style={styles.switchText}>
          {tab === "login" ? "New to SARS? " : "Already have an account? "}
          <button
            onClick={() => { setTab(tab === "login" ? "register" : "login"); setError(""); setSuccessMsg(""); }}
            style={styles.switchBtn}
          >
            {tab === "login" ? "Create an account" : "Sign in"}
          </button>
        </p>
      </div>
    </div>
  );
}

// ── Reusable field component ───────────────────────────────────────────────
function Field({ label, value, onChange, type = "text", placeholder, required, ...rest }) {
  return (
    <div style={styles.fieldGroup}>
      <label style={styles.label}>{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        style={styles.input}
        {...rest}
      />
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────────────────
const styles = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "24px",
    background: "#0a0f1e",
    position: "relative",
    overflow: "hidden",
  },
  grid: {
    position: "absolute", inset: 0,
    backgroundImage: `
      linear-gradient(rgba(56,189,248,0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(56,189,248,0.04) 1px, transparent 1px)
    `,
    backgroundSize: "48px 48px",
    pointerEvents: "none",
  },
  blob: {
    position: "absolute",
    width: "500px", height: "500px",
    borderRadius: "50%",
    filter: "blur(80px)",
    pointerEvents: "none",
  },
  card: {
    background: "#111827",
    border: "1px solid #1e293b",
    borderRadius: "20px",
    padding: "40px 36px",
    width: "100%",
    maxWidth: "440px",
    position: "relative",
    zIndex: 1,
    boxShadow: "0 24px 64px rgba(0,0,0,0.5)",
  },
  cardHeader: { textAlign: "center", marginBottom: "28px" },
  logo: { display: "flex", alignItems: "center", justifyContent: "center", gap: "10px", marginBottom: "8px" },
  logoIcon: { fontSize: "28px", color: "#38bdf8" },
  logoText: {
    fontSize: "26px", fontWeight: "700", letterSpacing: "0.08em",
    fontFamily: "'Space Mono', monospace", color: "#f1f5f9",
  },
  tagline: { fontSize: "13px", color: "#64748b", letterSpacing: "0.02em" },

  tabs: {
    display: "flex", background: "#0a0f1e", borderRadius: "10px",
    padding: "4px", marginBottom: "20px",
  },
  tab: {
    flex: 1, padding: "9px 0", border: "none",
    background: "transparent", color: "#64748b",
    borderRadius: "7px", fontSize: "14px", fontWeight: "500",
    transition: "all 0.18s ease", cursor: "pointer",
  },
  tabActive: {
    background: "#1e293b", color: "#f1f5f9",
    boxShadow: "0 1px 4px rgba(0,0,0,0.4)",
  },

  roleToggle: {
    display: "flex", gap: "8px", marginBottom: "20px",
  },
  roleBtn: {
    flex: 1, padding: "9px", border: "1px solid #1e293b",
    background: "transparent", color: "#64748b",
    borderRadius: "8px", fontSize: "13px", fontWeight: "500",
    transition: "all 0.18s ease", cursor: "pointer",
  },
  roleBtnActive: {
    border: "1px solid rgba(56,189,248,0.5)",
    background: "rgba(56,189,248,0.08)", color: "#38bdf8",
  },

  form: { display: "flex", flexDirection: "column", gap: "16px" },
  fieldGroup: { display: "flex", flexDirection: "column", gap: "6px" },
  label: { fontSize: "12px", fontWeight: "600", color: "#94a3b8", letterSpacing: "0.05em", textTransform: "uppercase" },
  input: {
    background: "#0a0f1e", border: "1px solid #1e293b",
    borderRadius: "8px", padding: "11px 14px",
    color: "#f1f5f9", fontSize: "14px",
    outline: "none", transition: "border-color 0.18s ease",
    width: "100%",
  },
  select: {
    background: "#0a0f1e", border: "1px solid #1e293b",
    borderRadius: "8px", padding: "11px 14px",
    color: "#f1f5f9", fontSize: "14px",
    outline: "none", width: "100%", cursor: "pointer",
  },

  error: {
    background: "rgba(248,113,113,0.1)", border: "1px solid rgba(248,113,113,0.3)",
    borderRadius: "8px", padding: "10px 14px",
    color: "#fca5a5", fontSize: "13px",
  },
  success: {
    background: "rgba(52,211,153,0.1)", border: "1px solid rgba(52,211,153,0.3)",
    borderRadius: "8px", padding: "10px 14px",
    color: "#6ee7b7", fontSize: "13px",
  },
  submitBtn: {
    background: "linear-gradient(135deg, #0ea5e9, #38bdf8)",
    color: "#fff", border: "none",
    borderRadius: "10px", padding: "13px",
    fontSize: "15px", fontWeight: "600",
    marginTop: "4px", transition: "opacity 0.18s ease",
    display: "flex", alignItems: "center", justifyContent: "center",
    minHeight: "46px",
  },
  spinner: {
    width: "18px", height: "18px",
    border: "2px solid rgba(255,255,255,0.3)",
    borderTop: "2px solid #fff",
    borderRadius: "50%",
    animation: "spin 0.7s linear infinite",
    display: "inline-block",
  },
  switchText: { textAlign: "center", marginTop: "20px", fontSize: "13px", color: "#64748b" },
  switchBtn: {
    background: "none", border: "none",
    color: "#38bdf8", cursor: "pointer",
    fontSize: "13px", fontWeight: "600",
    padding: "0", marginLeft: "4px",
  },
};
