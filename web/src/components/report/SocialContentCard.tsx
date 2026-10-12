"use client";

import { ExternalLink } from "lucide-react";
import { Section, ConfidenceBadge, TagList, Limitations } from "./Section";

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

export function SocialContentCard({ data }: SocialContentCardProps) {
  const tagGroups: [string, string[] | undefined, string][] = [
    ["Active platforms", data.platforms, ""],
    ["Inferred platforms", data.inferred_platforms, "text-muted"],
    ["Review sites", data.review_sites, ""],
  ];
  const signals: [string, string | undefined][] = [
    ["Content quality", data.content_quality],
    ["Frequency", data.content_frequency],
    ["Engagement", data.engagement_signals],
    ["Blog and resources", data.blog_or_resources],
    ["Email signals", data.email_signals],
  ];

  return (
    <Section title="Social & Content" aside={<ConfidenceBadge level={data.data_confidence} />}>
      <div className="space-y-5">
        {tagGroups.map(([label, items, tone]) =>
          items?.length ? (
            <div key={label}>
              <p className="sub-label">{label}</p>
              <TagList items={items} tone={tone} />
            </div>
          ) : null
        )}

        {data.verified_social_accounts?.length ? (
          <div>
            <p className="sub-label">Verified accounts</p>
            <div className="flex flex-wrap gap-x-5 gap-y-1.5">
              {data.verified_social_accounts.map((acc, i) => (
                <a
                  key={i}
                  href={acc.url || "#"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm text-accent hover:underline"
                >
                  {acc.platform}
                  <ExternalLink className="w-3 h-3" />
                </a>
              ))}
            </div>
          </div>
        ) : null}

        {signals.some(([, value]) => value) && (
          <dl className="sm:grid sm:grid-cols-[11rem_minmax(0,1fr)] sm:gap-x-6 sm:gap-y-3 max-w-3xl">
            {signals.map(([label, value]) =>
              value ? (
                <div key={label} className="contents">
                  <dt className="text-sm text-muted">{label}</dt>
                  <dd className="text-sm leading-relaxed mb-3 sm:mb-0">{value}</dd>
                </div>
              ) : null
            )}
          </dl>
        )}

        {data.content_gaps?.length ? (
          <div>
            <p className="sub-label">Content gaps</p>
            <ul className="list-disc pl-5 space-y-1 text-sm text-muted">
              {data.content_gaps.map((gap, i) => (
                <li key={i}>{gap}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <Limitations items={data.data_limitations} />
      </div>
    </Section>
  );
}
