"use client";

import { Globe, Users, Star, MessageSquare, ExternalLink, AlertTriangle } from "lucide-react";

interface SocialAccount {
  platform?: string;
  url?: string;
}

interface SocialContentData {
  platforms?: string[];
  verified_social_accounts?: SocialAccount[];
  inferred_platforms?: string[];
  content_quality?: string;
  content_frequency?: string;
  engagement_signals?: string;
  review_sites?: string[];
  blog_or_resources?: string;
  content_gaps?: string[];
  email_signals?: string;
  data_confidence?: string;
  data_limitations?: string[];
  [key: string]: unknown;
}

interface SocialContentCardProps {
  data: SocialContentData;
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

function SignalRow({ label, value }: { label: string; value?: string }) {
  if (!value) return null;
  return (
    <div className="flex gap-3">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-muted w-32 flex-shrink-0 mt-0.5">{label}</div>
      <div className="text-xs text-foreground">{value}</div>
    </div>
  );
}

export function SocialContentCard({ data }: SocialContentCardProps) {
  return (
    <div className="bg-surface border border-border rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-border bg-background/50 flex items-center gap-2">
        <Globe className="w-3.5 h-3.5 text-accent" />
        <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">Social & Content</h3>
        <div className="ml-auto">
          <ConfidenceBadge level={data.data_confidence} />
        </div>
      </div>

      <div className="p-5 space-y-5">
        {data.platforms?.length ? (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <MessageSquare className="w-3.5 h-3.5 text-accent" />
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted">Active Platforms</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {data.platforms.map((p, i) => (
                <span key={i} className="text-xs px-2 py-0.5 rounded-md bg-accent/10 text-accent border border-accent/20">
                  {p}
                </span>
              ))}
            </div>
          </div>
        ) : null}

        {data.verified_social_accounts?.length ? (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Users className="w-3.5 h-3.5 text-accent" />
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted">Verified Accounts</span>
            </div>
            <div className="space-y-1.5">
              {data.verified_social_accounts.map((acc, i) => (
                <a
                  key={i}
                  href={acc.url || "#"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-xs text-accent hover:underline"
                >
                  <span className="font-semibold">{acc.platform}</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              ))}
            </div>
          </div>
        ) : null}

        {data.inferred_platforms?.length ? (
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-muted mb-1.5">Inferred Platforms</div>
            <div className="flex flex-wrap gap-1.5">
              {data.inferred_platforms.map((p, i) => (
                <span key={i} className="text-xs px-2 py-0.5 rounded-md bg-muted/20 text-muted border border-muted/30">
                  {p}
                </span>
              ))}
            </div>
          </div>
        ) : null}

        {(data.content_quality || data.content_frequency || data.engagement_signals) && (
          <div className="border-t border-border pt-4 space-y-2">
            <SignalRow label="Content Quality" value={data.content_quality} />
            <SignalRow label="Frequency" value={data.content_frequency} />
            <SignalRow label="Engagement" value={data.engagement_signals} />
          </div>
        )}

        {data.review_sites?.length ? (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Star className="w-3.5 h-3.5 text-yellow-400" />
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted">Review Sites</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {data.review_sites.map((site, i) => (
                <span key={i} className="text-xs px-2 py-0.5 rounded-md bg-yellow-400/10 text-yellow-400 border border-yellow-400/20">
                  {site}
                </span>
              ))}
            </div>
          </div>
        ) : null}

        {data.blog_or_resources ? (
          <div className="border-t border-border pt-4">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-muted mb-1.5">Blog / Resources</div>
            <p className="text-xs text-muted">{data.blog_or_resources}</p>
          </div>
        ) : null}

        {data.content_gaps?.length ? (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-3.5 h-3.5 text-yellow-400" />
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted">Content Gaps</span>
            </div>
            <ul className="space-y-1">
              {data.content_gaps.map((gap, i) => (
                <li key={i} className="text-xs text-muted flex items-start gap-2">
                  <span className="text-yellow-400 flex-shrink-0">—</span>
                  <span>{gap}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {data.email_signals ? (
          <div className="border-t border-border pt-4">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-muted mb-1.5">Email Signals</div>
            <p className="text-xs text-muted">{data.email_signals}</p>
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