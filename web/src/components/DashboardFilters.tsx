"use client";

import { X } from "lucide-react";

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

  return (
    <div className="flex flex-wrap items-end gap-3 mb-6">
      <label className="w-40">
        <span className="field-label">Status</span>
        <select
          value={filters.status}
          onChange={(e) => onChange({ ...filters, status: e.target.value })}
          className="field"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </label>

      <label className="w-40">
        <span className="field-label">Provider</span>
        <select
          value={filters.provider}
          onChange={(e) => onChange({ ...filters, provider: e.target.value })}
          className="field"
        >
          {PROVIDER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </label>

      <label className="w-40">
        <span className="field-label">Minimum score</span>
        <select
          value={filters.min_score ?? ""}
          onChange={(e) =>
            onChange({
              ...filters,
              min_score: e.target.value ? Number(e.target.value) : null,
            })
          }
          className="field"
        >
          <option value="">Any score</option>
          <option value="30">30+ (D)</option>
          <option value="50">50+ (C)</option>
          <option value="70">70+ (B)</option>
          <option value="85">85+ (A)</option>
        </select>
      </label>

      <button
        type="button"
        aria-pressed={filters.error_only}
        onClick={() => onChange({ ...filters, error_only: !filters.error_only })}
        className={`btn h-[38px] ${filters.error_only ? "border-danger text-danger" : ""}`}
      >
        Failed only
      </button>

      {hasActiveFilters && (
        <>
          <button
            type="button"
            onClick={() => onChange({ status: "", provider: "", min_score: null, error_only: false })}
            className="btn h-[38px]"
          >
            <X className="w-3 h-3" />
            Clear filters
          </button>
          <span className="text-xs text-muted pb-2.5">
            {jobCount} of {totalCount} analyses
          </span>
        </>
      )}
    </div>
  );
}
