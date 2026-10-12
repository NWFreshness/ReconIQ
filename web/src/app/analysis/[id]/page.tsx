"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Download } from "lucide-react";
import { api, type AnalysisJob, type AnalysisResult } from "@/lib/api";
import { MODULE_LABELS } from "@/lib/modules";
import { StatusBadge } from "@/components/StatusBadge";
import { ProgressBar } from "@/components/ProgressBar";
import { GradeStamp } from "@/components/GradeStamp";
import { CompetitorMatrix, getCompetitorMatrix } from "@/components/CompetitorMatrix";
import { EvidenceList, getEvidenceItems } from "@/components/EvidenceList";
import { OutreachBlock } from "@/components/OutreachBlock";
import {
  SWOTQuadrantChart,
  CompetitorRadarChart,
  CompanyProfileCard,
  SEOKeywordsCard,
  SocialContentCard,
} from "@/components/report";
import { Section, RawData } from "@/components/report/Section";

const SCORE_DIMENSIONS: [string, string][] = [
  ["Marketing gap", "marketing_gap_severity"],
  ["AI fit", "ai_automation_fit"],
  ["Local relevance", "local_relevance"],
  ["Likely budget", "likely_budget"],
  ["Outreach ease", "outreach_ease"],
  ["Urgency", "urgency_signals"],
  ["Data confidence", "data_confidence"],
];

function moduleTitle(key: string): string {
  const fallback = key.replace(/_/g, " ");
  return (MODULE_LABELS as Record<string, string>)[key] ?? fallback.charAt(0).toUpperCase() + fallback.slice(1);
}

function competitorSeries(comp: Record<string, unknown>) {
  const textValues: Record<string, number> = { Premium: 90, "Mid-range": 60, Budget: 30, Enterprise: 90, SMB: 50, Consumer: 20, High: 90, Medium: 60, Low: 30 };
  const fields = ["pricing_tier", "positioning", "content_quality", "services", "seo_notes"];
  return ((comp.competitors as Record<string, unknown>[]) || []).map((c, ci) => ({
    name: (c.name as string) || `Competitor ${ci + 1}`,
    values: fields.map((field) => {
      const raw = c[field];
      if (typeof raw === "string") return textValues[raw] ?? 50;
      if (Array.isArray(raw)) return Math.min(raw.length * 20, 100);
      return 50;
    }),
  }));
}

function ModuleSection({ moduleKey, value }: { moduleKey: string; value: unknown }) {
  const v = (value ?? {}) as Record<string, unknown>;
  const evidence = <EvidenceList items={getEvidenceItems(value)} />;

  if (typeof value === "object" && value !== null && "error" in value) {
    return (
      <Section title={`${moduleTitle(moduleKey)} failed`}>
        <p className="notice-danger font-mono whitespace-pre-wrap">{String(v.error || "Unknown error")}</p>
      </Section>
    );
  }

  if (moduleKey === "company_profile") {
    return <CompanyProfileCard data={v as Parameters<typeof CompanyProfileCard>[0]["data"]} />;
  }

  if (moduleKey === "social_content") {
    return <SocialContentCard data={v as Parameters<typeof SocialContentCard>[0]["data"]} />;
  }

  if (moduleKey === "seo_keywords") {
    return (
      <div>
        <SEOKeywordsCard data={v as Parameters<typeof SEOKeywordsCard>[0]["data"]} />
        <div className="-mt-8 mb-12">
          {evidence}
          <RawData value={value} />
        </div>
      </div>
    );
  }

  if (moduleKey === "swot") {
    const sw = (v.swot || v) as Record<string, unknown>;
    return (
      <Section title={moduleTitle(moduleKey)}>
        <SWOTQuadrantChart data={{
          strengths: (sw.strengths as string[]) || [],
          weaknesses: (sw.weaknesses as string[]) || [],
          opportunities: (sw.opportunities as string[]) || [],
          threats: (sw.threats as string[]) || [],
        }} />
        <RawData value={value} />
      </Section>
    );
  }

  if (moduleKey === "competitor") {
    const comps = competitorSeries(v);
    return (
      <Section title={moduleTitle(moduleKey)}>
        {comps.length > 0 ? (
          <CompetitorRadarChart competitors={comps} />
        ) : (
          <p className="text-sm text-muted">No competitor data available</p>
        )}
        <CompetitorMatrix matrix={getCompetitorMatrix(value)} />
        {evidence}
        <RawData value={value} />
      </Section>
    );
  }

  if (moduleKey === "outreach") {
    return (
      <Section title={moduleTitle(moduleKey)}>
        <OutreachBlock data={v} />
      </Section>
    );
  }

  return (
    <Section title={moduleTitle(moduleKey)}>
      <pre className="text-xs text-muted font-mono overflow-x-auto whitespace-pre-wrap">
        {JSON.stringify(value, null, 2)}
      </pre>
    </Section>
  );
}

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

  const backLink = (
    <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-foreground">
      <ArrowLeft className="w-4 h-4" />
      All analyses
    </Link>
  );

  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
        {backLink}
        <p className="notice-danger mt-6">{error}</p>
      </div>
    );
  }

  if (!job) {
    return <p className="max-w-6xl mx-auto px-4 sm:px-6 py-10 text-sm text-muted">Loading analysis...</p>;
  }

  const isRunning = job.status === "running" || job.status === "pending";
  const data = results?.results ?? null;

  const ps = data?.prospect_score as Record<string, unknown> | undefined;
  const score =
    ps && !ps.error && typeof ps.overall === "number" && typeof ps.grade === "string"
      ? { overall: ps.overall, grade: ps.grade }
      : null;
  const modules = data
    ? Object.entries(data).filter(([key]) => key !== "metadata" && key !== "prospect_score")
    : [];
  const hasMetadata = data !== null && "metadata" in data;
  const index: [string, string][] = [
    ...(score ? [["prospect_score", moduleTitle("prospect_score")] as [string, string]] : []),
    ...modules.map(([key]) => [key, moduleTitle(key)] as [string, string]),
    ...(hasMetadata ? [["metadata", "Metadata"] as [string, string]] : []),
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
      {backLink}

      <header className="mt-6 mb-10 flex flex-wrap items-start justify-between gap-8">
        <div className="min-w-0 flex-1">
          <h1 className="font-display text-3xl sm:text-4xl font-semibold leading-tight break-words">{job.target_url}</h1>
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted">
            <StatusBadge status={job.status} />
            <span>Created {new Date(job.created_at).toLocaleString()}</span>
            {job.provider && (
              <span>
                {job.provider}
                {job.model && `/${job.model}`}
              </span>
            )}
            <span className="font-mono">{job.id.slice(0, 8)}</span>
            {job.report_path && (
              <a href={`${process.env.NEXT_PUBLIC_API_URL}/reports/${job.id}`} className="btn" target="_blank">
                <Download className="w-3 h-3" />
                Download .{job.fmt}
              </a>
            )}
          </div>
        </div>
        {score && (
          <div className="pr-3 pt-2">
            <GradeStamp grade={score.grade} score={score.overall} large />
          </div>
        )}
      </header>

      {isRunning && job.progress_pct > 0 && (
        <div className="border-y border-border py-5 mb-8">
          <ProgressBar pct={job.progress_pct} msg={job.progress_msg} />
        </div>
      )}

      {job.error && (
        <div className="notice-danger mb-8">
          <p className="text-sm font-semibold mb-1">Analysis failed</p>
          <p className="font-mono whitespace-pre-wrap">{job.error}</p>
        </div>
      )}

      {data && (
        <div className="lg:grid lg:grid-cols-[11rem_minmax(0,1fr)] lg:gap-12">
          <nav aria-label="Report sections" className="hidden lg:block lg:sticky lg:top-8 lg:self-start border-t border-foreground pt-4">
            <ul className="space-y-2 text-sm">
              {index.map(([key, title]) => (
                <li key={key}>
                  <a href={`#${key}`} className="text-muted hover:text-foreground hover:underline">
                    {title}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          <div>
            {score && ps && (
              <div id="prospect_score" className="scroll-mt-6">
                <Section title={moduleTitle("prospect_score")}>
                  {typeof ps.summary === "string" && (
                    <p className="text-base leading-relaxed max-w-3xl mb-6">{ps.summary}</p>
                  )}
                  <dl className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-5">
                    {SCORE_DIMENSIONS.map(([label, field]) =>
                      ps[field] !== undefined ? (
                        <div key={field} className="flex flex-col-reverse">
                          <dt className="text-xs text-muted">{label}</dt>
                          <dd className="font-display text-2xl font-semibold tabular-nums">{Number(ps[field]).toFixed(0)}</dd>
                        </div>
                      ) : null
                    )}
                  </dl>
                </Section>
              </div>
            )}

            {modules.map(([key, value]) => (
              <div key={key} id={key} className="scroll-mt-6">
                <ModuleSection moduleKey={key} value={value} />
              </div>
            ))}

            {hasMetadata && (
              <div id="metadata" className="scroll-mt-6">
                <Section title="Metadata">
                  <pre className="text-xs text-muted font-mono overflow-x-auto whitespace-pre-wrap">
                    {JSON.stringify(data.metadata, null, 2)}
                  </pre>
                </Section>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
