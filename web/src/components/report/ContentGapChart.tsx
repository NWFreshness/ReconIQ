"use client";

interface GapItem {
  label: string;
  value: number;
}

const barColors = ["#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#ec4899", "#14b8a6", "#6366f1"];

export function ContentGapChart({ items, title = "Content Gaps & SEO Weaknesses" }: { items: GapItem[]; title?: string }) {
  if (!items || items.length === 0) return null;

  const maxVal = Math.max(...items.map((i) => i.value), 1);

  return (
    <div>
      <h4 className="text-xs font-semibold text-foreground mb-3">{title}</h4>
      <div className="space-y-2">
        {items.slice(0, 8).map((item, i) => {
          const barWidth = (item.value / maxVal) * 100;
          const color = barColors[i % barColors.length];
          return (
            <div key={i} className="flex items-center gap-3">
              <span className="text-xs text-muted w-48 truncate flex-shrink-0" title={item.label}>
                {item.label}
              </span>
              <div className="flex-1 h-5 bg-surface-hover rounded-sm overflow-hidden">
                <div
                  className="h-full rounded-sm transition-all duration-500"
                  style={{ width: `${barWidth}%`, backgroundColor: color }}
                />
              </div>
              <span className="text-xs font-mono text-foreground w-8 text-right">
                {item.value.toFixed(0)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
