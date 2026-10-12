"use client";

import { gradeTone } from "../GradeStamp";

interface ScoreDimension {
  label: string;
  value: number;
  key: string;
}

interface ScoreData {
  overall: number;
  grade: string;
  dimensions?: ScoreDimension[];
}

export function ProspectScoreDonut({ data }: { data: ScoreData }) {
  if (!data.overall && !data.grade) return null;

  const pct = Math.min(Math.max(data.overall, 0), 100) / 100;
  const r = 60;
  const circumference = 2 * Math.PI * r;
  const dashLen = circumference * pct;
  const gap = circumference - dashLen;

  return (
    <div className="flex flex-col md:flex-row items-center gap-6">
      {/* Donut */}
      <div className={`relative w-40 h-40 flex-shrink-0 ${gradeTone(data.grade)}`}>
        <svg viewBox="0 0 160 160" className="w-full h-full">
          <circle cx="80" cy="80" r={r} fill="none" className="stroke-border" strokeWidth="14" />
          {dashLen > 0 && (
            <circle
              cx="80" cy="80" r={r} fill="none"
              stroke="currentColor" strokeWidth="14"
              strokeDasharray={`${dashLen.toFixed(1)} ${gap.toFixed(1)}`}
              strokeLinecap="round"
              transform="rotate(-90 80 80)"
              className="transition-all duration-700"
            />
          )}
          <text x="80" y="74" textAnchor="middle" fill="currentColor" fontSize="28" fontWeight="bold">
            {data.overall.toFixed(0)}
          </text>
          <text x="80" y="96" textAnchor="middle" className="fill-muted" fontSize="14">
            {data.grade}
          </text>
        </svg>
      </div>

      {/* Dimensions */}
      {data.dimensions && data.dimensions.length > 0 && (
        <div className="grid grid-cols-2 gap-x-6 gap-y-2 flex-1">
          {data.dimensions.map((dim) => (
            <div key={dim.key} className="flex items-center justify-between">
              <span className="text-xs text-muted">{dim.label}</span>
              <span className="text-xs tabular-nums text-foreground">{dim.value.toFixed(0)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
