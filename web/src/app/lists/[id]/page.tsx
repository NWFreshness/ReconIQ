"use client";

import { useState, useEffect, use } from "react";
import Link from "next/link";
import { ArrowLeft, Trash2, Plus, FolderOpen, Terminal, Zap, Shield, List } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { StatusBadge } from "@/components/StatusBadge";
import { ListManager } from "@/components/ListManager";
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

  const handleListChange = (analysisId: string, newListIds: string[]) => {
    if (!newListIds.includes(id)) {
      setAnalyses((prev) => prev.filter((a) => a.id !== analysisId));
      setList((prev) =>
        prev ? { ...prev, analysis_count: Math.max(0, prev.analysis_count - 1) } : null
      );
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

  if (loading) {
    return (
      <div className="min-h-full flex items-center justify-center text-muted">
        Loading list...
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <Link href="/" className="text-accent hover:underline text-sm">
            ← Back to dashboard
          </Link>
        </div>
      </div>
    );
  }

  if (!list) return null;

  return (
    <div className="min-h-full grid-pattern">
      {/* Header */}
      <header className="border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="text-muted hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div className="w-8 h-8 rounded-lg bg-amber-400/10 border border-amber-400/20 flex items-center justify-center">
              <FolderOpen className="w-4 h-4 text-amber-400" />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-wider text-foreground">
                {list.name.toUpperCase()}
              </h1>
              <p className="text-[10px] text-muted">
                {list.analysis_count} analyses · {new Date(list.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10">
        {/* List Description */}
        {list.description && (
          <p className="text-muted text-sm mb-8">{list.description}</p>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          {[
            { icon: List, label: "Total", value: list.analysis_count },
            { icon: Terminal, label: "Completed", value: analyses.filter((a) => a.status === "completed").length },
            { icon: Zap, label: "Running", value: analyses.filter((a) => a.status === "running").length },
            { icon: Shield, label: "Avg Score", value: avgScore ? avgScore.toFixed(0) : "—" },
          ].map((stat) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4 }}
              className="bg-surface border border-border rounded-xl p-4"
            >
              <div className="flex items-center gap-2 mb-2">
                <stat.icon className="w-3.5 h-3.5 text-muted" />
                <span className="text-[10px] text-muted uppercase tracking-wider">
                  {stat.label}
                </span>
              </div>
              <p className="text-2xl font-bold text-foreground font-mono">{stat.value}</p>
            </motion.div>
          ))}
        </div>

        {/* Analyses List */}
        <div>
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
              Analyses in this list
            </h3>
            <span className="text-xs text-muted">
              {topScore !== null ? `Top score: ${topScore.toFixed(0)}` : ""}
            </span>
          </div>

          <AnimatePresence>
            {analyses.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-16 text-muted border border-dashed border-border rounded-xl"
              >
                <List className="w-8 h-8 mx-auto mb-3 opacity-30" />
                <p className="text-sm mb-3">No analyses in this list yet.</p>
                <Link
                  href="/"
                  className="text-xs text-accent hover:underline"
                >
                  Run an analysis and add it to this list
                </Link>
              </motion.div>
            ) : (
              <div className="space-y-3">
                {analyses.map((job) => (
                  <motion.div
                    key={job.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                  >
                    <div className="group relative bg-surface border border-border rounded-xl p-5 hover:border-amber-500/30 transition-all duration-300">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 mb-2">
                            <StatusBadge status={job.status} />
                            {scores[job.id] && (
                              <span className={`text-xs font-bold px-2 py-0.5 rounded-md border ${
                                scores[job.id].grade.startsWith("A")
                                  ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/30"
                                  : scores[job.id].grade.startsWith("B")
                                  ? "text-cyan-400 bg-cyan-400/10 border-cyan-400/30"
                                  : "text-yellow-400 bg-yellow-400/10 border-yellow-400/30"
                              }`}>
                                {scores[job.id].grade} {scores[job.id].overall.toFixed(0)}
                              </span>
                            )}
                          </div>
                          <Link href={`/analysis/${job.id}`} className="text-sm font-semibold text-foreground hover:text-accent transition-colors truncate block">
                            {job.target_url}
                          </Link>
                          <p className="text-xs text-muted mt-1">
                            {new Date(job.created_at).toLocaleString()}
                            {job.provider && ` · ${job.provider}`}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Link
                            href={`/analysis/${job.id}`}
                            className="text-xs px-3 py-1.5 rounded-lg bg-surface-hover text-foreground border border-border hover:border-cyan-500/30 transition-colors"
                          >
                            View
                          </Link>
                          <button
                            onClick={() => handleRemove(job.id)}
                            className="text-xs px-2 py-1.5 rounded-lg bg-red-400/5 text-red-400 border border-red-400/10 hover:bg-red-400/10 hover:border-red-400/30 transition-colors"
                            title="Remove from list"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
