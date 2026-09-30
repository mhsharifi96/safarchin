"use client";

import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react";

import { apiFetch, ApiError, ensureCsrfCookie } from "@/lib/api";
import type { User } from "@/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  refresh: () => Promise<void>;
  login: (email: string, password: string) => Promise<User>;
  register: (email: string, password: string, fullName: string) => Promise<User>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const me = await apiFetch<User>("/api/auth/me/");
      setUser(me);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setUser(null);
      } else {
        setUser(null);
      }
    }
  }, []);

  useEffect(() => {
    (async () => {
      await ensureCsrfCookie();
      await refresh();
      setLoading(false);
    })();
  }, [refresh]);

  const login = useCallback(async (email: string, password: string) => {
    const me = await apiFetch<User>("/api/auth/login/", { method: "POST", body: { email, password } });
    setUser(me);
    return me;
  }, []);

  const register = useCallback(async (email: string, password: string, fullName: string) => {
    const me = await apiFetch<User>("/api/auth/register/", {
      method: "POST",
      body: { email, password, full_name: fullName },
    });
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(async () => {
    await apiFetch("/api/auth/logout/", { method: "POST" });
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, refresh, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
