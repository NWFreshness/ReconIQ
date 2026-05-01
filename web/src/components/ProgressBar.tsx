"use client";

import { motion } from "framer-motion";

export function ProgressBar({ pct, msg }: { pct: number; msg?: string | null }) {
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-muted mb-1">
        <span>{msg || "Processing..."}</span>
        <span className="font-mono">{pct.toFixed(0)}%</span>
      </div>
      <div className="h-1.5 bg-border rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-amber-500 to-cyan-500 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ type: "spring", stiffness: 50, damping: 15 }}
        />
      </div>
    </div>
  );
}
