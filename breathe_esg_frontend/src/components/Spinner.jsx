export default function Spinner({ label = "Loading...", size = "md" }) {
  const sizes = {
    sm: "h-6 w-6 border-2",
    md: "h-10 w-10 border-4",
  };

  return (
    <div className="flex flex-col items-center justify-center gap-3 py-8">
      <div
        className={`animate-spin rounded-full border-emerald-200 border-t-emerald-600 ${sizes[size] || sizes.md}`}
        role="status"
        aria-label={label}
      />
      {label && <p className="text-sm font-medium text-slate-500">{label}</p>}
    </div>
  );
}
