import { useState } from "react";
import {
  approveRecord,
  flagRecord,
  getRecord,
  rejectRecord,
} from "../api/client";
import {
  labelScope,
  labelSource,
  SCOPE_BADGE,
  SOURCE_BADGE,
  STATUS_BADGE,
} from "../utils/labels";
import Badge from "./Badge";
import { useToast } from "./Toast";
import Spinner from "./Spinner";

const ROW_BG = {
  PENDING: "bg-white",
  FLAGGED: "bg-[#FEF9C3]",
  APPROVED: "bg-[#F0FDF4]",
  REJECTED: "bg-[#FEF2F2]",
};

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function ActionButton({ children, variant, disabled, onClick }) {
  const variants = {
    approve:
      "border-emerald-600 text-emerald-700 hover:bg-emerald-50 focus-visible:ring-emerald-500",
    reject:
      "border-red-600 text-red-700 hover:bg-red-50 focus-visible:ring-red-500",
    flag: "border-amber-500 text-amber-700 hover:bg-amber-50 focus-visible:ring-amber-500",
    submit:
      "border-slate-400 bg-slate-800 text-white hover:bg-slate-900 focus-visible:ring-slate-500",
  };

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`inline-flex items-center rounded-lg border px-2.5 py-1 text-xs font-semibold transition focus-visible:outline focus-visible:ring-2 focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]}`}
    >
      {children}
    </button>
  );
}

export default function RecordRow({
  record,
  canReview = false,
  onUpdated,
  loadingId,
  setLoadingId,
  zebra = false,
}) {
  const { showToast } = useToast();
  const [expanded, setExpanded] = useState(false);
  const [rawData, setRawData] = useState(null);
  const [loadingRaw, setLoadingRaw] = useState(false);
  const [showReject, setShowReject] = useState(false);
  const [showFlag, setShowFlag] = useState(false);
  const [rejectNote, setRejectNote] = useState("");
  const [flagReason, setFlagReason] = useState("");

  const isBusy = loadingId === record.id;
  const locked = record.is_locked;
  const baseBg = ROW_BG[record.status] || "bg-white";
  const bg =
    record.status === "PENDING" && zebra ? "bg-slate-50/90" : baseBg;

  const runAction = async (action, successMsg, toastType) => {
    setLoadingId(record.id);
    try {
      const { data } = await action();
      onUpdated(data);
      showToast(successMsg, toastType);
      setShowReject(false);
      setShowFlag(false);
      setRejectNote("");
      setFlagReason("");
    } catch (err) {
      const msg =
        err.response?.data?.detail || "Action failed. Please try again.";
      showToast(msg, "error");
    } finally {
      setLoadingId(null);
    }
  };

  const handleExpand = async () => {
    const next = !expanded;
    setExpanded(next);
    if (next && !rawData) {
      setLoadingRaw(true);
      try {
        const { data } = await getRecord(record.id);
        setRawData(data.raw_data);
      } catch {
        showToast("Could not load raw data", "error");
        setExpanded(false);
      } finally {
        setLoadingRaw(false);
      }
    }
  };

  const renderActions = () => {
    if (!canReview) {
      return (
        <span className="inline-flex items-center rounded-lg bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
          View only
        </span>
      );
    }
    if (locked || record.status === "APPROVED") {
      return (
        <span
          className="inline-flex items-center gap-1 rounded-lg bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-800"
          title="Locked"
        >
          <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
              clipRule="evenodd"
            />
          </svg>
          Locked
        </span>
      );
    }
    if (record.status === "REJECTED") {
      return (
        <span className="max-w-[140px] truncate text-xs text-red-700" title={record.reject_note}>
          {record.reject_note || "Rejected"}
        </span>
      );
    }

    const disabled = isBusy || locked;

    return (
      <div
        className="flex flex-wrap items-center gap-1.5"
        onClick={(e) => e.stopPropagation()}
      >
        {(record.status === "PENDING" || record.status === "FLAGGED") && (
          <ActionButton
            variant="approve"
            disabled={disabled}
            onClick={() =>
              runAction(
                () => approveRecord(record.id),
                "Record approved",
                "success"
              )
            }
          >
            Approve
          </ActionButton>
        )}

        {(record.status === "PENDING" || record.status === "FLAGGED") && (
          <>
            {!showReject ? (
              <ActionButton
                variant="reject"
                disabled={disabled}
                onClick={() => setShowReject(true)}
              >
                Reject
              </ActionButton>
            ) : (
              <div className="flex items-center gap-1">
                <input
                  type="text"
                  value={rejectNote}
                  onChange={(e) => setRejectNote(e.target.value)}
                  placeholder="Note"
                  className="w-28 rounded-lg border border-slate-300 px-2 py-1 text-xs focus:border-red-400 focus:outline-none focus:ring-1 focus:ring-red-400"
                />
                <ActionButton
                  variant="submit"
                  disabled={disabled}
                  onClick={() =>
                    runAction(
                      () => rejectRecord(record.id, rejectNote),
                      "Record rejected",
                      "error"
                    )
                  }
                >
                  OK
                </ActionButton>
              </div>
            )}
          </>
        )}

        {record.status === "PENDING" && (
          <>
            {!showFlag ? (
              <ActionButton
                variant="flag"
                disabled={disabled}
                onClick={() => setShowFlag(true)}
              >
                Flag
              </ActionButton>
            ) : (
              <div className="flex items-center gap-1">
                <input
                  type="text"
                  value={flagReason}
                  onChange={(e) => setFlagReason(e.target.value)}
                  placeholder="Reason"
                  className="w-28 rounded-lg border border-slate-300 px-2 py-1 text-xs focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                />
                <ActionButton
                  variant="submit"
                  disabled={disabled}
                  onClick={() =>
                    runAction(
                      () => flagRecord(record.id, flagReason),
                      "Record flagged",
                      "warning"
                    )
                  }
                >
                  OK
                </ActionButton>
              </div>
            )}
          </>
        )}
      </div>
    );
  };

  return (
    <>
      <tr
        className={`cursor-pointer border-b border-slate-100 transition-colors ${bg} hover:brightness-[0.98]`}
        onClick={handleExpand}
      >
        <td className="px-2 py-3 text-slate-400">
          <svg
            className={`h-4 w-4 transition-transform ${expanded ? "rotate-90" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </td>
        <td className="px-4 py-3">
          <Badge className={SOURCE_BADGE[record.source_type] || "bg-slate-100 text-slate-700"}>
            {labelSource(record.source_type)}
          </Badge>
          {record.anomaly_count > 0 && (
            <span className="ml-2">
              <Badge className="bg-red-100 text-red-800 ring-red-200">
                {record.anomaly_count} alert{record.anomaly_count === 1 ? "" : "s"}
              </Badge>
            </span>
          )}
        </td>
        <td className="px-4 py-3">
          <Badge className={SCOPE_BADGE[record.scope] || "bg-slate-100 text-slate-700"}>
            {labelScope(record.scope)}
          </Badge>
        </td>
        <td className="px-4 py-3 text-sm font-medium tabular-nums text-slate-900">
          {record.activity_value}
        </td>
        <td className="px-4 py-3 text-sm text-slate-600">{record.activity_unit}</td>
        <td className="px-4 py-3">
          <Badge className={STATUS_BADGE[record.status]}>
            {record.status}
          </Badge>
          {record.status === "FLAGGED" && record.flag_reason && (
            <p className="mt-1 max-w-[120px] truncate text-xs text-amber-800" title={record.flag_reason}>
              {record.flag_reason}
            </p>
          )}
        </td>
        <td className="px-4 py-3 text-sm text-slate-600">
          {formatDate(record.created_at)}
        </td>
        <td className="px-4 py-3">{renderActions()}</td>
      </tr>
      {expanded && (
        <tr className={bg}>
          <td colSpan={8} className="px-4 pb-4 pl-10">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Raw data
            </p>
            {loadingRaw ? (
              <Spinner label="Loading raw data..." size="sm" />
            ) : (
              <pre className="max-h-64 overflow-auto rounded-xl border border-slate-200 bg-slate-900 p-4 font-mono text-xs leading-relaxed text-emerald-100">
                {JSON.stringify(rawData, null, 2)}
              </pre>
            )}
          </td>
        </tr>
      )}
    </>
  );
}
