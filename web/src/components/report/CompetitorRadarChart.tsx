"use client";

interface CompetitorData {
  name: string;
  values: number[];
}

const SERIES = ["text-chart-1", "text-chart-2", "text-chart-3", "text-chart-4", "text-chart-5"];
const defaultAxes = ["Pricing", "Positioning", "Content", "Services", "SEO"];

export function CompetitorRadarChart({ competitors, axes = defaultAxes }: { competitors: CompetitorData[]; axes?: string[] }) {
  if (!competitors || competitors.length === 0) return null;

  const size = 300;
  const cx = size / 2;
  const cy = size / 2 + 10;
  const maxR = size / 2 - 50;
  const n = axes.length;
  const angleStep = (2 * Math.PI) / n;

  const polar = (angle: number, r: number) => ({
    x: cx + r * Math.cos(angle - Math.PI / 2),
    y: cy + r * Math.sin(angle - Math.PI / 2),
  });

  return (
    <div className="flex flex-col items-center">
      <svg viewBox={`0 0 ${size} ${size + 20}`} className="w-full max-w-sm" role="img" aria-label="Competitor comparison radar chart">
        {/* Grid rings */}
        {[0.25, 0.5, 0.75, 1.0].map((ringPct, ri) => {
          const r = maxR * ringPct;
          const pts = Array.from({ length: n }, (_, i) => polar(i * angleStep, r));
          return (
            <polygon
              key={ri}
              points={pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")}
              fill="none"
              className="stroke-border"
              strokeWidth="0.75"
            />
          );
        })}

        {/* Axis lines and labels */}
        {axes.map((axis, i) => {
          const angle = i * angleStep;
          const end = polar(angle, maxR);
          const label = polar(angle, maxR + 22);
          return (
            <g key={i}>
              <line x1={cx} y1={cy} x2={end.x.toFixed(1)} y2={end.y.toFixed(1)} className="stroke-border" strokeWidth="0.75" />
              <text x={label.x.toFixed(1)} y={label.y.toFixed(1)} textAnchor="middle" className="fill-muted" fontSize="10">
                {axis}
              </text>
            </g>
          );
        })}

        {/* Data series */}
        {competitors.map((comp, ci) => {
          const pts = comp.values.slice(0, n).map((v, i) => {
            const r = maxR * (Math.min(Math.max(v, 0), 100) / 100);
            return polar(i * angleStep, r);
          });
          return (
            <polygon
              key={ci}
              points={pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")}
              className={SERIES[ci % SERIES.length]}
              fill="currentColor"
              fillOpacity="0.1"
              stroke="currentColor"
              strokeWidth="2"
            />
          );
        })}
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-1.5 mt-2">
        {competitors.map((comp, ci) => (
          <div key={ci} className={`flex items-center gap-1.5 ${SERIES[ci % SERIES.length]}`}>
            <div className="w-2.5 h-2.5 bg-current" />
            <span className="text-xs text-foreground">{comp.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
