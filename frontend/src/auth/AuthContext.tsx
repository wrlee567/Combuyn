import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { setOn401Handler } from "../api";
import { clearToken, getToken, setToken } from "./token";

interface LoginResponse {
  access_token: string;
  org_id: string;
}

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(getToken);

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
    window.location.href = "/login";
  }, []);

  // Register 401 handler so api.ts can trigger logout without importing React.
  useEffect(() => {
    setOn401Handler(logout);
    return () => setOn401Handler(null);
  }, [logout]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail ?? "Login failed");
    }
    const data: LoginResponse = await res.json();
    setToken(data.access_token);
    setTokenState(data.access_token);
  }, []);

  return (
    <AuthContext.Provider value={{ token, isAuthenticated: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
