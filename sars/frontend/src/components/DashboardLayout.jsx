// frontend/src/components/DashboardLayout.jsx
//
// Shared layout: sidebar + top bar + main content area.
// Used by BOTH student and teacher dashboards.
// Props:
//   navItems: [{ label, icon, path, badge? }]
//   children: page content
//
import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function DashboardLayout({ navItems, children, role }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const accentColor = role === "teacher" ? "#a78bfa" : "#38bdf8";

  return (
    <div style={styles.shell}>
      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <aside style={{ ...styles.sidebar, width: collapsed ? "64px" : "220px" }}>
        {/* Logo */}
        <div style={styles.sidebarLogo}>
          <span style={{ ...styles.logoIcon, color: accentColor }}>◈</span>
          {!collapsed && (
            <span style={styles.logoText}>SARS</span>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            style={{ ...styles.collapseBtn, marginLeft: "auto" }}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? "›" : "‹"}
          </button>
        </div>

        {/* Role badge */}
        {!collapsed && (
          <div style={{ ...styles.roleBadge, borderColor: accentColor, color: accentColor }}>
            {role === "teacher" ? "👨‍🏫 Faculty" : "🎓 Student"}
          </div>
        )}

        {/* Nav */}
        <nav style={styles.nav}>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                ...styles.navItem,
                ...(isActive ? { ...styles.navItemActive, borderLeftColor: accentColor, color: accentColor } : {}),
              })}
              title={collapsed ? item.label : ""}
            >
              <span style={styles.navIcon}>{item.icon}</span>
              {!collapsed && <span style={styles.navLabel}>{item.label}</span>}
              {!collapsed && item.badge && (
                <span style={{ ...styles.navBadge, background: accentColor }}>{item.badge}</span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User section */}
        <div style={styles.sidebarUser}>
          {!collapsed && (
            <div>
              <div style={styles.userName}>{user?.full_name}</div>
              <div style={styles.userEmail}>{user?.email}</div>
            </div>
          )}
          <button onClick={handleLogout} style={styles.logoutBtn} title="Sign out">
            ⏻
          </button>
        </div>
      </aside>

      {/* ── Main area ────────────────────────────────────────────────────── */}
      <main style={styles.main}>
        {children}
      </main>
    </div>
  );
}

const styles = {
  shell: {
    display: "flex", minHeight: "100vh", background: "#0a0f1e",
  },
  sidebar: {
    background: "#1e3a5f",
    borderRight: "1px solid #1e293b",
    display: "flex",
    flexDirection: "column",
    transition: "width 0.2s ease",
    flexShrink: 0,
    position: "sticky",
    top: 0, height: "100vh",
    overflow: "hidden",
  },
  sidebarLogo: {
    display: "flex", alignItems: "center", gap: "10px",
    padding: "20px 16px 16px",
    borderBottom: "1px solid #1e293b",
  },
  logoIcon: { fontSize: "22px", flexShrink: 0 },
  logoText: { fontSize: "18px", fontWeight: "700", fontFamily: "'Space Mono', monospace", color: "#f1f5f9" },
  collapseBtn: {
    background: "none", border: "none", color: "#475569",
    fontSize: "18px", cursor: "pointer", padding: "2px 6px",
    flexShrink: 0,
    transition: "color 0.15s",
  },

  roleBadge: {
    margin: "12px 14px 4px",
    padding: "4px 10px",
    border: "1px solid",
    borderRadius: "6px",
    fontSize: "11px", fontWeight: "600", letterSpacing: "0.03em",
    textAlign: "center",
  },

  nav: { flex: 1, padding: "8px 8px", display: "flex", flexDirection: "column", gap: "2px" },
  navItem: {
    display: "flex", alignItems: "center", gap: "10px",
    padding: "10px 10px", borderRadius: "8px",
    fontSize: "13px", fontWeight: "500",
    color: "#64748b", borderLeft: "2px solid transparent",
    transition: "all 0.15s ease", whiteSpace: "nowrap",
  },
  navItemActive: {
    background: "rgba(56,189,248,0.08)",
    borderLeftColor: "#38bdf8", color: "#38bdf8",
  },
  navIcon: { fontSize: "16px", flexShrink: 0, width: "20px", textAlign: "center" },
  navLabel: { flex: 1 },
  navBadge: {
    fontSize: "10px", fontWeight: "700",
    borderRadius: "99px", padding: "1px 7px", color: "#0a0f1e",
  },

  sidebarUser: {
    padding: "12px 14px",
    borderTop: "1px solid #1e293b",
    display: "flex", alignItems: "center", gap: "10px",
  },
  userName: { fontSize: "13px", fontWeight: "600", color: "#f1f5f9", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  userEmail: { fontSize: "11px", color: "#475569", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  logoutBtn: {
    background: "none", border: "1px solid #1e293b",
    borderRadius: "6px", color: "#64748b",
    fontSize: "16px", cursor: "pointer",
    padding: "6px 8px", marginLeft: "auto", flexShrink: 0,
    transition: "all 0.15s",
  },

  main: { flex: 1, overflow: "auto", padding: "32px 36px" },
};
