"use client";

import { useState, useEffect, use } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { AnalysisCard } from "@/components/AnalysisCard";
import { StatStrip } from "@/components/StatStrip";
import { prospectLists, api, type ProspectList, type AnalysisJob } from "@/lib/api";

export default function ListDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [list, setList] = useState<ProspectList | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisJob[]>([]);
  const [scores, setScores] = useState<Record<string, { overall: number; grade: string }>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadData = async () => {
      try {
        const [listData, analysesData] = await Promise.all([
          prospectLists.get(id),
          prospectLists.getAnalyses(id),
        ]);
        setList(listData);
        setAnalyses(analysesData);

        // Fetch scores
        const newScores: Record<string, { overall: number; grade: string }> = {};
        for (const job of analysesData) {
          try {
            const results = await api.getResults(job.id);
            const ps = results.results?.prospect_score as Record<string, unknown> | undefined;
            if (ps && typeof ps.overall === "number" && typeof ps.grade === "string") {
              newScores[job.id] = { overall: ps.overall, grade: ps.grade };
            }
          } catch {
            // skip
          }
        }
        setScores(newScores);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load list");
      } finally {
        setLoading(false);
      }
    };
    void loadData();
  }, [id]);

  const handleRemove = async (analysisId: string) => {
    try {
      await prospectLists.removeAnalysis(id, analysisId);
      setAnalyses((prev) => prev.filter((a) => a.id !== analysisId));
      setList((prev) =>
        prev ? { ...prev, analysis_count: Math.max(0, prev.analysis_count - 1) } : null
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove");
    }
  };

  const avgScore =
    Object.values(scores).length > 0
      ? Object.values(scores).reduce((sum, s) => sum + s.overall, 0) / Object.values(scores).length
      : null;

  const topScore =
    Object.values(scores).length > 0
      ? Math.max(...Object.values(scores).map((s) => s.overall))
      : null;

  const backLink = (
    <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-foreground">
      <ArrowLeft className="w-4 h-4" />
      All analyses
    </Link>
  );

  if (loading) {
    return <p className="max-w-7xl mx-auto px-4 sm:px-6 py-10 text-sm text-muted">Loading list...</p>;
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
        {backLink}
        <p className="notice-danger mt-6">{error}</p>
      </div>
    );
  }

  if (!list) return null;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
      {backLink}

      <header className="mt-6 mb-8">
        <h1 className="font-display text-4xl font-semibold leading-tight">{list.name}</h1>
        <p className="mt-2 text-xs text-muted">
          {list.analysis_count} analyses, created {new Date(list.created_at).toLocaleDateString()}
        </p>
        {list.description && <p className="mt-3 text-sm text-muted max-w-2xl">{list.description}</p>}
      </header>

      <StatStrip
        stats={[
          { label: "Total", value: list.analysis_count },
          { label: "Completed", value: analyses.filter((a) => a.status === "completed").length },
          { label: "Running", value: analyses.filter((a) => a.status === "running").length },
          { label: "Average score", value: avgScore ? avgScore.toFixed(0) : "—" },
        ]}
      />

      <div className="flex items-baseline justify-between mb-4">
        <h2 className="font-display text-2xl font-semibold">Analyses in this list</h2>
        <span className="text-xs text-muted">
          {topScore !== null ? `Top score: ${topScore.toFixed(0)}` : ""}
        </span>
      </div>

      {analyses.length === 0 ? (
        <p className="border-y border-border py-12 text-sm text-muted">
          No analyses in this list yet.{" "}
          <Link href="/" className="text-accent hover:underline">
            Run an analysis and add it to this list
          </Link>
        </p>
      ) : (
        <div className="border-t border-border">
          {analyses.map((job) => (
            <AnalysisCard
              key={job.id}
              job={job}
              score={scores[job.id]}
              onDelete={handleRemove}
              deleteLabel="Remove from list"
            />
          ))}
        </div>
      )}
    </div>
  );
}
