"use client";

import { useState, useEffect, useCallback } from "react";
import { RefreshCw } from "lucide-react";
import { api, type AnalysisJob, prospectLists } from "@/lib/api";
import { AnalysisCard } from "@/components/AnalysisCard";
import { StatStrip } from "@/components/StatStrip";
import { MODULE_LABELS } from "@/lib/modules";
import {
  DashboardFiltersBar,
  type DashboardFilters,
} from "@/components/DashboardFilters";

type ModuleKey = keyof typeof MODULE_LABELS;
type EnabledModules = Record<ModuleKey, boolean>;

const DEFAULT_MODULES: EnabledModules = {
  company_profile: true,
  seo_keywords: true,
  competitor: true,
  social_content: true,
  swot: true,
  outreach: true,
  prospect_score: true,
};

const MODULE_ENTRIES = Object.entries(MODULE_LABELS) as [ModuleKey, string][];

function normalizeUrl(url: string): string {
  url = url.trim();
  if (!url) return url;
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    url = "https://" + url;
  }
  return url;
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [provider, setProvider] = useState("deepseek");
  const [model, setModel] = useState("");
  const [fmt, setFmt] = useState("md");
  const [modules, setModules] = useState<EnabledModules>(DEFAULT_MODULES);
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [allJobs, setAllJobs] = useState<AnalysisJob[]>([]);
  const [scores, setScores] = useState<Record<string, { overall: number; grade: string }>>({});
  const [analysisLists, setAnalysisLists] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState<DashboardFilters>({
    status: "",
    provider: "",
    min_score: null,
    error_only: false,
  });

  const runningJobs = jobs.filter((job) => job.status === "running").length;
  const completedJobs = jobs.filter((job) => job.status === "completed").length;
  const failedJobs = jobs.filter((job) => job.status === "failed").length;

  const loadJobs = useCallback(async () => {
    try {
      // Load all jobs (with backend filters applied)
      const data = await api.listAnalyses(50, {
        status: filters.status || undefined,
        provider: filters.provider || undefined,
        min_score: filters.min_score ?? undefined,
        error_only: filters.error_only || undefined,
      });
      setJobs(data);
      setAllJobs(data);
      // Fetch scores for completed jobs
      const newScores: Record<string, { overall: number; grade: string }> = {};
      for (const job of data) {
        if (job.status === "completed") {
          try {
            const results = await api.getResults(job.id);
            const ps = results.results?.prospect_score as Record<string, unknown> | undefined;
            if (ps && typeof ps.overall === "number" && typeof ps.grade === "string") {
              newScores[job.id] = { overall: ps.overall, grade: ps.grade };
            }
          } catch {
            // skip if results not available
          }
        }
      }
      setScores(newScores);
      // Fetch list assignments for completed jobs
      const newListAssignments: Record<string, string[]> = {};
      for (const job of data) {
        if (job.status === "completed") {
          try {
            const lists = await prospectLists.list();
            const jobLists: string[] = [];
            for (const list of lists) {
              const analyses = await prospectLists.getAnalyses(list.id);
              if (analyses.some((a) => a.id === job.id)) {
                jobLists.push(list.id);
              }
            }
            if (jobLists.length > 0) {
              newListAssignments[job.id] = jobLists;
            }
          } catch {
            // skip if lists not available
          }
        }
      }
      setAnalysisLists(newListAssignments);
    } catch {
      // silently fail on polling
    }
  }, [filters]);

  useEffect(() => {
    const initialLoad = setTimeout(() => {
      void loadJobs();
    }, 0);
    const interval = setInterval(() => {
      void loadJobs();
    }, 3000);
    return () => {
      clearTimeout(initialLoad);
      clearInterval(interval);
    };
  }, [loadJobs]);

  const toggleModule = (key: ModuleKey) => {
    setModules((current) => ({ ...current, [key]: !current[key] }));
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this analysis?")) return;
    try {
      await api.deleteAnalysis(id);
      await loadJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
    }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const normalized = normalizeUrl(url);
    if (!normalized.trim()) return;
    setLoading(true);
    setError("");
    try {
      const enabled = Object.entries(modules)
        .filter(([, v]) => v)
        .map(([k]) => k);
      await api.createAnalysis({
        target_url: normalized,
        modules: enabled,
        provider,
        model: model || undefined,
        fmt,
      });
      setUrl("");
      await loadJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start analysis");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10 lg:grid lg:grid-cols-[20rem_minmax(0,1fr)] lg:gap-12">
      <aside className="mb-12 lg:mb-0 lg:sticky lg:top-8 lg:self-start">
        <h1 className="font-display text-4xl font-semibold leading-tight mb-3">Research a competitor</h1>
        <p className="text-sm text-muted leading-relaxed mb-6">
          Enter a company URL. ReconIQ profiles the company, finds its competitors, checks SEO and
          social signals, then writes a SWOT and strategy report.
        </p>

        <form onSubmit={submit} className="space-y-4">
          <label className="block">
            <span className="field-label">Company URL</span>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="example.com"
              className="field"
              required
            />
          </label>

          <details className="border-y border-border py-3">
            <summary className="text-sm font-medium cursor-pointer">Options</summary>
            <div className="mt-4 space-y-4">
              <label className="block">
                <span className="field-label">Provider</span>
                <select value={provider} onChange={(e) => setProvider(e.target.value)} className="field">
                  <option value="deepseek">DeepSeek</option>
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="groq">Groq</option>
                  <option value="ollama">Ollama</option>
                </select>
              </label>
              <label className="block">
                <span className="field-label">Model override</span>
                <input
                  type="text"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="Default"
                  className="field"
                />
              </label>
              <label className="block">
                <span className="field-label">Report format</span>
                <select value={fmt} onChange={(e) => setFmt(e.target.value)} className="field">
                  <option value="md">Markdown</option>
                  <option value="html">HTML</option>
                  <option value="pdf">PDF</option>
                </select>
              </label>
              <div>
                <span className="field-label">Modules</span>
                <div className="flex flex-wrap gap-2">
                  {MODULE_ENTRIES.map(([key, label]) => (
                    <button
                      key={key}
                      type="button"
                      aria-pressed={modules[key]}
                      onClick={() => toggleModule(key)}
                      className={`btn ${modules[key] ? "bg-foreground text-surface border-foreground" : "text-muted"}`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </details>

          {error && <div className="notice-danger">{error}</div>}

          <button type="submit" disabled={loading} className="btn btn-primary w-full py-3 text-sm">
            {loading && <RefreshCw className="w-4 h-4 animate-spin" />}
            {loading ? "Starting..." : "Analyze"}
          </button>
        </form>
      </aside>

      <section>
        <StatStrip
          stats={[
            { label: "Total", value: jobs.length },
            { label: "Running", value: runningJobs },
            { label: "Completed", value: completedJobs },
            { label: "Failed", value: failedJobs },
          ]}
        />

        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display text-2xl font-semibold">Analyses</h2>
          <button onClick={loadJobs} className="btn">
            <RefreshCw className="w-3 h-3" />
            Refresh
          </button>
        </div>

        <DashboardFiltersBar
          filters={filters}
          onChange={(f) => setFilters(f)}
          jobCount={jobs.length}
          totalCount={jobs.length}
        />

        {jobs.length === 0 ? (
          <p className="border-y border-border py-12 text-sm text-muted">
            No analyses to show. Enter a company URL to start one, or clear the filters.
          </p>
        ) : (
          <div className="border-t border-border">
            {jobs.map((job) => (
              <AnalysisCard
                key={job.id}
                job={job}
                onDelete={handleDelete}
                score={scores[job.id]}
                listIds={analysisLists[job.id]}
                onListsChange={(newListIds) =>
                  setAnalysisLists((prev) => ({ ...prev, [job.id]: newListIds }))
                }
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
