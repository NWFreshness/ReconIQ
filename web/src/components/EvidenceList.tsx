import { ExternalLink } from "lucide-react";

interface EvidenceItem {
  module?: string;
  source_type?: string;
  url?: string;
  page_title?: string;
  selector_or_field?: string;
  excerpt?: string;
  confidence?: string;
}

interface EvidenceCarrier {
  evidence?: unknown;
}

function isEvidenceItem(value: unknown): value is EvidenceItem {
  return typeof value === "object" && value !== null;
}

export function getEvidenceItems(value: unknown): EvidenceItem[] {
  if (!isEvidenceItem(value)) {
    return [];
  }
  const candidate = value as EvidenceCarrier;
  if (!Array.isArray(candidate.evidence)) {
    return [];
  }
  return candidate.evidence.filter(isEvidenceItem);
}

export function EvidenceList({ items }: { items: EvidenceItem[] }) {
  if (items.length === 0) {
    return null;
  }

  return (
    <details className="mt-4 rounded-lg border border-cyan-400/10 bg-cyan-400/[0.03] p-3">
      <summary className="cursor-pointer text-[10px] font-semibold uppercase tracking-wider text-cyan-300">
        Evidence Sources ({items.length})
      </summary>
      <div className="mt-3 space-y-3">
        {items.map((item, index) => (
          <div key={`${item.url ?? "evidence"}-${item.selector_or_field ?? index}-${index}`} className="rounded-md border border-border bg-background/60 p-3">
            <div className="mb-2 flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-wider text-muted">
              <span>{item.source_type ?? "source"}</span>
              <span>·</span>
              <span>{item.selector_or_field ?? "field"}</span>
              <span>·</span>
              <span>confidence: {item.confidence ?? "unknown"}</span>
            </div>
            {item.page_title && <p className="mb-1 text-xs font-semibold text-foreground">{item.page_title}</p>}
            {item.url && (
              <a href={item.url} target="_blank" className="mb-2 flex items-center gap-1 text-xs text-accent hover:underline">
                <ExternalLink className="h-3 w-3" />
                {item.url}
              </a>
            )}
            {item.excerpt && <p className="text-xs leading-relaxed text-muted">“{item.excerpt}”</p>}
          </div>
        ))}
      </div>
    </details>
  );
}
