"use client";

interface SWOTData {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}

const quadrantColors = {
  strengths: "#10b981",
  weaknesses: "#ef4444",
  opportunities: "#3b82f6",
  threats: "#f59e0b",
};

export function SWOTQuadrantChart({ data }: { data: SWOTData }) {
  if (!data || (!data.strengths?.length && !data.weaknesses?.length &&
      !data.opportunities?.length && !data.threats?.length)) {
    return null;
  }

  const quadrants = [
    { label: "Strengths", color: quadrantColors.strengths, items: data.strengths || [] },
    { label: "Weaknesses", color: quadrantColors.weaknesses, items: data.weaknesses || [] },
    { label: "Opportunities", color: quadrantColors.opportunities, items: data.opportunities || [] },
    { label: "Threats", color: quadrantColors.threats, items: data.threats || [] },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {quadrants.map((q) => (
        <div
          key={q.label}
          className="rounded-xl border overflow-hidden"
          style={{ borderColor: `${q.color}30` }}
        >
          <div
            className="px-4 py-2 flex items-center gap-2"
            style={{ backgroundColor: `${q.color}15` }}
          >
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: q.color }} />
            <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: q.color }}>
              {q.label}
            </span>
          </div>
          <div className="p-3 bg-surface">
            {q.items.length === 0 ? (
              <p className="text-xs text-muted italic">No data</p>
            ) : (
              <ul className="space-y-1.5">
                {q.items.slice(0, 5).map((item, i) => (
                  <li key={i} className="text-xs text-muted flex items-start gap-2">
                    <span className="mt-1 w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: q.color }} />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
