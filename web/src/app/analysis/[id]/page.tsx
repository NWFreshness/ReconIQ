"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, Download, FileText, AlertCircle, Target } from "lucide-react";
import { api, type AnalysisJob, type AnalysisResult } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { ProgressBar } from "@/components/ProgressBar";
import {
  SWOTQuadrantChart,
  ProspectScoreDonut,
  ContentGapChart,
  CompetitorRadarChart,
  AutomationRoadmap,
} from "@/components/report";

export default function AnalysisDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [results, setResults] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      try {
        const j = await api.getAnalysis(id);
        setJob(j);
        if (j.status === "completed" || j.status === "failed") {
          const r = await api.getResults(id);
          setResults(r);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      }
    };
    load();
    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, [id]);

  if (error) {
    return (
      <div className="min-h-full flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-3" />
          <p className="text-sm text-red-400">{error}</p>
          <Link href="/" className="text-xs text-accent mt-4 inline-block hover:underline">
            ← Back to dashboard
          </Link>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-full flex items-center justify-center">
        <div className="text-center text-muted">
          <div className="w-6 h-6 border-2 border-accent/20 border-t-accent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm">Loading analysis...</p>
        </div>
      </div>
    );
  }

  const isRunning = job.status === "running" || job.status === "pending";

  return (
    <div className="min-h-full grid-pattern">
      <header className="border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-muted hover:text-foreground transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <span className="text-xs text-muted font-mono">{job.id.slice(0, 8)}</span>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={job.status} />
            {job.report_path && (
              <a
                href={`${process.env.NEXT_PUBLIC_API_URL}/reports/${job.id}`}
                className="text-xs px-3 py-1.5 rounded-lg bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20 transition-colors flex items-center gap-1.5"
                target="_blank"
              >
                <Download className="w-3 h-3" />
                .{job.fmt}
              </a>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          <h1 className="text-xl font-bold text-foreground mb-1">{job.target_url}</h1>
          <p className="text-xs text-muted mb-6">
            Created {new Date(job.created_at).toLocaleString()}
            {job.provider && ` · ${job.provider}`}
            {job.model && `/${job.model}`}
          </p>

          {isRunning && job.progress_pct > 0 && (
            <div className="bg-surface border border-border rounded-xl p-5 mb-6">
              <ProgressBar pct={job.progress_pct} msg={job.progress_msg} />
            </div>
          )}

          {job.error && (
            <div className="bg-red-400/5 border border-red-400/10 rounded-xl p-5 mb-6">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="w-4 h-4 text-red-400" />
                <span className="text-sm font-semibold text-red-400">Analysis Failed</span>
              </div>
              <p className="text-xs text-red-300 font-mono whitespace-pre-wrap">{job.error}</p>
            </div>
          )}

          {results?.results && (
            <div className="space-y-4">
              {/* Prospect Score — special rendering */}
              {(() => {
                const ps = results.results.prospect_score as Record<string, unknown> | undefined;
                if (!ps || ps.error) return null;
                const overall = ps.overall as number | undefined;
                const grade = ps.grade as string | undefined;
                const summary = ps.summary as string | undefined;
                if (overall === undefined || !grade) return null;

                const gradeColor = grade.startsWith("A") ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/30"
                  : grade.startsWith("B") ? "text-cyan-400 bg-cyan-400/10 border-cyan-400/30"
                  : grade.startsWith("C") ? "text-yellow-400 bg-yellow-400/10 border-yellow-400/30"
                  : grade === "D" ? "text-orange-400 bg-orange-400/10 border-orange-400/30"
                  : "text-red-400 bg-red-400/10 border-red-400/30";

                const dimensions = [
                  ["Marketing Gap", ps.marketing_gap_severity as number | undefined],
                  ["AI Fit", ps.ai_automation_fit as number | undefined],
                  ["Local Relevance", ps.local_relevance as number | undefined],
                  ["Likely Budget", ps.likely_budget as number | undefined],
                  ["Outreach Ease", ps.outreach_ease as number | undefined],
                  ["Urgency", ps.urgency_signals as number | undefined],
                  ["Data Confidence", ps.data_confidence as number | undefined],
                ];

                return (
                  <div className="bg-surface border border-border rounded-xl overflow-hidden">
                    <div className="px-5 py-3 border-b border-border bg-background/50 flex items-center gap-2">
                      <Target className="w-3.5 h-3.5 text-accent" />
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">Prospect Score</h3>
                      <span className={`ml-auto text-sm font-bold px-2 py-0.5 rounded-md border ${gradeColor}`}>
                        {grade} {overall.toFixed(0)}
                      </span>
                    </div>
                    <div className="p-5">
                      {summary && <p className="text-xs text-muted mb-4 italic">{summary}</p>}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {dimensions.map(([label, val]) => val !== undefined && (
                          <div key={label} className="text-center">
                            <div className="text-lg font-bold text-foreground">{Number(val).toFixed(0)}</div>
                            <div className="text-[10px] text-muted uppercase tracking-wider">{label}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })()}

              {Object.entries(results.results).map(([key, value]) => {
                if (key === "metadata" || key === "prospect_score") return null;
                const hasError = typeof value === "object" && value !== null && "error" in value;
                if (hasError) {
                  return (
                    <div key={key} className="bg-red-400/5 border border-red-400/10 rounded-xl overflow-hidden">
                      <div className="px-5 py-3 border-b border-red-400/10 bg-red-400/5 flex items-center gap-2">
                        <AlertCircle className="w-3.5 h-3.5 text-red-400" />
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-red-400">
                          {key.replace(/_/g, " ")} — Failed
                        </h3>
                      </div>
                      <div className="p-5">
                        <p className="text-xs text-red-300 font-mono whitespace-pre-wrap">
                          {(value as Record<string, string>).error}
                        </p>
                      </div>
                    </div>
                  );
                }
                const v = value as Record<string, unknown> | undefined;

                // SWOT — visual quadrant
                if (key === "swot") {
                  const sw = (v?.swot || v || {}) as Record<string, unknown>;
                  return (
                    <div key={key} className="bg-surface border border-border rounded-xl overflow-hidden">
                      <div className="px-5 py-3 border-b border-border bg-background/50 flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-accent" />
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">SWOT Analysis</h3>
                      </div>
                      <div className="p-5">
                        <SWOTQuadrantChart data={{
                          strengths: (sw.strengths as string[]) || [],
                          weaknesses: (sw.weaknesses as string[]) || [],
                          opportunities: (sw.opportunities as string[]) || [],
                          threats: (sw.threats as string[]) || [],
                        }} />
                        {/* Fallback data below chart */}
                        <details className="mt-4">
                          <summary className="text-xs text-muted cursor-pointer hover:text-foreground">Show raw data</summary>
                          <pre className="text-xs text-muted font-mono overflow-x-auto whitespace-pre-wrap mt-2">
                            {JSON.stringify(value, null, 2)}
                          </pre>
                        </details>
                      </div>
                    </div>
                  );
                }

                // SEO — content gap chart
                if (key === "seo_keywords") {
                  const seo = v || {};
                  const gaps = ((seo.content_gaps as string[]) || []).map((g, i) => ({
                    label: g, value: Math.max(100 - i * 10 - 20, 10),
                  }));
                  const weaknesses = ((seo.seo_weaknesses as string[]) || []).map((w, i) => ({
                    label: w, value: Math.max(100 - i * 15 - 10, 10),
                  }));
                  return (
                    <div key={key} className="bg-surface border border-border rounded-xl overflow-hidden">
                      <div className="px-5 py-3 border-b border-border bg-background/50 flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-accent" />
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">SEO & Keywords</h3>
                      </div>
                      <div className="p-5">
                        <ContentGapChart items={[...gaps, ...weaknesses]} />
                        <details className="mt-4">
                          <summary className="text-xs text-muted cursor-pointer hover:text-foreground">Show raw data</summary>
                          <pre className="text-xs text-muted font-mono overflow-x-auto whitespace-pre-wrap mt-2">
                            {JSON.stringify(value, null, 2)}
                          </pre>
                        </details>
                      </div>
                    </div>
                  );
                }

                // Competitor — radar chart
                if (key === "competitor") {
                  const comp = v || {};
                  const comps = ((comp.competitors as Record<string, unknown>[]) || []).map((c: Record<string, unknown>, ci: number) => {
                    const fieldMap: Record<string, string> = {
                      pricing_tier: "pricing_tier", positioning: "positioning",
                      content_quality: "content_quality", services: "services", seo_notes: "seo_notes",
                    };
                    const textValues: Record<string, number> = { Premium: 90, "Mid-range": 60, Budget: 30, Enterprise: 90, SMB: 50, Consumer: 20, High: 90, Medium: 60, Low: 30 };
                    const axes = ["Pricing Tier", "Positioning", "Content Quality", "Services", "SEO"];
                    const values = axes.map((axis) => {
                      const fname = fieldMap[axis.toLowerCase().replace(/ /g, "_")] || "";
                      const raw = c[fname];
                      if (typeof raw === "string") return textValues[raw] ?? 50;
                      if (Array.isArray(raw)) return Math.min(raw.length * 20, 100);
                      return 50;
                    });
                    const radarColors = ["#8b5cf6", "#06b6d4", "#f59e0b", "#10b981", "#ef4444"];
                    return { name: (c.name as string) || `Competitor ${ci + 1}`, values, color: radarColors[ci % radarColors.length] };
                  });
                  return (
                    <div key={key} className="bg-surface border border-border rounded-xl overflow-hidden">
                      <div className="px-5 py-3 border-b border-border bg-background/50 flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-accent" />
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">Competitors</h3>
                      </div>
                      <div className="p-5">
                        {comps.length > 0 ? (
                          <CompetitorRadarChart competitors={comps} />
                        ) : (
                          <p className="text-xs text-muted italic">No competitor data available</p>
                        )}
                        <details className="mt-4">
                          <summary className="text-xs text-muted cursor-pointer hover:text-foreground">Show raw data</summary>
                          <pre className="text-xs text-muted font-mono overflow-x-auto whitespace-pre-wrap mt-2">
                            {JSON.stringify(value, null, 2)}
                          </pre>
                        </details>
                      </div>
                    </div>
                  );
                }

                // Outreach — formatted display
                if (key === "outreach") {
                  const o = v || {};
                  const fields = [
                    ["Cold Email", o.cold_email],
                    ["LinkedIn DM", o.linkedin_dm],
                    ["Discovery Call Opener", o.discovery_call_opener],
                    ["Proposal Outline", o.proposal_outline],
                  ].filter(([, val]) => val);
                  return (
                    <div key={key} className="bg-surface border border-border rounded-xl overflow-hidden">
                      <div className="px-5 py-3 border-b border-border bg-background/50 flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-accent" />
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">Outreach Pack</h3>
                      </div>
                      <div className="p-5 space-y-4">
                        {fields.map(([heading, val]) => (
                          <div key={heading as string}>
                            <h4 className="text-xs font-semibold text-foreground mb-1">{heading as string}</h4>
                            <p className="text-xs text-muted whitespace-pre-wrap">{String(val)}</p>
                          </div>
                        ))}
                        {Array.isArray(o.follow_up_sequence) && o.follow_up_sequence.length > 0 && (
                          <div>
                            <h4 className="text-xs font-semibold text-foreground mb-1">Follow-up Sequence</h4>
                            <ul className="space-y-1">
                              {(o.follow_up_sequence as string[]).map((step: string, i: number) => (
                                <li key={i} className="text-xs text-muted flex items-start gap-2">
                                  <span className="text-accent flex-shrink-0">{i + 1}.</span>
                                  <span>{step}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                }

                // Default — raw JSON with collapsible
                return (
                  <div key={key} className="bg-surface border border-border rounded-xl overflow-hidden">
                    <div className="px-5 py-3 border-b border-border bg-background/50 flex items-center gap-2">
                      <FileText className="w-3.5 h-3.5 text-accent" />
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">
                        {key.replace(/_/g, " ")}
                      </h3>
                    </div>
                    <div className="p-5">
                      <pre className="text-xs text-muted font-mono overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(value, null, 2)}
                      </pre>
                    </div>
                  </div>
                );
              })}

              {typeof results.results === "object" && results.results !== null && "metadata" in results.results && (
                <div className="bg-surface border border-border rounded-xl overflow-hidden">
                  <div className="px-5 py-3 border-b border-border bg-background/50">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">Metadata</h3>
                  </div>
                  <div className="p-5">
                    <pre className="text-xs text-muted font-mono overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify((results.results as Record<string, unknown>).metadata, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )}
        </motion.div>
      </main>
    </div>
  );
}
