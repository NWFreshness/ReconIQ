"use client";

import { Building2, MapPin, Target, Megaphone, Zap, List } from "lucide-react";

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

function Field({ label, value, icon: Icon }: { label: string; value?: string; icon?: React.ElementType }) {
  if (!value) return null;
  return (
    <div className="flex gap-3">
      {Icon && <Icon className="w-3.5 h-3.5 text-accent mt-0.5 flex-shrink-0" />}
      <div>
        <div className="text-[10px] font-semibold uppercase tracking-wider text-muted mb-0.5">{label}</div>
        <div className="text-sm text-foreground">{value}</div>
      </div>
    </div>
  );
}

function ListField({ label, items, icon: Icon }: { label: string; items?: string[]; icon?: React.ElementType }) {
  if (!items?.length) return null;
  return (
    <div className="flex gap-3">
      {Icon && <Icon className="w-3.5 h-3.5 text-accent mt-0.5 flex-shrink-0" />}
      <div>
        <div className="text-[10px] font-semibold uppercase tracking-wider text-muted mb-1.5">{label}</div>
        <div className="flex flex-wrap gap-1.5">
          {items.map((item, i) => (
            <span key={i} className="text-xs px-2 py-0.5 rounded-md bg-accent/10 text-accent border border-accent/20">
              {item}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
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

export function CompanyProfileCard({ data }: CompanyProfileCardProps) {
  const brandVoice = Array.isArray(data.brand_voice) ? data.brand_voice.join(", ") : (data.brand_voice || "");
  const location = [data.location_city, data.location_state].filter(Boolean).join(", ");

  return (
    <div className="bg-surface border border-border rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-border bg-background/50 flex items-center gap-2">
        <Building2 className="w-3.5 h-3.5 text-accent" />
        <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">Company Profile</h3>
        <div className="ml-auto flex items-center gap-2">
          <ConfidenceBadge level={data.data_confidence} />
          {data.company_name && (
            <span className="text-xs font-semibold text-foreground">{data.company_name}</span>
          )}
        </div>
      </div>

      <div className="p-5 space-y-5">
        <Field label="What They Do" value={data.what_they_do} icon={Zap} />
        <Field label="Target Audience" value={data.target_audience} icon={Target} />
        <Field label="Value Proposition" value={data.value_proposition} icon={Target} />
        <Field label="Brand Voice" value={brandVoice} icon={Building2} />
        <Field label="Primary CTA" value={data.primary_cta} icon={Zap} />

        <ListField label="Services & Products" items={data.services_products} icon={List} />
        <ListField label="Marketing Channels" items={data.marketing_channels} icon={Megaphone} />
        <ListField label="Service Area" items={data.service_area} icon={MapPin} />

        {location && (
          <div className="flex gap-3">
            <MapPin className="w-3.5 h-3.5 text-accent mt-0.5 flex-shrink-0" />
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-muted mb-0.5">Location</div>
              <div className="text-sm text-foreground">{location}</div>
            </div>
          </div>
        )}

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