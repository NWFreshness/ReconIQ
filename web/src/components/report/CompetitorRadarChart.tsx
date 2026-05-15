"use client";

interface CompetitorData {
  name: string;
  values: number[];
  color: string;
}

const radarColors = ["#8b5cf6", "#06b6d4", "#f59e0b", "#10b981", "#ef4444"];
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
      <svg viewBox={`0 0 ${size} ${size + 20}`} className="w-full max-w-xs">
        {/* Grid rings */}
        {[0.25, 0.5, 0.75, 1.0].map((ringPct, ri) => {
          const r = maxR * ringPct;
          const pts = Array.from({ length: n }, (_, i) => polar(i * angleStep, r));
          return (
            <polygon
              key={ri}
              points={pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")}
              fill="none"
              stroke="#334155"
              strokeWidth="0.5"
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
              <line x1={cx} y1={cy} x2={end.x.toFixed(1)} y2={end.y.toFixed(1)} stroke="#334155" strokeWidth="0.5" />
              <text x={label.x.toFixed(1)} y={label.y.toFixed(1)} textAnchor="middle" fill="#94a3b8" fontSize="10">
                {axis}
              </text>
            </g>
          );
        })}

        {/* Data series */}
        {competitors.map((comp, ci) => {
          const color = comp.color || radarColors[ci % radarColors.length];
          const pts = comp.values.slice(0, n).map((v, i) => {
            const r = maxR * (Math.min(Math.max(v, 0), 100) / 100);
            return polar(i * angleStep, r);
          });
          return (
            <polygon
              key={ci}
              points={pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")}
              fill={color}
              fillOpacity="0.15"
              stroke={color}
              strokeWidth="2"
            />
          );
        })}
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mt-2">
        {competitors.map((comp, ci) => (
          <div key={ci} className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: comp.color || radarColors[ci % radarColors.length] }} />
            <span className="text-[10px] text-muted">{comp.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
