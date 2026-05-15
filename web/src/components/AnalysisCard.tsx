"use client";

import Link from "next/link";
import { Trash2, Target } from "lucide-react";
import { StatusBadge } from "./StatusBadge";
import { ProgressBar } from "./ProgressBar";
import type { AnalysisJob, AnalysisResult } from "@/lib/api";

function getScoreFromResults(job: AnalysisJob): { score: number; grade: string } | null {
  // Score is stored in the results, which are fetched separately.
  // For the card, we check if there's a score badge from the job metadata.
  // The score data comes from the results endpoint.
  return null;
}

function gradeColor(grade: string): string {
  if (grade.startsWith("A")) return "text-emerald-400 bg-emerald-400/10 border-emerald-400/30";
  if (grade.startsWith("B")) return "text-cyan-400 bg-cyan-400/10 border-cyan-400/30";
  if (grade.startsWith("C")) return "text-yellow-400 bg-yellow-400/10 border-yellow-400/30";
  if (grade === "D") return "text-orange-400 bg-orange-400/10 border-orange-400/30";
  return "text-red-400 bg-red-400/10 border-red-400/30";
}

export function AnalysisCard({ job, onDelete, score }: { job: AnalysisJob; onDelete?: (id: string) => void; score?: { overall: number; grade: string } }) {
  const isRunning = job.status === "running" || job.status === "pending";

  return (
    <div className="group relative bg-surface border border-border rounded-xl p-5 hover:border-amber-500/30 transition-all duration-300 hover:shadow-lg hover:shadow-amber-500/5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <StatusBadge status={job.status} />
            {score && (
              <span className={`text-xs font-bold px-2 py-0.5 rounded-md border ${gradeColor(score.grade)}`}>
                {score.grade} {score.overall.toFixed(0)}
              </span>
            )}
            <span className="text-xs text-muted font-mono">{job.id.slice(0, 8)}</span>
          </div>
          <h3 className="text-sm font-semibold text-foreground truncate">
            {job.target_url}
          </h3>
          <p className="text-xs text-muted mt-1">
            {new Date(job.created_at).toLocaleString()}
            {job.provider && ` · ${job.provider}`}
            {job.model && `/${job.model}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {job.report_path && (
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL}/reports/${job.id}`}
              className="text-xs px-3 py-1.5 rounded-lg bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20 transition-colors"
              target="_blank"
            >
              Download .{job.fmt}
            </a>
          )}
          <Link
            href={`/analysis/${job.id}`}
            className="text-xs px-3 py-1.5 rounded-lg bg-surface-hover text-foreground border border-border hover:border-cyan-500/30 transition-colors"
          >
            View
          </Link>
          {onDelete && (
            <button
              onClick={() => onDelete(job.id)}
              className="text-xs px-2 py-1.5 rounded-lg bg-red-400/5 text-red-400 border border-red-400/10 hover:bg-red-400/10 hover:border-red-400/30 transition-colors"
              title="Delete analysis"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {isRunning && job.progress_pct > 0 && (
        <div className="mt-4">
          <ProgressBar pct={job.progress_pct} msg={job.progress_msg} />
        </div>
      )}

      {job.error && (
        <div className="mt-3 text-xs text-red-400 bg-red-400/5 border border-red-400/10 rounded-lg p-3">
          {job.error}
        </div>
      )}
    </div>
  );
}
