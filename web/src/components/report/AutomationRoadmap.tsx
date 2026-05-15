"use client";

interface RoadmapItem {
  phase: string;
  title: string;
  priority: "high" | "medium" | "low";
}

const priorityColors: Record<string, string> = {
  high: "#ef4444",
  medium: "#f59e0b",
  low: "#10b981",
};

export function AutomationRoadmap({ items }: { items: RoadmapItem[] }) {
  if (!items || items.length === 0) return null;

  return (
    <div>
      <h4 className="text-xs font-semibold text-foreground mb-4">Recommended Automation Roadmap</h4>
      <div className="space-y-0">
        {items.map((item, i) => {
          const color = priorityColors[item.priority] || "#94a3b8";
          return (
            <div key={i} className="flex items-start gap-4">
              {/* Timeline */}
              <div className="flex flex-col items-center flex-shrink-0 w-8">
                <div
                  className="w-3 h-3 rounded-full border-2 border-surface flex-shrink-0"
                  style={{ backgroundColor: color }}
                />
                {i < items.length - 1 && (
                  <div className="w-px h-8 bg-border mt-1" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 pb-4">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color }}>
                      {item.phase}
                    </span>
                    <h5 className="text-sm font-medium text-foreground">{item.title}</h5>
                  </div>
                  <span
                    className="text-[9px] font-bold px-2 py-0.5 rounded-md"
                    style={{ backgroundColor: `${color}15`, color }}
                  >
                    {item.priority.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
