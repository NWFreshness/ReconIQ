"use client";

import { Search, TrendingUp, AlertTriangle, Zap, BarChart2 } from "lucide-react";

interface SEOKeywordsData {
  top_keywords?: string[];
  content_gaps?: string[];
  seo_weaknesses?: string[];
  quick_wins?: string[];
  estimated_traffic_tier?: string;
  local_seo_signals?: string;
  data_confidence?: string;
  data_limitations?: string[];
  [key: string]: unknown;
}

interface SEOKeywordsCardProps {
  data: SEOKeywordsData;
}

function ConfidenceBadge({ level }: { level?: string }) {
  if (!level) return null;
  const color =
    level === "high" ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/30"
    : level === "medium" ? "text-yellow-400 bg-yellow-400/10 border-yellow-400/30"
    : "text-red-400 bg-red-400/10 border-red-400/30";
  return (
    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${color}`}>
      {level.toUpperCase()} CONFIDENCE
    </span>
  );
}

function TagList({ items, accent = "accent" }: { items?: string[]; accent?: "accent" | "warning" | "success" }) {
  if (!items?.length) return null;
  const colors = {
    accent: "bg-accent/10 text-accent border-accent/20",
    warning: "bg-yellow-400/10 text-yellow-400 border-yellow-400/20",
    success: "bg-emerald-400/10 text-emerald-400 border-emerald-400/20",
  };
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item, i) => (
        <span key={i} className={`text-xs px-2 py-0.5 rounded-md border ${colors[accent]}`}>
          {item}
        </span>
      ))}
    </div>
  );
}

export function SEOKeywordsCard({ data }: SEOKeywordsCardProps) {
  return (
    <div className="bg-surface border border-border rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-border bg-background/50 flex items-center gap-2">
        <Search className="w-3.5 h-3.5 text-accent" />
        <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">SEO & Keywords</h3>
        <div className="ml-auto flex items-center gap-3">
          <ConfidenceBadge level={data.data_confidence} />
          {data.estimated_traffic_tier && (
            <span className="text-xs text-muted flex items-center gap-1">
              <BarChart2 className="w-3 h-3" />
              {data.estimated_traffic_tier}
            </span>
          )}
        </div>
      </div>

      <div className="p-5 space-y-5">
        {data.top_keywords?.length ? (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-3.5 h-3.5 text-accent" />
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted">Top Keywords</span>
            </div>
            <TagList items={data.top_keywords} />
          </div>
        ) : null}

        {data.quick_wins?.length ? (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-[10px] font-semibold uppercase tracking-wider text-emerald-400">Quick Wins</span>
            </div>
            <TagList items={data.quick_wins} accent="success" />
          </div>
        ) : null}

        {data.content_gaps?.length ? (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Search className="w-3.5 h-3.5 text-yellow-400" />
              <span className="text-[10px] font-semibold uppercase tracking-wider text-yellow-400">Content Gaps</span>
            </div>
            <TagList items={data.content_gaps} accent="warning" />
          </div>
        ) : null}

        {data.seo_weaknesses?.length ? (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
              <span className="text-[10px] font-semibold uppercase tracking-wider text-red-400">SEO Weaknesses</span>
            </div>
            <TagList items={data.seo_weaknesses} accent="warning" />
          </div>
        ) : null}

        {data.local_seo_signals ? (
          <div className="border-t border-border pt-4">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-muted mb-1.5">Local SEO Signals</div>
            <p className="text-xs text-muted">{data.local_seo_signals}</p>
          </div>
        ) : null}

        {data.data_limitations?.length ? (
          <div className="border-t border-border pt-4">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-muted mb-2">Data Limitations</div>
            <ul className="space-y-1">
              {data.data_limitations.map((lim, i) => (
                <li key={i} className="text-xs text-muted flex items-start gap-2">
                  <span className="text-red-400 flex-shrink-0">—</span>
                  <span>{lim}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </div>
  );
}