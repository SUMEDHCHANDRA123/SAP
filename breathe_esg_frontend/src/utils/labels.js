export const SOURCE_LABELS = {
  SAP_FUEL: "SAP Fuel",
  SAP_PROCUREMENT: "SAP Procurement",
  UTILITY_ELECTRICITY: "Utility Electricity",
  TRAVEL_FLIGHT: "Travel Flight",
  TRAVEL_HOTEL: "Travel Hotel",
  TRAVEL_GROUND: "Travel Ground",
};

export const SOURCE_BADGE = {
  SAP_FUEL: "bg-amber-100 text-amber-800 ring-amber-200",
  SAP_PROCUREMENT: "bg-amber-50 text-amber-700 ring-amber-200",
  UTILITY_ELECTRICITY: "bg-sky-100 text-sky-800 ring-sky-200",
  TRAVEL_FLIGHT: "bg-violet-100 text-violet-800 ring-violet-200",
  TRAVEL_HOTEL: "bg-purple-100 text-purple-800 ring-purple-200",
  TRAVEL_GROUND: "bg-indigo-100 text-indigo-800 ring-indigo-200",
};

export const SCOPE_BADGE = {
  SCOPE_1: "bg-orange-100 text-orange-800 ring-orange-200",
  SCOPE_2: "bg-blue-100 text-blue-800 ring-blue-200",
  SCOPE_3: "bg-purple-100 text-purple-800 ring-purple-200",
};

export const SCOPE_LABELS = {
  SCOPE_1: "Scope 1",
  SCOPE_2: "Scope 2",
  SCOPE_3: "Scope 3",
};

export const STATUS_BADGE = {
  PENDING: "bg-slate-100 text-slate-700 ring-slate-200",
  FLAGGED: "bg-amber-100 text-amber-800 ring-amber-200",
  APPROVED: "bg-emerald-100 text-emerald-800 ring-emerald-200",
  REJECTED: "bg-red-100 text-red-800 ring-red-200",
};

export function labelSource(type) {
  return SOURCE_LABELS[type] || type;
}

export function labelScope(scope) {
  return SCOPE_LABELS[scope] || scope;
}

export function formatRelativeTime(iso) {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}
