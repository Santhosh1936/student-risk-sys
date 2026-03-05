// frontend/src/context/AuthContext.jsx
//
// Single source of truth for authentication state.
// Every component that needs user info uses useAuth() — never reads
// from sessionStorage directly.
//
import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { authAPI } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null);   // { id, email, role, full_name }
  const [loading, setLoading] = useState(true);   // true while verifying token on load

  // ── On app load: check if a token exists and is still valid ──────────────
  useEffect(() => {
    const token = sessionStorage.getItem("sars_token");
    if (!token) {
      setLoading(false);
      return;
    }
    // Verify token is still valid by calling /auth/me
    authAPI.me()
      .then((res) => setUser(res.data))
      .catch(() => sessionStorage.removeItem("sars_token")) // expired token
      .finally(() => setLoading(false));
  }, []);

  // ── Login: store token + set user state ──────────────────────────────────
  const login = useCallback(async (email, password) => {
    try {
      const res = await authAPI.login({ email, password });
      const { access_token, role, full_name, user_id } = res.data;
      sessionStorage.setItem("sars_token", access_token);
      setUser({ id: user_id, email, role, full_name });
      return { success: true, role };
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || "Login failed" };
    }
  }, []);

  // ── Register: create account only — user must login separately ──────────
  const register = useCallback(async (data) => {
    try {
      await authAPI.register(data);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || "Registration failed" };
    }
  }, []);

  // ── Logout: clear everything ──────────────────────────────────────────────
  const logout = useCallback(() => {
    sessionStorage.removeItem("sars_token");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook — always use this, never useContext(AuthContext) directly
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
