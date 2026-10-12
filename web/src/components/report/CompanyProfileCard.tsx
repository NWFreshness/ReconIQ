"use client";

import { Section, ConfidenceBadge, TagList, Limitations } from "./Section";

interface CompanyProfileData {
  company_name?: string;
  what_they_do?: string;
  target_audience?: string;
  value_proposition?: string;
  brand_voice?: string | string[];
  primary_cta?: string;
  services_products?: string[];
  marketing_channels?: string[];
  location_city?: string;
  location_state?: string;
  location_zip?: string;
  service_area?: string[];
  data_confidence?: string;
  data_limitations?: string[];
  // raw LLM output may have unexpected fields
  [key: string]: unknown;
}

interface CompanyProfileCardProps {
  data: CompanyProfileData;
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <>
      <dt className="text-sm text-muted">{label}</dt>
      <dd className="text-sm leading-relaxed mb-3 sm:mb-0">{children}</dd>
    </>
  );
}

export function CompanyProfileCard({ data }: CompanyProfileCardProps) {
  const brandVoice = Array.isArray(data.brand_voice) ? data.brand_voice.join(", ") : (data.brand_voice || "");
  const location = [data.location_city, data.location_state].filter(Boolean).join(", ");
  const fields: [string, string | undefined][] = [
    ["What they do", data.what_they_do],
    ["Target audience", data.target_audience],
    ["Value proposition", data.value_proposition],
    ["Brand voice", brandVoice],
    ["Primary call to action", data.primary_cta],
    ["Location", location],
  ];
  const lists: [string, string[] | undefined][] = [
    ["Services and products", data.services_products],
    ["Marketing channels", data.marketing_channels],
    ["Service area", data.service_area],
  ];

  return (
    <Section
      title="Company Profile"
      aside={
        <>
          {data.company_name && <span className="font-medium text-foreground">{data.company_name}</span>}
          <ConfidenceBadge level={data.data_confidence} />
        </>
      }
    >
      <dl className="sm:grid sm:grid-cols-[11rem_minmax(0,1fr)] sm:gap-x-6 sm:gap-y-4 max-w-3xl mb-5">
        {fields.map(([label, value]) => value && <Row key={label} label={label}>{value}</Row>)}
        {lists.map(([label, items]) => items?.length ? <Row key={label} label={label}><TagList items={items} /></Row> : null)}
      </dl>
      <Limitations items={data.data_limitations} />
    </Section>
  );
}
