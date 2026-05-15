"use client";

import { useMemo } from "react";

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

const gradeColors: Record<string, string> = {
  "A+": "#10b981", A: "#10b981",
  "B+": "#06b6d4", B: "#06b6d4",
  "C+": "#eab308", C: "#eab308",
  D: "#f97316",
  F: "#ef4444",
};

function getGradeColor(grade: string): string {
  return gradeColors[grade] || "#94a3b8";
}

export function ProspectScoreDonut({ data }: { data: ScoreData }) {
  const color = useMemo(() => getGradeColor(data.grade), [data.grade]);

  if (!data.overall && !data.grade) return null;

  const pct = Math.min(Math.max(data.overall, 0), 100) / 100;
  const r = 60;
  const circumference = 2 * Math.PI * r;
  const dashLen = circumference * pct;
  const gap = circumference - dashLen;

  return (
    <div className="flex flex-col md:flex-row items-center gap-6">
      {/* Donut */}
      <div className="relative w-40 h-40 flex-shrink-0">
        <svg viewBox="0 0 160 160" className="w-full h-full">
          <circle cx="80" cy="80" r={r} fill="none" stroke="#334155" strokeWidth="14" />
          {dashLen > 0 && (
            <circle
              cx="80" cy="80" r={r} fill="none"
              stroke={color} strokeWidth="14"
              strokeDasharray={`${dashLen.toFixed(1)} ${gap.toFixed(1)}`}
              strokeLinecap="round"
              transform="rotate(-90 80 80)"
              className="transition-all duration-700"
            />
          )}
          <text x="80" y="74" textAnchor="middle" fill={color} fontSize="28" fontWeight="bold">
            {data.overall.toFixed(0)}
          </text>
          <text x="80" y="96" textAnchor="middle" fill="#94a3b8" fontSize="14">
            {data.grade}
          </text>
        </svg>
      </div>

      {/* Dimensions */}
      {data.dimensions && data.dimensions.length > 0 && (
        <div className="grid grid-cols-2 gap-x-6 gap-y-2 flex-1">
          {data.dimensions.map((dim) => (
            <div key={dim.key} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: getGradeColor(data.grade) }}
                />
                <span className="text-xs text-muted">{dim.label}</span>
              </div>
              <span className="text-xs font-mono text-foreground">{dim.value.toFixed(0)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
