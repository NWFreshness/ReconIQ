const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "reconiq-dev-key-change-in-production";

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`${res.status}: ${err}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface AnalysisJob {
  id: string;
  target_url: string;
  status: "pending" | "running" | "completed" | "failed";
  modules: string[];
  provider: string | null;
  model: string | null;
  fmt: string;
  created_at: string;
  updated_at: string;
  progress_pct: number;
  progress_msg: string | null;
  report_path: string | null;
  error: string | null;
}

export interface AnalysisResult {
  id: string;
  target_url: string;
  status: string;
  results: Record<string, unknown> | null;
  report_path: string | null;
  error: string | null;
  created_at: string;
  completed_at: string | null;
}

export const api = {
  health: () => fetchJson<{ status: string; version: string; timestamp: string }>("/health"),
  listAnalyses: (
    limit = 50,
    params?: {
      status?: string;
      provider?: string;
      min_score?: number;
      error_only?: boolean;
    },
  ) => {
    const qs = new URLSearchParams({ limit: String(limit) });
    if (params?.status) qs.set("status", params.status);
    if (params?.provider) qs.set("provider", params.provider);
    if (params?.min_score !== undefined) qs.set("min_score", String(params.min_score));
    if (params?.error_only) qs.set("error_only", String(params.error_only));
    return fetchJson<AnalysisJob[]>(`/analyses?${qs.toString()}`);
  },
  getAnalysis: (id: string) => fetchJson<AnalysisJob>(`/analyses/${id}`),
  getResults: (id: string) => fetchJson<AnalysisResult>(`/analyses/${id}/results`),
  createAnalysis: (body: {
    target_url: string;
    modules?: string[];
    provider?: string;
    model?: string;
    fmt?: string;
    max_pages?: number;
    max_depth?: number;
  }) =>
    fetchJson<AnalysisJob>("/analyses", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  downloadReport: (id: string) =>
    fetch(`${API_BASE}/reports/${id}`, {
      headers: { "X-API-Key": API_KEY },
    }),
  deleteAnalysis: (id: string) =>
    fetchJson<void>(`/analyses/${id}`, { method: "DELETE" }),
};

// ── Prospect Lists ─────────────────────────────────────────────────────────

export interface ProspectList {
  id: string;
  name: string;
  description: string | null;
  analysis_count: number;
  created_at: string;
  updated_at: string;
}

export const prospectLists = {
  create: (name: string, description?: string) =>
    fetchJson<ProspectList>("/prospect-lists", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    }),
  list: () => fetchJson<ProspectList[]>("/prospect-lists"),
  get: (id: string) => fetchJson<ProspectList>(`/prospect-lists/${id}`),
  update: (id: string, name?: string, description?: string) =>
    fetchJson<ProspectList>(`/prospect-lists/${id}`, {
      method: "PUT",
      body: JSON.stringify({ name, description }),
    }),
  delete: (id: string) =>
    fetchJson<void>(`/prospect-lists/${id}`, { method: "DELETE" }),
  getAnalyses: (id: string) => fetchJson<AnalysisJob[]>(`/prospect-lists/${id}/analyses`),
  addAnalysis: (listId: string, analysisId: string) =>
    fetchJson<{ status: string }>(`/prospect-lists/${listId}/analyses`, {
      method: "POST",
      body: JSON.stringify({ analysis_id: analysisId }),
    }),
  removeAnalysis: (listId: string, analysisId: string) =>
    fetchJson<void>(`/prospect-lists/${listId}/analyses/${analysisId}`, { method: "DELETE" }),
};
