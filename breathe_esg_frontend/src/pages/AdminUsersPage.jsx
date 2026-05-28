import { useCallback, useEffect, useState } from "react";
import { approveUser, getPendingUsers, getTenants } from "../api/client";
import PageHeader from "../components/PageHeader";
import Spinner from "../components/Spinner";
import { useToast } from "../components/Toast";

const ROLES = ["ANALYST", "REVIEWER", "MANAGER", "ADMIN"];

export default function AdminUsersPage() {
  const { showToast } = useToast();
  const [pending, setPending] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [approvingId, setApprovingId] = useState(null);
  const [tenantByUser, setTenantByUser] = useState({});
  const [roleByUser, setRoleByUser] = useState({});

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [usersRes, tenantsRes] = await Promise.all([getPendingUsers(), getTenants()]);
      setPending(usersRes.data || []);
      setTenants(tenantsRes.data || []);
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to load pending users", "error");
      setPending([]);
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    load();
  }, [load]);

  const handleApprove = async (userId) => {
    const tenantId = tenantByUser[userId];
    if (!tenantId) {
      showToast("Select a tenant before approving", "warning");
      return;
    }
    setApprovingId(userId);
    try {
      await approveUser(userId, {
        tenant_id: Number(tenantId),
        role: roleByUser[userId] || "ANALYST",
      });
      showToast("User approved", "success");
      await load();
    } catch (err) {
      showToast(err.response?.data?.detail || "Approval failed", "error");
    } finally {
      setApprovingId(null);
    }
  };

  return (
    <div>
      <PageHeader
        title="User Approvals"
        subtitle="Approve new accounts and assign tenant access."
      />

      {loading ? (
        <Spinner label="Loading pending users..." />
      ) : pending.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white py-16 text-center text-slate-600">
          No users waiting for approval.
        </div>
      ) : (
        <div className="space-y-3">
          {pending.map((u) => (
            <div
              key={u.id}
              className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
            >
              <div className="min-w-[160px] flex-1">
                <p className="font-semibold text-slate-900">{u.username}</p>
                <p className="text-xs text-slate-500">
                  Registered {new Date(u.created_at).toLocaleString()}
                </p>
              </div>
              <select
                value={tenantByUser[u.id] || ""}
                onChange={(e) =>
                  setTenantByUser((prev) => ({ ...prev, [u.id]: e.target.value }))
                }
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                <option value="">Select tenant</option>
                {tenants.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
              <select
                value={roleByUser[u.id] || "ANALYST"}
                onChange={(e) =>
                  setRoleByUser((prev) => ({ ...prev, [u.id]: e.target.value }))
                }
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                {ROLES.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
              <button
                type="button"
                disabled={approvingId === u.id}
                onClick={() => handleApprove(u.id)}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60"
              >
                {approvingId === u.id ? "Approving..." : "Approve"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
