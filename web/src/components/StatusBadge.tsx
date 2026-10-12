"use client";

const STATUS_TONE: Record<string, string> = {
  pending: "text-warn",
  running: "text-accent",
  completed: "text-success",
  failed: "text-danger",
};

export function StatusBadge({ status }: { status: string }) {
  const tone = STATUS_TONE[status] || STATUS_TONE.pending;
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium capitalize ${tone}`}>
      <span className={`w-1.5 h-1.5 rounded-full bg-current ${status === "running" ? "animate-pulse motion-reduce:animate-none" : ""}`} />
      {status}
    </span>
  );
}
