"use client";

import { Section, ConfidenceBadge, TagList, Limitations } from "./Section";

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

export function SEOKeywordsCard({ data }: SEOKeywordsCardProps) {
  const groups: [string, string[] | undefined, string][] = [
    ["Top keywords", data.top_keywords, ""],
    ["Quick wins", data.quick_wins, "text-success"],
    ["Content gaps", data.content_gaps, "text-warn"],
    ["SEO weaknesses", data.seo_weaknesses, "text-danger"],
  ];

  return (
    <Section
      title="SEO & Keywords"
      aside={
        <>
          <ConfidenceBadge level={data.data_confidence} />
          {data.estimated_traffic_tier && <span>Traffic: {data.estimated_traffic_tier}</span>}
        </>
      }
    >
      <div className="space-y-5">
        {groups.map(([label, items, tone]) =>
          items?.length ? (
            <div key={label}>
              <p className="sub-label">{label}</p>
              <TagList items={items} tone={tone} />
            </div>
          ) : null
        )}

        {data.local_seo_signals ? (
          <div>
            <p className="sub-label">Local SEO signals</p>
            <p className="text-sm text-muted leading-relaxed max-w-3xl">{data.local_seo_signals}</p>
          </div>
        ) : null}

        <Limitations items={data.data_limitations} />
      </div>
    </Section>
  );
}
