import { useEffect, useMemo, useState } from "react";
import PageHeader from "../components/PageHeader";
import Spinner from "../components/Spinner";
import StatCard from "../components/StatCard";
import Badge from "../components/Badge";
import { useToast } from "../components/Toast";
import {
  analyticsAnomalies,
  analyticsBenchmarkOverview,
  analyticsBreakdown,
  analyticsScenarioOverview,
  analyticsSummary,
  analyticsTargets,
  analyticsTrends,
  refreshAnalytics,
} from "../api/client";

function toNumber(v) {
  if (v === null || v === undefined) return 0;
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

function formatNumber(n, { decimals = 0 } = {}) {
  return toNumber(n).toLocaleString(undefined, {
    maximumFractionDigits: decimals,
  });
}

function pct(part, total) {
  const p = total > 0 ? (part / total) * 100 : 0;
  return Math.max(0, Math.min(100, p));
}

function pickTopBreakdown(breakdown) {
  const entries = Object.entries(breakdown || {})
    .map(([label, obj]) => ({ label, value: toNumber(obj?.value), code: obj?.code }))
    .sort((a, b) => b.value - a.value);
  return entries[0] || null;
}

function calcDeltaPercent(points) {
  if (!points || points.length < 2) return null;
  const a = toNumber(points[points.length - 2]?.total);
  const b = toNumber(points[points.length - 1]?.total);
  if (a === 0) return null;
  return ((b - a) / a) * 100;
}

export default function AnalyticsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [summary, setSummary] = useState(null);
  const [scopeBreakdown, setScopeBreakdown] = useState({});
  const [sourceBreakdown, setSourceBreakdown] = useState({});
  const [trends, setTrends] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [targets, setTargets] = useState([]);
  const [benchmarks, setBenchmarks] = useState([]);
  const [scenarios, setScenarios] = useState([]);

  async function loadAll() {
    setLoading(true);
    const calls = await Promise.allSettled([
      analyticsSummary(),
      analyticsBreakdown("scope"),
      analyticsBreakdown("source"),
      analyticsTrends("monthly", 12),
      analyticsAnomalies(),
      analyticsTargets(),
      analyticsBenchmarkOverview(),
      analyticsScenarioOverview(),
    ]);

    const failures = [];
    calls.forEach((entry, idx) => {
      if (entry.status !== "fulfilled") {
        failures.push(idx);
        return;
      }
      const data = entry.value.data;
      if (idx === 0) setSummary(data);
      if (idx === 1) setScopeBreakdown(data.breakdown || {});
      if (idx === 2) setSourceBreakdown(data.breakdown || {});
      if (idx === 3) setTrends(data.trends || []);
      if (idx === 4) setAnomalies(data || []);
      if (idx === 5) setTargets(data || []);
      if (idx === 6) setBenchmarks(data || []);
      if (idx === 7) setScenarios(data || []);
    });

    if (failures.length > 0) {
      showToast("Some analytics sections failed to load", "warning");
    }
    setLoading(false);
  }

  async function onRefresh() {
    setRefreshing(true);
    try {
      await refreshAnalytics();
      await loadAll();
      showToast("Analytics refreshed", "success");
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to refresh analytics", "error");
    } finally {
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadAll();
  }, []);

  const totalEmissions = toNumber(summary?.grand_total);
  const totalApprovedRecords = toNumber(summary?.record_count);

  const sourceEntries = useMemo(() => {
    const entries = Object.entries(sourceBreakdown || {})
      .map(([label, obj]) => ({ label, value: toNumber(obj?.value), code: obj?.code }))
      .sort((a, b) => b.value - a.value);
    return entries;
  }, [sourceBreakdown]);

  const scopeEntries = useMemo(() => {
    const entries = Object.entries(scopeBreakdown || {})
      .map(([label, obj]) => ({ label, value: toNumber(obj?.value), code: obj?.code }))
      .sort((a, b) => b.value - a.value);
    return entries;
  }, [scopeBreakdown]);

  const topSource = useMemo(() => pickTopBreakdown(sourceBreakdown), [sourceBreakdown]);
  const topScope = useMemo(() => pickTopBreakdown(scopeBreakdown), [scopeBreakdown]);
  const momDelta = useMemo(() => calcDeltaPercent(trends), [trends]);

  const anomaliesTop = useMemo(() => {
    const severityRank = { high: 3, medium: 2, low: 1 };
    return [...(anomalies || [])]
      .sort((a, b) => (severityRank[b.severity] || 0) - (severityRank[a.severity] || 0))
      .slice(0, 6);
  }, [anomalies]);

  if (loading) {
    return <Spinner label="Loading analytics..." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Analytics Dashboard"
        subtitle="A quick view of emissions drivers, trends, and risk signals."
      >
        <div className="flex flex-wrap items-center gap-2">
          <a
            href="http://localhost:8000/api/analytics/reports/export.csv"
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
          >
            Export report (CSV)
          </a>
          <button
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </PageHeader>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <StatCard
          label="Total Emissions (kg CO2e)"
          value={formatNumber(totalEmissions, { decimals: 0 })}
          accent="blue"
        />
        <StatCard
          label="Scope 1 (kg)"
          value={formatNumber(summary?.scope_1_total || 0, { decimals: 0 })}
          accent="amber"
        />
        <StatCard
          label="Scope 2 (kg)"
          value={formatNumber(summary?.scope_2_total || 0, { decimals: 0 })}
          accent="slate"
        />
        <StatCard
          label="Scope 3 (kg)"
          value={formatNumber(summary?.scope_3_total || 0, { decimals: 0 })}
          accent="slate"
        />
        <StatCard
          label="Approved Records"
          value={formatNumber(totalApprovedRecords, { decimals: 0 })}
          accent="emerald"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <InsightCard
          title="Biggest driver"
          subtitle="Top emission source today"
          value={
            topSource
              ? `${topSource.label} · ${formatNumber(topSource.value)} kg`
              : "No data"
          }
          badge={
            topSource
              ? `${pct(topSource.value, totalEmissions).toFixed(1)}%`
              : null
          }
        />
        <InsightCard
          title="Largest scope"
          subtitle="Where emissions sit by scope"
          value={
            topScope
              ? `${topScope.label} · ${formatNumber(topScope.value)} kg`
              : "No data"
          }
          badge={
            topScope ? `${pct(topScope.value, totalEmissions).toFixed(1)}%` : null
          }
        />
        <InsightCard
          title="Momentum"
          subtitle="Last period vs previous"
          value={
            momDelta === null
              ? "Not enough history"
              : `${momDelta > 0 ? "+" : ""}${momDelta.toFixed(1)}%`
          }
          badge={momDelta === null ? null : momDelta > 0 ? "Increase" : "Decrease"}
          tone={momDelta === null ? "neutral" : momDelta > 0 ? "risk" : "good"}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <BreakdownBars
          title="Emissions by Source"
          subtitle="Top sources ranked by contribution"
          entries={sourceEntries.slice(0, 8)}
          total={totalEmissions}
        />
        <BreakdownBars
          title="Emissions by Scope"
          subtitle="Scope distribution"
          entries={scopeEntries}
          total={totalEmissions}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <TrendSparkline
          title="12-month trend"
          subtitle="Total emissions per month"
          points={trends.slice(-12)}
        />
        <TargetsPanel title={`Targets (${targets.length})`} targets={targets} />
        <AnomaliesPanel title={`Anomalies (${anomalies.length})`} anomalies={anomaliesTop} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <CompactTable
          title={`Benchmarks (${benchmarks.length})`}
          subtitle="Intensity metrics and snapshots"
          columns={["Metric", "Value", "Date"]}
          rows={benchmarks.slice(0, 8).map((b) => [b.metric, formatNumber(b.value, { decimals: 4 }), b.date])}
          emptyText="No benchmark snapshots"
        />
        <CompactTable
          title={`Scenarios (${scenarios.length})`}
          subtitle="What-if simulations (projected deltas)"
          columns={["Scenario", "Δ (kg)", "Projected total (kg)"]}
          rows={scenarios.slice(0, 8).map((s) => [s.name, formatNumber(s.projected_delta_kg), formatNumber(s.projected_total_kg)])}
          emptyText="No scenarios yet"
        />
      </div>
    </div>
  );
}

function Card({ title, subtitle, children, right }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm ring-1 ring-slate-900/5">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
          {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
        </div>
        {right}
      </div>
      {children}
    </div>
  );
}

function InsightCard({ title, subtitle, value, badge, tone = "neutral" }) {
  const tones = {
    neutral: "bg-slate-100 text-slate-700 ring-slate-200",
    good: "bg-emerald-100 text-emerald-800 ring-emerald-200",
    risk: "bg-amber-100 text-amber-800 ring-amber-200",
  };

  return (
    <Card
      title={title}
      subtitle={subtitle}
      right={
        badge ? <Badge className={tones[tone]}>{badge}</Badge> : null
      }
    >
      <p className="text-lg font-semibold text-slate-900">{value}</p>
      <p className="mt-1 text-xs text-slate-500">
        Click “Refresh” after new approvals to update insights.
      </p>
    </Card>
  );
}

function BreakdownBars({ title, subtitle, entries, total }) {
  return (
    <Card title={title} subtitle={subtitle} right={<Badge className="bg-slate-100 text-slate-700 ring-slate-200">Top</Badge>}>
      {entries.length === 0 ? (
        <p className="text-sm text-slate-500">No data</p>
      ) : (
        <div className="space-y-3">
          {entries.map((e) => {
            const percent = pct(e.value, total);
            return (
              <div key={e.label} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="truncate font-medium text-slate-700">{e.label}</span>
                  <span className="ml-3 tabular-nums text-slate-600">
                    {formatNumber(e.value)} kg
                    <span className="ml-2 text-xs text-slate-400">
                      {percent.toFixed(1)}%
                    </span>
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-100">
                  <div
                    className="h-2 rounded-full bg-emerald-500"
                    style={{ width: `${percent}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}

function TrendSparkline({ title, subtitle, points }) {
  const vals = points.map((p) => toNumber(p.total));
  const max = Math.max(1, ...vals);
  const min = Math.min(...vals, 0);
  const range = Math.max(1, max - min);
  const W = 240;
  const H = 70;
  const step = points.length > 1 ? W / (points.length - 1) : W;
  const path = points
    .map((p, i) => {
      const x = i * step;
      const y = H - ((toNumber(p.total) - min) / range) * H;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const last = points[points.length - 1];

  return (
    <Card
      title={title}
      subtitle={subtitle}
      right={
        last ? (
          <Badge className="bg-slate-100 text-slate-700 ring-slate-200">
            {last.date}
          </Badge>
        ) : null
      }
    >
      {points.length === 0 ? (
        <p className="text-sm text-slate-500">No trend data</p>
      ) : (
        <>
          <div className="flex items-end justify-between gap-3">
            <div>
              <p className="text-2xl font-bold tabular-nums text-slate-900">
                {formatNumber(last.total)} kg
              </p>
              <p className="text-xs text-slate-500">Latest month total</p>
            </div>
            <svg viewBox={`0 0 ${W} ${H}`} className="h-20 w-60">
              <polyline
                points={path}
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                className="text-emerald-600"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-600">
            <div className="rounded-lg bg-slate-50 px-2 py-2">
              <span className="font-semibold text-slate-900">{formatNumber(Math.max(...vals))}</span>{" "}
              max
            </div>
            <div className="rounded-lg bg-slate-50 px-2 py-2">
              <span className="font-semibold text-slate-900">{formatNumber(Math.min(...vals))}</span>{" "}
              min
            </div>
          </div>
        </>
      )}
    </Card>
  );
}

function TargetsPanel({ title, targets }) {
  return (
    <Card title={title} subtitle="Progress vs baseline → target">
      {targets.length === 0 ? (
        <p className="text-sm text-slate-500">No targets configured</p>
      ) : (
        <div className="space-y-3">
          {targets.slice(0, 5).map((t) => (
            <div key={t.id} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="truncate font-medium text-slate-700">{t.name}</span>
                <Badge className="bg-emerald-100 text-emerald-800 ring-emerald-200">
                  {toNumber(t.progress_percent).toFixed(1)}%
                </Badge>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-100">
                <div
                  className="h-2 rounded-full bg-emerald-600"
                  style={{ width: `${pct(toNumber(t.progress_percent), 100)}%` }}
                />
              </div>
              <p className="text-xs text-slate-500">
                Baseline {t.baseline_year} → Target {t.target_year}
              </p>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function AnomaliesPanel({ title, anomalies }) {
  const badgeFor = (severity) => {
    if (severity === "high") return "bg-red-100 text-red-800 ring-red-200";
    if (severity === "medium") return "bg-amber-100 text-amber-800 ring-amber-200";
    return "bg-blue-100 text-blue-800 ring-blue-200";
  };

  return (
    <Card title={title} subtitle="Top issues to review">
      {anomalies.length === 0 ? (
        <p className="text-sm text-slate-500">No active anomalies</p>
      ) : (
        <ul className="space-y-2">
          {anomalies.map((a) => (
            <li key={a.id} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-slate-900">
                    {a.anomaly_type}
                  </p>
                  <p className="mt-1 line-clamp-2 text-xs text-slate-600">
                    {a.description}
                  </p>
                  <p className="mt-2 text-xs text-slate-500">
                    Record #{a.record_id} · {a.source_type} · {a.scope}
                  </p>
                </div>
                <Badge className={badgeFor(a.severity)}>{a.severity}</Badge>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function CompactTable({ title, subtitle, columns, rows, emptyText }) {
  return (
    <Card title={title} subtitle={subtitle}>
      {rows.length === 0 ? (
        <p className="text-sm text-slate-500">{emptyText}</p>
      ) : (
        <div className="overflow-auto">
          <table className="w-full min-w-[420px] text-left text-sm">
            <thead className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                {columns.map((c) => (
                  <th key={c} className="px-2 py-2">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((r, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  {r.map((cell, i) => (
                    <td key={i} className="px-2 py-2 text-slate-700">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
