"use client";

import Link from "next/link";
import { Trash2 } from "lucide-react";
import { StatusBadge } from "./StatusBadge";
import { ProgressBar } from "./ProgressBar";
import { ListManager } from "./ListManager";
import { GradeStamp } from "./GradeStamp";
import type { AnalysisJob } from "@/lib/api";

export function AnalysisCard({ job, onDelete, deleteLabel = "Delete analysis", score, listIds, onListsChange }: { job: AnalysisJob; onDelete?: (id: string) => void; deleteLabel?: string; score?: { overall: number; grade: string }; listIds?: string[]; onListsChange?: (listIds: string[]) => void }) {
  const isRunning = job.status === "running" || job.status === "pending";

  return (
    <div className="border-b border-border py-4">
      <div className="flex flex-wrap items-start gap-x-4 gap-y-3">
        <div className="w-11 shrink-0">
          {score && <GradeStamp grade={score.grade} score={score.overall} />}
        </div>
        <div className="flex-1 min-w-[12rem]">
          <Link
            href={`/analysis/${job.id}`}
            className="block truncate font-display text-lg font-medium leading-snug hover:text-accent hover:underline"
          >
            {job.target_url}
          </Link>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
            <StatusBadge status={job.status} />
            <span>{new Date(job.created_at).toLocaleString()}</span>
            {job.provider && (
              <span>
                {job.provider}
                {job.model && `/${job.model}`}
              </span>
            )}
            <span className="font-mono">{job.id.slice(0, 8)}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {job.report_path && (
            <a href={`${process.env.NEXT_PUBLIC_API_URL}/reports/${job.id}`} className="btn" target="_blank">
              Download .{job.fmt}
            </a>
          )}
          {job.status === "completed" && onListsChange && (
            <ListManager
              analysisId={job.id}
              currentListIds={listIds || []}
              onListsChange={onListsChange}
            />
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(job.id)}
              className="btn btn-danger px-2"
              title={deleteLabel}
              aria-label={deleteLabel}
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {isRunning && job.progress_pct > 0 && (
        <div className="mt-4 sm:ml-15">
          <ProgressBar pct={job.progress_pct} msg={job.progress_msg} />
        </div>
      )}

      {job.error && <div className="mt-3 sm:ml-15 notice-danger">{job.error}</div>}
    </div>
  );
}
