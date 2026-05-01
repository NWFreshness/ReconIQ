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
  listAnalyses: (limit = 50) => fetchJson<AnalysisJob[]>(`/analyses?limit=${limit}`),
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
};
