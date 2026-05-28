import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { getActiveTenantId, getTenants, setActiveTenantId } from "../api/client";
import { useAuth } from "../auth/AuthContext";

const linkClass = ({ isActive }) =>
  `block rounded-lg px-3 py-2 text-sm font-medium transition-all ${
    isActive
      ? "bg-white/20 text-white shadow-sm ring-1 ring-white/30"
      : "text-emerald-100 hover:bg-white/10 hover:text-white"
  }`;

const baseNavItems = [
  { to: "/analytics", label: "Analytics" },
  { to: "/upload", label: "Upload" },
  { to: "/records", label: "Review" },
  { to: "/jobs", label: "History" },
];

export default function Navbar() {
  const { authenticated, user, activeRole, hasRoleAtLeast, logout } = useAuth();
  const navItems = hasRoleAtLeast("ADMIN")
    ? [...baseNavItems, { to: "/admin/users", label: "Approvals" }]
    : baseNavItems;
  const [mobileOpen, setMobileOpen] = useState(false);
  const [tenants, setTenants] = useState([]);
  const [tenantId, setTenantId] = useState(getActiveTenantId() || "");
  const [loadingTenants, setLoadingTenants] = useState(true);

  useEffect(() => {
    if (!authenticated) {
      setLoadingTenants(false);
      setTenants([]);
      return;
    }
    let mounted = true;
    getTenants()
      .then(({ data }) => {
        if (!mounted) return;
        setTenants(data || []);
        const current = String(getActiveTenantId() || "");
        if (current) {
          setTenantId(current);
          return;
        }
        if (data?.length) {
          const fallback = String(data[0].id);
          setActiveTenantId(fallback);
          setTenantId(fallback);
        }
      })
      .catch(() => {
        if (mounted) setTenants([]);
      })
      .finally(() => {
        if (mounted) setLoadingTenants(false);
      });
    return () => {
      mounted = false;
    };
  }, [authenticated]);

  const handleTenantChange = (nextTenantId) => {
    setActiveTenantId(nextTenantId);
    setTenantId(String(nextTenantId));
    window.location.reload();
  };

  return (
    <header className="sticky top-0 z-40 border-b border-emerald-900/30 bg-emerald-800 text-white shadow-lg shadow-emerald-900/10">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <NavLink to="/analytics" className="group flex flex-col">
          <span className="text-lg font-bold tracking-tight">
            🌿 Breathe ESG
          </span>
          <span className="text-xs font-medium text-emerald-200/90 group-hover:text-emerald-100">
            Carbon data ingestion
          </span>
        </NavLink>

        {authenticated && (
          <label className="mx-3 inline-flex min-w-[132px] items-center gap-2 rounded-lg bg-white/10 px-2.5 py-1.5 text-xs font-medium text-emerald-100 ring-1 ring-white/20">
            Tenant
            <select
              value={tenantId}
              disabled={loadingTenants || tenants.length === 0}
              onChange={(e) => handleTenantChange(e.target.value)}
              className="w-full rounded-md border border-white/20 bg-emerald-900/40 px-2 py-1 text-xs text-white focus:outline-none disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loadingTenants && <option value="">Loading...</option>}
              {!loadingTenants && tenants.length === 0 && <option value="">No tenants</option>}
              {!loadingTenants &&
                tenants.map((tenant) => (
                  <option key={tenant.id} value={tenant.id} className="text-slate-900">
                    {tenant.name}
                  </option>
                ))}
            </select>
          </label>
        )}

        <nav className="hidden items-center gap-1 md:flex">
          {authenticated ? (
            <>
              {navItems.map((item) => (
                <NavLink key={item.to} to={item.to} className={linkClass}>
                  {item.label}
                </NavLink>
              ))}
              <span className="ml-2 rounded-lg bg-white/10 px-2 py-1 text-xs text-emerald-100 ring-1 ring-white/20">
                {user?.username} {activeRole ? `(${activeRole})` : ""}
              </span>
              <button
                type="button"
                onClick={logout}
                className="ml-2 rounded-lg bg-white/10 px-3 py-2 text-xs font-medium text-emerald-100 hover:bg-white/20"
              >
                Logout
              </button>
            </>
          ) : (
            <NavLink to="/login" className={linkClass}>
              Login
            </NavLink>
          )}
        </nav>

        <button
          type="button"
          className="rounded-lg p-2 text-emerald-100 hover:bg-white/10 md:hidden"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {mobileOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {mobileOpen && (
        <nav className="border-t border-emerald-700/50 px-4 py-3 md:hidden">
          <div className="flex flex-col gap-1">
            {authenticated ? (
              <>
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={linkClass}
                    onClick={() => setMobileOpen(false)}
                  >
                    {item.label}
                  </NavLink>
                ))}
                <button
                  type="button"
                  onClick={() => {
                    logout();
                    setMobileOpen(false);
                  }}
                  className="mt-1 rounded-lg bg-white/10 px-3 py-2 text-left text-sm font-medium text-emerald-100 hover:bg-white/20"
                >
                  Logout
                </button>
              </>
            ) : (
              <NavLink to="/login" className={linkClass} onClick={() => setMobileOpen(false)}>
                Login
              </NavLink>
            )}
          </div>
        </nav>
      )}
    </header>
  );
}
