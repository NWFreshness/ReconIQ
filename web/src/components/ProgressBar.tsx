"use client";

import { motion } from "framer-motion";

export function ProgressBar({ pct, msg }: { pct: number; msg?: string | null }) {
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-muted mb-1">
        <span>{msg || "Processing..."}</span>
        <span className="tabular-nums">{pct.toFixed(0)}%</span>
      </div>
      <div className="h-1 bg-border overflow-hidden">
        <motion.div
          className="h-full bg-accent"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ type: "spring", stiffness: 50, damping: 15 }}
        />
      </div>
    </div>
  );
}
