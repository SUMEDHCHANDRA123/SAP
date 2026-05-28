import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { downloadJobErrors, getJobs } from "../api/client";
import Badge from "../components/Badge";
import PageHeader from "../components/PageHeader";
import Spinner from "../components/Spinner";
import { formatRelativeTime } from "../utils/labels";

const STATUS_STYLES = {
  PROCESSING: "bg-blue-100 text-blue-800 ring-blue-200",
  DONE: "bg-emerald-100 text-emerald-800 ring-emerald-200",
  FAILED: "bg-red-100 text-red-800 ring-red-200",
};

const JOB_SOURCE_LABELS = {
  SAP_FUEL: "SAP Fuel",
  UTILITY_ELECTRICITY: "Utility",
  TRAVEL: "Travel",
};

export default function JobsPage() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const { data } = await getJobs();
        setJobs(data);
      } catch {
        setJobs([]);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleDownloadErrors = async (jobId) => {
    setDownloadingId(jobId);
    try {
      const { data } = await downloadJobErrors(jobId);
      const url = window.URL.createObjectURL(data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `job_${jobId}_errors.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div>
      <PageHeader
        title="Ingestion History"
        subtitle="Click a row to review records from that upload."
      />

      {loading ? (
        <Spinner label="Loading jobs..." />
      ) : jobs.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white py-20 text-center shadow-sm">
          <p className="text-lg font-medium text-slate-700">
            No ingestion jobs yet
          </p>
          <p className="mt-1 text-sm text-slate-500">
            Upload a CSV to create your first job.
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
          <table className="w-full text-left">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-600">
              <tr>
                <th className="px-4 py-3">File Name</th>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3">Uploaded</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Rows</th>
                <th className="px-4 py-3">Errors</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr
                  key={job.id}
                  onClick={() => navigate(`/records?job=${job.id}`)}
                  className="cursor-pointer border-b border-slate-100 transition-colors hover:bg-emerald-50/80"
                >
                  <td className="px-4 py-3">
                    <span className="text-sm font-medium text-slate-900">
                      {job.file_name}
                    </span>
                    <span className="ml-2 font-mono text-xs text-slate-400">
                      #{job.id}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-700">
                    {JOB_SOURCE_LABELS[job.source_type] || job.source_type}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-slate-700">
                      {formatRelativeTime(job.uploaded_at)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Badge className={STATUS_STYLES[job.status] || "bg-slate-100"}>
                      {job.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-sm font-medium tabular-nums">
                    {job.row_count}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-sm font-medium tabular-nums ${
                        job.error_count > 0 ? "text-red-600" : "text-slate-600"
                      }`}
                    >
                      {job.error_count}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {job.error_count > 0 ? (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDownloadErrors(job.id);
                        }}
                        className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
                      >
                        {downloadingId === job.id ? "Exporting..." : "Export Errors"}
                      </button>
                    ) : (
                      <span className="text-xs text-slate-400">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
