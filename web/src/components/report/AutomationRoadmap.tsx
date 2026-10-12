"use client";

interface RoadmapItem {
  phase: string;
  title: string;
  priority: "high" | "medium" | "low";
}

const priorityColors: Record<string, string> = {
  high: "text-danger",
  medium: "text-warn",
  low: "text-success",
};

export function AutomationRoadmap({ items }: { items: RoadmapItem[] }) {
  if (!items || items.length === 0) return null;

  return (
    <div>
      <h4 className="text-xs font-semibold text-foreground mb-4">Recommended Automation Roadmap</h4>
      <div className="space-y-0">
        {items.map((item, i) => {
          const tone = priorityColors[item.priority] || "text-muted";
          return (
            <div key={i} className={`flex items-start gap-4 ${tone}`}>
              {/* Timeline */}
              <div className="flex flex-col items-center flex-shrink-0 w-8">
                <div className="w-3 h-3 rounded-full bg-current flex-shrink-0" />
                {i < items.length - 1 && (
                  <div className="w-px h-8 bg-border mt-1" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 pb-4">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold">
                      {item.phase}
                    </span>
                    <h5 className="text-sm font-medium text-foreground">{item.title}</h5>
                  </div>
                  <span className="tag capitalize">{item.priority}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
