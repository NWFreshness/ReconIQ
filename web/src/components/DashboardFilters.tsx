"use client";

import { Filter, X } from "lucide-react";

export interface DashboardFilters {
  status: string;
  provider: string;
  min_score: number | null;
  error_only: boolean;
}

interface Props {
  filters: DashboardFilters;
  onChange: (filters: DashboardFilters) => void;
  jobCount: number;
  totalCount: number;
}

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "pending", label: "Pending" },
  { value: "running", label: "Running" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
];

const PROVIDER_OPTIONS = [
  { value: "", label: "All providers" },
  { value: "deepseek", label: "DeepSeek" },
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "groq", label: "Groq" },
  { value: "ollama", label: "Ollama" },
];

export function DashboardFiltersBar({ filters, onChange, jobCount, totalCount }: Props) {
  const hasActiveFilters =
    filters.status !== "" ||
    filters.provider !== "" ||
    filters.min_score !== null ||
    filters.error_only;

  const activeFilterCount = [
    filters.status,
    filters.provider,
    filters.min_score !== null ? "1" : null,
    filters.error_only ? "1" : null,
  ].filter(Boolean).length;

  return (
    <div className="mb-6">
      {/* Filter bar */}
      <div className="bg-surface border border-border rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-muted" />
            <span className="text-xs font-semibold text-foreground uppercase tracking-wider">Filters</span>
            {activeFilterCount > 0 && (
              <span className="px-1.5 py-0.5 text-[10px] font-bold bg-cyan-400/10 text-cyan-400 rounded-full">
                {activeFilterCount}
              </span>
            )}
          </div>
          {hasActiveFilters && (
            <button
              onClick={() =>
                onChange({
                  status: "",
                  provider: "",
                  min_score: null,
                  error_only: false,
                })
              }
              className="text-xs text-muted hover:text-red-400 transition-colors flex items-center gap-1"
            >
              <X className="w-3 h-3" />
              Clear all
            </button>
          )}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {/* Status */}
          <div>
            <label className="text-[10px] text-muted uppercase tracking-wider mb-1 block">Status</label>
            <select
              value={filters.status}
              onChange={(e) => onChange({ ...filters, status: e.target.value })}
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-xs text-foreground focus:outline-none focus:border-amber-500/50"
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Provider */}
          <div>
            <label className="text-[10px] text-muted uppercase tracking-wider mb-1 block">Provider</label>
            <select
              value={filters.provider}
              onChange={(e) => onChange({ ...filters, provider: e.target.value })}
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-xs text-foreground focus:outline-none focus:border-amber-500/50"
            >
              {PROVIDER_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Min Score */}
          <div>
            <label className="text-[10px] text-muted uppercase tracking-wider mb-1 block">Min Score</label>
            <select
              value={filters.min_score ?? ""}
              onChange={(e) =>
                onChange({
                  ...filters,
                  min_score: e.target.value ? Number(e.target.value) : null,
                })
              }
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-xs text-foreground focus:outline-none focus:border-amber-500/50"
            >
              <option value="">Any score</option>
              <option value="30">30+ (D)</option>
              <option value="50">50+ (C)</option>
              <option value="70">70+ (B)</option>
              <option value="85">85+ (A)</option>
            </select>
          </div>

          {/* Error only toggle */}
          <div>
            <label className="text-[10px] text-muted uppercase tracking-wider mb-1 block">Quick</label>
            <button
              type="button"
              onClick={() =>
                onChange({
                  ...filters,
                  error_only: !filters.error_only,
                })
              }
              className={`w-full px-3 py-2 border rounded-lg text-xs font-medium transition-all ${
                filters.error_only
                  ? "bg-red-400/10 text-red-400 border-red-400/30"
                  : "bg-background text-muted border-border hover:border-muted"
              }`}
            >
              Failed only
            </button>
          </div>
        </div>

        {/* Active filter badges */}
        {hasActiveFilters && (
          <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-border/50">
            {filters.status && (
              <span className="px-2 py-1 text-[10px] font-medium bg-cyan-400/10 text-cyan-400 rounded-md border border-cyan-400/20">
                Status: {filters.status}
              </span>
            )}
            {filters.provider && (
              <span className="px-2 py-1 text-[10px] font-medium bg-purple-400/10 text-purple-400 rounded-md border border-purple-400/20">
                Provider: {filters.provider}
              </span>
            )}
            {filters.min_score !== null && (
              <span className="px-2 py-1 text-[10px] font-medium bg-emerald-400/10 text-emerald-400 rounded-md border border-emerald-400/20">
                Min score: {filters.min_score}
              </span>
            )}
            {filters.error_only && (
              <span className="px-2 py-1 text-[10px] font-medium bg-red-400/10 text-red-400 rounded-md border border-red-400/20">
                Failed only
              </span>
            )}
            <span className="px-2 py-1 text-[10px] text-muted">
              {jobCount} of {totalCount} jobs
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
