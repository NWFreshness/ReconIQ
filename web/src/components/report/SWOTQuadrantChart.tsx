"use client";

interface SWOTData {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}

export function SWOTQuadrantChart({ data }: { data: SWOTData }) {
  if (!data || (!data.strengths?.length && !data.weaknesses?.length &&
      !data.opportunities?.length && !data.threats?.length)) {
    return null;
  }

  const quadrants = [
    { label: "Strengths", tone: "text-success", items: data.strengths || [] },
    { label: "Weaknesses", tone: "text-danger", items: data.weaknesses || [] },
    { label: "Opportunities", tone: "text-accent", items: data.opportunities || [] },
    { label: "Threats", tone: "text-warn", items: data.threats || [] },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 border-l border-t border-border">
      {quadrants.map((q) => (
        <div key={q.label} className="border-r border-b border-border bg-surface p-4">
          <h3 className={`font-display text-lg font-semibold mb-2 ${q.tone}`}>{q.label}</h3>
          {q.items.length === 0 ? (
            <p className="text-sm text-muted">No data</p>
          ) : (
            <ul className="list-disc pl-5 space-y-1.5 text-sm">
              {q.items.slice(0, 5).map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}
