import { ExternalLink } from "lucide-react";

interface CompetitorRow {
  name: string;
  url: string;
  pricing_tier: string;
  positioning: string;
  key_messaging: string;
  services: string[];
  weaknesses: string[];
  content_quality: string;
  seo_notes: string;
}

interface CompetitorMatrixModel {
  rows: CompetitorRow[];
}

const DASH = "—";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function text(value: unknown): string {
  if (value === null || value === undefined) return DASH;
  const rendered = String(value).trim();
  return rendered || DASH;
}

function list(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean);
  }
  if (value === null || value === undefined || value === "") {
    return [];
  }
  return [String(value).trim()].filter(Boolean);
}

export function getCompetitorMatrix(value: unknown): CompetitorMatrixModel {
  if (!isRecord(value) || !Array.isArray(value.competitors)) {
    return { rows: [] };
  }

  return {
    rows: value.competitors.filter(isRecord).map((competitor) => ({
      name: text(competitor.name ?? competitor.company_name ?? "Unknown Competitor"),
      url: text(competitor.url) === DASH ? "" : text(competitor.url),
      pricing_tier: text(competitor.pricing_tier ?? competitor.estimated_pricing_tier),
      positioning: text(competitor.positioning),
      key_messaging: text(competitor.key_messaging),
      services: list(competitor.services ?? competitor.inferred_services),
      weaknesses: list(competitor.weaknesses),
      content_quality: text(competitor.content_quality),
      seo_notes: text(competitor.seo_notes),
    })),
  };
}

export function CompetitorMatrix({ matrix }: { matrix: CompetitorMatrixModel }) {
  if (matrix.rows.length === 0) {
    return null;
  }

  return (
    <div className="mt-8">
      <div className="overflow-x-auto border-y border-border">
        <table className="min-w-[900px] w-full text-left text-xs">
          <thead className="bg-surface text-xs text-muted">
            <tr>
              <th className="px-3 py-2.5 font-medium">Competitor</th>
              <th className="px-3 py-2.5 font-medium">Pricing</th>
              <th className="px-3 py-2.5 font-medium">Positioning</th>
              <th className="px-3 py-2.5 font-medium">Messaging</th>
              <th className="px-3 py-2.5 font-medium">Services</th>
              <th className="px-3 py-2.5 font-medium">Weaknesses</th>
              <th className="px-3 py-2.5 font-medium">Content</th>
              <th className="px-3 py-2.5 font-medium">SEO</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {matrix.rows.map((row, index) => (
              <tr key={`${row.url || row.name}-${index}`} className="align-top text-muted">
                <td className="px-3 py-3 font-display text-base font-medium text-foreground whitespace-nowrap">
                  {row.url ? (
                    <a href={row.url} target="_blank" className="inline-flex items-center gap-1 text-accent hover:underline">
                      {row.name}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  ) : (
                    row.name
                  )}
                </td>
                <td className="px-3 py-3">{row.pricing_tier}</td>
                <td className="px-3 py-3 leading-relaxed">{row.positioning}</td>
                <td className="px-3 py-3 leading-relaxed">{row.key_messaging}</td>
                <td className="px-3 py-3">{row.services.length ? row.services.join(", ") : DASH}</td>
                <td className="px-3 py-3">{row.weaknesses.length ? row.weaknesses.join(", ") : DASH}</td>
                <td className="px-3 py-3 leading-relaxed">{row.content_quality}</td>
                <td className="px-3 py-3 leading-relaxed">{row.seo_notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
