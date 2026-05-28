import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { getRecords } from "../api/client";
import PageHeader from "../components/PageHeader";
import RecordRow from "../components/RecordRow";
import Spinner from "../components/Spinner";
import StatCard from "../components/StatCard";
import { labelSource } from "../utils/labels";
import { useAuth } from "../auth/AuthContext";

const STATUS_OPTIONS = [
  { value: "", label: "All Status" },
  { value: "PENDING", label: "Pending" },
  { value: "FLAGGED", label: "Flagged" },
  { value: "APPROVED", label: "Approved" },
  { value: "REJECTED", label: "Rejected" },
];

const SOURCE_OPTIONS = [
  { value: "", label: "All Sources" },
  { value: "SAP_FUEL", label: "SAP Fuel" },
  { value: "UTILITY_ELECTRICITY", label: "Utility Electricity" },
  { value: "TRAVEL_FLIGHT", label: "Travel Flight" },
  { value: "TRAVEL_HOTEL", label: "Travel Hotel" },
  { value: "TRAVEL_GROUND", label: "Travel Ground" },
];

export default function ReviewPage() {
  const { hasRoleAtLeast } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const jobFromUrl = searchParams.get("job") || "";

  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("");
  const [sourceType, setSourceType] = useState("");
  const [job, setJob] = useState(jobFromUrl);
  const [hasAnomalies, setHasAnomalies] = useState(false);
  const [loadingId, setLoadingId] = useState(null);
  const [tipsOpen, setTipsOpen] = useState(false);
  const canReview = hasRoleAtLeast("REVIEWER");

  const fetchRecords = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (status) params.status = status;
      if (sourceType) params.source_type = sourceType;
      if (job) params.job = job;
      if (hasAnomalies) params.has_anomalies = "1";
      const { data } = await getRecords(params);
      setRecords(data);
    } catch {
      setRecords([]);
    } finally {
      setLoading(false);
    }
  }, [status, sourceType, job, hasAnomalies]);

  useEffect(() => {
    setJob(jobFromUrl);
  }, [jobFromUrl]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  const stats = useMemo(() => {
    const counts = { PENDING: 0, FLAGGED: 0, APPROVED: 0, REJECTED: 0 };
    records.forEach((r) => {
      if (counts[r.status] !== undefined) counts[r.status]++;
    });
    return counts;
  }, [records]);

  const handleUpdated = (updated) => {
    setRecords((prev) =>
      prev.map((r) => (r.id === updated.id ? { ...r, ...updated } : r))
    );
  };

  const clearFilters = () => {
    setStatus("");
    setSourceType("");
    setJob("");
    setHasAnomalies(false);
    navigate("/records");
  };

  return (
    <div>
      <PageHeader
        title="Review Records"
        subtitle={
          job
            ? `Showing records from ingestion job #${job}`
            : "Verify and approve emission data before reporting."
        }
      />

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Pending" value={stats.PENDING} accent="slate" />
        <StatCard label="Flagged" value={stats.FLAGGED} accent="amber" />
        <StatCard label="Approved" value={stats.APPROVED} accent="emerald" />
        <StatCard label="Rejected" value={stats.REJECTED} accent="red" />
      </div>

      <div className="mb-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm ring-1 ring-slate-900/5">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
          >
            {STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
            className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
          >
            {SOURCE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={clearFilters}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
          >
            Clear filters
          </button>
          <label className="ml-1 inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700">
            <input
              type="checkbox"
              checked={hasAnomalies}
              onChange={(e) => setHasAnomalies(e.target.checked)}
            />
            Has alerts
          </label>
          {job && (
            <button
              type="button"
              onClick={clearFilters}
              className="rounded-lg bg-emerald-100 px-3 py-2 text-sm font-medium text-emerald-800"
            >
              Clear job filter
            </button>
          )}
        </div>

        <button
          type="button"
          onClick={() => setTipsOpen(!tipsOpen)}
          className="mt-3 text-xs font-medium text-emerald-700 hover:underline"
        >
          {tipsOpen ? "Hide" : "Show"} review tips
        </button>
        {tipsOpen && (
          <p className="mt-2 rounded-lg bg-emerald-50 p-3 text-xs leading-relaxed text-emerald-900">
            Expand a row to inspect raw CSV data. Approve when quantity, unit, date,
            and site look correct. Flag uncertain rows for investigation. Reject
            duplicates or invalid entries.
          </p>
        )}
      </div>

      {loading ? (
        <Spinner label="Loading records..." />
      ) : records.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white py-20 text-center shadow-sm">
          <p className="text-lg font-medium text-slate-700">
            No records yet
          </p>
          <p className="mt-1 text-sm text-slate-500">
            Upload a file to get started.
          </p>
          <Link
            to="/upload"
            className="mt-4 inline-block rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
          >
            Go to Upload →
          </Link>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-md ring-1 ring-slate-900/5">
          <div className="max-h-[70vh] overflow-auto">
            <table className="w-full min-w-[800px] text-left">
              <thead className="sticky top-0 z-10 border-b border-slate-200 bg-slate-50/95 text-xs font-semibold uppercase tracking-wide text-slate-600 backdrop-blur-sm">
                <tr>
                  <th className="w-8 px-2 py-3" />
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Scope</th>
                  <th className="px-4 py-3">Activity</th>
                  <th className="px-4 py-3">Unit</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Ingested</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record, idx) => (
                  <RecordRow
                    key={record.id}
                    record={record}
                    canReview={canReview}
                    onUpdated={handleUpdated}
                    loadingId={loadingId}
                    setLoadingId={setLoadingId}
                    zebra={record.status === "PENDING" && idx % 2 === 1}
                  />
                ))}
              </tbody>
            </table>
          </div>
          <div className="border-t border-slate-100 bg-slate-50 px-4 py-2 text-xs text-slate-500">
            {records.length} record{records.length !== 1 ? "s" : ""} shown
            {sourceType && ` · ${labelSource(sourceType)}`}
          </div>
        </div>
      )}
    </div>
  );
}
