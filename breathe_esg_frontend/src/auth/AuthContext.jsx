import { createContext, useContext, useEffect, useMemo, useState } from "react";
import {
  authMe,
  getActiveTenantId,
  loginSession,
  logoutSession,
  setActiveTenantId,
} from "../api/client";

const AuthContext = createContext(null);

const ROLE_ORDER = {
  ANALYST: 1,
  REVIEWER: 2,
  MANAGER: 3,
  ADMIN: 4,
};

export function AuthProvider({ children }) {
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [memberships, setMemberships] = useState([]);

  const refreshAuth = async () => {
    setLoading(true);
    try {
      const { data } = await authMe();
      setAuthenticated(Boolean(data.authenticated));
      setUser(data.user || null);
      setMemberships(data.memberships || []);
    } catch {
      setAuthenticated(false);
      setUser(null);
      setMemberships([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshAuth();
  }, []);

  const activeTenantMembership = useMemo(() => {
    const tenantId = Number(getActiveTenantId() || 0);
    if (!tenantId) return null;
    return memberships.find((m) => Number(m.tenant_id) === tenantId) || null;
  }, [memberships]);

  const activeRole = activeTenantMembership?.role || null;

  const hasRoleAtLeast = (minRole) => {
    if (user?.is_superuser) return true;
    if (!activeRole) return false;
    return (ROLE_ORDER[activeRole] || 0) >= (ROLE_ORDER[minRole] || 0);
  };

  const login = async (username, password) => {
    await loginSession(username, password);
    await refreshAuth();
  };

  const logout = async () => {
    try {
      await logoutSession();
    } catch {
      // Clear local session even if network logout fails.
    }
    setActiveTenantId(null);
    setAuthenticated(false);
    setUser(null);
    setMemberships([]);
    window.location.assign("/login");
  };

  const value = {
    loading,
    authenticated,
    user,
    memberships,
    activeTenantMembership,
    activeRole,
    hasRoleAtLeast,
    refreshAuth,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return ctx;
}

