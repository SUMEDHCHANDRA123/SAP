export default function StatCard({ label, value, accent = "slate" }) {
  const accents = {
    slate: "border-slate-200 bg-white text-slate-900",
    amber: "border-amber-200 bg-amber-50 text-amber-900",
    emerald: "border-emerald-200 bg-emerald-50 text-emerald-900",
    red: "border-red-200 bg-red-50 text-red-900",
    blue: "border-blue-200 bg-blue-50 text-blue-900",
  };

  return (
    <div
      className={`rounded-xl border px-4 py-3 shadow-sm ring-1 ring-black/5 ${accents[accent] || accents.slate}`}
    >
      <p className="text-xs font-medium uppercase tracking-wide opacity-70">
        {label}
      </p>
      <p className="mt-1 text-2xl font-bold tabular-nums">{value}</p>
    </div>
  );
}
