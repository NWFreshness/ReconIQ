"use client";

interface GapItem {
  label: string;
  value: number;
}

export function ContentGapChart({ items, title = "Content Gaps & SEO Weaknesses" }: { items: GapItem[]; title?: string }) {
  if (!items || items.length === 0) return null;

  const maxVal = Math.max(...items.map((i) => i.value), 1);

  return (
    <div>
      <h4 className="text-xs font-semibold text-foreground mb-3">{title}</h4>
      <div className="space-y-2">
        {items.slice(0, 8).map((item, i) => {
          const barWidth = (item.value / maxVal) * 100;
          return (
            <div key={i} className="flex items-center gap-3">
              <span className="text-xs text-muted w-48 truncate flex-shrink-0" title={item.label}>
                {item.label}
              </span>
              <div className="flex-1 h-5 bg-surface-hover overflow-hidden">
                <div
                  className="h-full bg-accent transition-all duration-500"
                  style={{ width: `${barWidth}%` }}
                />
              </div>
              <span className="text-xs tabular-nums text-foreground w-8 text-right">
                {item.value.toFixed(0)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
