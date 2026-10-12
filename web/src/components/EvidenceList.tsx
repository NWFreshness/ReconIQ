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
    <details className="mt-5">
      <summary className="cursor-pointer text-xs text-muted hover:text-foreground">
        Evidence sources ({items.length})
      </summary>
      <div className="mt-3 border-t border-border">
        {items.map((item, index) => (
          <div key={`${item.url ?? "evidence"}-${item.selector_or_field ?? index}-${index}`} className="border-b border-border py-3">
            <p className="mb-1 text-xs text-muted">
              {item.source_type ?? "source"}, {item.selector_or_field ?? "field"}, confidence {item.confidence ?? "unknown"}
            </p>
            {item.page_title && <p className="mb-1 text-sm font-medium">{item.page_title}</p>}
            {item.url && (
              <a href={item.url} target="_blank" className="mb-1 inline-flex items-center gap-1 text-xs text-accent hover:underline break-all">
                <ExternalLink className="h-3 w-3 shrink-0" />
                {item.url}
              </a>
            )}
            {item.excerpt && <p className="text-sm leading-relaxed text-muted">“{item.excerpt}”</p>}
          </div>
        ))}
      </div>
    </details>
  );
}
