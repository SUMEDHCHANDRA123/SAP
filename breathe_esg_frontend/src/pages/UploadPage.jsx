import { useRef, useState } from "react";
import { ingestSap, ingestSapProcurement, ingestTravel, ingestUtility } from "../api/client";
import PageHeader from "../components/PageHeader";
import { useToast } from "../components/Toast";

const UPLOAD_CARDS = [
  {
    id: "sap",
    title: "SAP Fuel",
    icon: "⛽",
    description:
      "SAP export with WERKS, MENGE, MEINS, BLDAT, MATNR, KOSTL, BKTXT, LIFNR.",
    ingest: ingestSap,
    accent: "border-amber-300 bg-gradient-to-br from-amber-50 to-white ring-amber-200/60",
    button: "bg-amber-600 hover:bg-amber-700 focus-visible:ring-amber-500",
    dropActive: "border-amber-500 bg-amber-50/80",
  },
  {
    id: "sap_proc",
    title: "SAP Procurement",
    icon: "🧾",
    description:
      "Procurement export with EBELN, EBELP, WERKS, MATNR, MENGE, MEINS, NETWR, WAERS, BLDAT, LIFNR.",
    ingest: ingestSapProcurement,
    accent: "border-orange-300 bg-gradient-to-br from-orange-50 to-white ring-orange-200/60",
    button: "bg-orange-600 hover:bg-orange-700 focus-visible:ring-orange-500",
    dropActive: "border-orange-500 bg-orange-50/80",
  },
  {
    id: "utility",
    title: "Utility Electricity",
    icon: "⚡",
    description:
      "Utility bills with meter_id, site_name, billing periods, consumption_kwh, supplier.",
    ingest: ingestUtility,
    accent: "border-sky-300 bg-gradient-to-br from-sky-50 to-white ring-sky-200/60",
    button: "bg-sky-600 hover:bg-sky-700 focus-visible:ring-sky-500",
    dropActive: "border-sky-500 bg-sky-50/80",
  },
  {
    id: "travel",
    title: "Travel (Concur)",
    icon: "✈️",
    description:
      "Travel expenses with trip_id, category, distance_km, nights, cost_usd, department.",
    ingest: ingestTravel,
    accent: "border-violet-300 bg-gradient-to-br from-violet-50 to-white ring-violet-200/60",
    button: "bg-violet-600 hover:bg-violet-700 focus-visible:ring-violet-500",
    dropActive: "border-violet-500 bg-violet-50/80",
  },
];

function UploadCard({ card }) {
  const { showToast } = useToast();
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [errorsOpen, setErrorsOpen] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const pickFile = (f) => {
    if (f && f.name.toLowerCase().endsWith(".csv")) {
      setFile(f);
      setResult(null);
    } else if (f) {
      showToast("Please select a .csv file", "warning");
    }
  };

  const handleUpload = async () => {
    if (!file) {
      showToast("Please select a CSV file first", "warning");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const { data } = await card.ingest(file);
      setResult({ status: "DONE", ...data });
      showToast(`${card.title} upload complete`, "success");
    } catch (err) {
      const msg = err.response?.data?.detail || "Upload failed";
      setResult({
        status: "FAILED",
        job_id: err.response?.data?.job_id,
        row_count: 0,
        error_count: 1,
        errors: [{ row_number: null, reason: msg }],
      });
      showToast(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    pickFile(e.dataTransfer.files?.[0]);
  };

  const statusBadge = () => {
    if (loading) {
      return (
        <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-800">
          Processing
        </span>
      );
    }
    if (!result) return null;
    const colors =
      result.status === "DONE"
        ? "bg-emerald-100 text-emerald-800"
        : "bg-red-100 text-red-800";
    return (
      <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${colors}`}>
        {result.status === "DONE" ? "Done" : "Failed"}
      </span>
    );
  };

  return (
    <div
      className={`flex flex-col rounded-2xl border-2 p-6 shadow-md ring-1 ${card.accent}`}
    >
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-2xl" aria-hidden>
            {card.icon}
          </span>
          <h2 className="text-lg font-semibold text-slate-900">{card.title}</h2>
        </div>
        {statusBadge()}
      </div>
      <p className="mb-4 flex-1 text-sm leading-relaxed text-slate-600">
        {card.description}
      </p>

      <div
        role="button"
        tabIndex={0}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        className={`mb-4 cursor-pointer rounded-xl border-2 border-dashed px-4 py-8 text-center transition-colors ${
          dragOver ? card.dropActive : "border-slate-300 bg-white/60 hover:border-slate-400 hover:bg-white"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => pickFile(e.target.files?.[0])}
        />
        <p className="text-sm font-medium text-slate-700">
          Drop CSV here or click to browse
        </p>
        {file ? (
          <p className="mt-2 text-xs text-slate-500">
            <span className="font-semibold text-slate-800">{file.name}</span>
            {" · "}
            {(file.size / 1024).toFixed(1)} KB
          </p>
        ) : (
          <p className="mt-1 text-xs text-slate-400">.csv files only</p>
        )}
      </div>

      {loading && (
        <div className="mb-3 h-1 overflow-hidden rounded-full bg-slate-200">
          <div className="h-full w-1/3 rounded-full bg-emerald-500 animate-progress" />
        </div>
      )}

      <button
        type="button"
        onClick={handleUpload}
        disabled={loading || !file}
        className={`rounded-xl px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition focus-visible:outline focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${card.button}`}
      >
        {loading ? "Uploading…" : "Upload"}
      </button>

      {result && (
        <div className="mt-4 space-y-2 rounded-xl border border-slate-200/80 bg-white/80 p-4 text-sm backdrop-blur-sm">
          {result.job_id && (
            <p>
              <span className="font-medium text-slate-500">Job ID</span>{" "}
              <span className="font-mono text-slate-800">#{result.job_id}</span>
            </p>
          )}
          <div className="flex gap-4">
            <p>
              <span className="font-medium text-slate-500">Rows</span>{" "}
              <span className="font-semibold">{result.row_count ?? 0}</span>
            </p>
            <p>
              <span className="font-medium text-slate-500">Errors</span>{" "}
              <span
                className={`font-semibold ${result.error_count > 0 ? "text-red-600" : "text-emerald-600"}`}
              >
                {result.error_count ?? 0}
              </span>
            </p>
          </div>

          {result.errors?.length > 0 && (
            <div>
              <button
                type="button"
                onClick={() => setErrorsOpen(!errorsOpen)}
                className="text-sm font-medium text-emerald-700 hover:underline"
              >
                {errorsOpen ? "Hide" : "Show"} error details ({result.errors.length})
              </button>
              {errorsOpen && (
                <ul className="mt-2 max-h-40 space-y-1.5 overflow-auto rounded-lg bg-red-50 p-3 text-xs text-red-900 ring-1 ring-red-100">
                  {result.errors.map((err, i) => (
                    <li key={i} className="border-b border-red-100/80 pb-1 last:border-0 last:pb-0">
                      <span className="font-semibold">Row {err.row_number ?? "—"}</span>
                      {": "}
                      {err.reason}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function UploadPage() {
  return (
    <div>
      <PageHeader
        title="Upload Data"
        subtitle="Import CSV files from SAP, utility providers, or travel systems."
      />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        {UPLOAD_CARDS.map((card) => (
          <UploadCard key={card.id} card={card} />
        ))}
      </div>
    </div>
  );
}
