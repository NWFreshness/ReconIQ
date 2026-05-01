"use client";

const STATUS_COLORS: Record<string, string> = {
  pending: "text-amber-400 bg-amber-400/10 border-amber-400/20",
  running: "text-cyan-400 bg-cyan-400/10 border-cyan-400/20 animate-pulse-glow",
  completed: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
  failed: "text-red-400 bg-red-400/10 border-red-400/20",
};

export function StatusBadge({ status }: { status: string }) {
  const classes = STATUS_COLORS[status] || STATUS_COLORS.pending;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${classes}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${status === "running" ? "animate-pulse bg-current" : "bg-current"}`} />
      {status}
    </span>
  );
}
