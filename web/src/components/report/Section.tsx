import { gradeTone } from "../GradeStamp";

export function Section({ title, aside, children }: { title: string; aside?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="border-t border-foreground pt-4 pb-12">
      <div className="flex flex-wrap items-baseline justify-between gap-3 mb-5">
        <h2 className="font-display text-2xl font-semibold">{title}</h2>
        {aside && <div className="flex items-center gap-3 text-xs text-muted">{aside}</div>}
      </div>
      {children}
    </section>
  );
}

const CONFIDENCE_GRADE: Record<string, string> = { high: "A", medium: "C" };

export function ConfidenceBadge({ level }: { level?: string }) {
  if (!level) return null;
  return (
    <span className={`text-xs font-medium ${gradeTone(CONFIDENCE_GRADE[level] ?? "F")}`}>
      {level.charAt(0).toUpperCase() + level.slice(1)} confidence
    </span>
  );
}

export function TagList({ items, tone = "" }: { items?: string[]; tone?: string }) {
  if (!items?.length) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item, i) => (
        <span key={i} className={`tag ${tone}`}>
          {item}
        </span>
      ))}
    </div>
  );
}

export function Limitations({ items }: { items?: string[] }) {
  if (!items?.length) return null;
  return (
    <div className="border-t border-border pt-4">
      <p className="sub-label">Data limitations</p>
      <ul className="list-disc pl-5 space-y-1 text-sm text-muted">
        {items.map((lim, i) => (
          <li key={i}>{lim}</li>
        ))}
      </ul>
    </div>
  );
}

export function RawData({ value }: { value: unknown }) {
  return (
    <details className="mt-5">
      <summary className="text-xs text-muted cursor-pointer hover:text-foreground">Show raw data</summary>
      <pre className="text-xs text-muted font-mono overflow-x-auto whitespace-pre-wrap mt-2">
        {JSON.stringify(value, null, 2)}
      </pre>
    </details>
  );
}
