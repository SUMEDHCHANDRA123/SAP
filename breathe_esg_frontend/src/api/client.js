import axios from "axios";

// In dev, use Vite proxy (same origin) so Django session cookies work after login.
const baseURL = import.meta.env.DEV
  ? ""
  : import.meta.env.VITE_API_URL || "http://localhost:8000";
const tenantIdFromEnv = import.meta.env.VITE_TENANT_ID;
const TENANT_STORAGE_KEY = "breatheTenantId";

export const api = axios.create({
  baseURL,
  withCredentials: true,
});

export const setActiveTenantId = (tenantId) => {
  if (!tenantId) {
    localStorage.removeItem(TENANT_STORAGE_KEY);
    return;
  }
  localStorage.setItem(TENANT_STORAGE_KEY, String(tenantId));
};

export const getActiveTenantId = () =>
  localStorage.getItem(TENANT_STORAGE_KEY) || tenantIdFromEnv || null;

function getCsrfToken() {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

api.interceptors.request.use((config) => {
  const method = (config.method || "get").toLowerCase();
  const unsafe = !["get", "head", "options", "trace"].includes(method);
  if (unsafe) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      config.headers = config.headers || {};
      config.headers["X-CSRFToken"] = csrfToken;
    }
  }

  const tenantId = getActiveTenantId();
  if (tenantId) {
    config.params = { ...(config.params || {}), tenant_id: tenantId };
  }
  return config;
});

export const getRecords = (params) => api.get("/api/records/", { params });
export const getTenants = () => api.get("/api/tenants/");
export const authMe = () => api.get("/api/auth/me/");
export const loginSession = (username, password) =>
  api.post("/api/auth/me/", { username, password });
export const registerUser = (username, password) =>
  api.post("/api/auth/register/", { username, password });
export const logoutSession = () => api.delete("/api/auth/me/");
export const getPendingUsers = () => api.get("/api/admin/users/pending/");
export const approveUser = (userId, payload) =>
  api.patch(`/api/admin/users/${userId}/approve/`, payload);

export const getRecord = (id) => api.get(`/api/records/${id}/`);

export const approveRecord = (id) => api.patch(`/api/records/${id}/approve/`);

export const rejectRecord = (id, note) =>
  api.patch(`/api/records/${id}/reject/`, { note });

export const flagRecord = (id, reason) =>
  api.patch(`/api/records/${id}/flag/`, { reason });

export const getJobs = () => api.get("/api/jobs/");
export const downloadJobErrors = (jobId) =>
  api.get(`/api/jobs/${jobId}/errors.csv`, { responseType: "blob" });
export const getTemplates = () => api.get("/api/templates/");
export const getFactors = () => api.get("/api/factors/");
export const getQualitySnapshots = () => api.get("/api/quality-snapshots/");
export const getAuditEvents = () => api.get("/api/audit-events/");
export const getTargets = () => api.get("/api/targets/");
export const createTarget = (payload) => api.post("/api/targets/", payload);
export const getScenarios = () => api.get("/api/scenarios/");
export const createScenario = (payload) => api.post("/api/scenarios/", payload);
export const getBenchmarks = () => api.get("/api/benchmarks/");

export const analyticsSummary = () => api.get("/api/analytics/summary/");
export const analyticsBreakdown = (groupBy = "scope") =>
  api.get("/api/analytics/breakdown/", { params: { group_by: groupBy } });
export const analyticsTrends = (period = "monthly", monthsBack = 12) =>
  api.get("/api/analytics/trends/", { params: { period, months_back: monthsBack } });
export const analyticsAnomalies = () => api.get("/api/analytics/anomalies/", { params: { limit: 100 } });
export const analyticsTargets = () => api.get("/api/analytics/targets/");
export const analyticsBenchmarkOverview = () => api.get("/api/analytics/benchmarks/");
export const analyticsScenarioOverview = () => api.get("/api/analytics/scenarios/");
export const refreshAnalytics = () => api.post("/api/analytics/refresh/");

export const ingestSap = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/api/ingest/sap/", formData);
};

export const ingestSapProcurement = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/api/ingest/sap-procurement/", formData);
};

export const ingestUtility = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/api/ingest/utility/", formData);
};

export const ingestTravel = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/api/ingest/travel/", formData);
};
