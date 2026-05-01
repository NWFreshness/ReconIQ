"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Radar, Plus, RefreshCw, Terminal, Zap, Globe, Shield } from "lucide-react";
import { api, type AnalysisJob } from "@/lib/api";
import { AnalysisCard } from "@/components/AnalysisCard";

export default function Home() {
  const [url, setUrl] = useState("");
  const [provider, setProvider] = useState("deepseek");
  const [model, setModel] = useState("");
  const [fmt, setFmt] = useState("md");
  const [modules, setModules] = useState({
    company_profile: true,
    seo_keywords: true,
    competitor: true,
    social_content: true,
    swot: true,
  });
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadJobs = useCallback(async () => {
    try {
      const data = await api.listAnalyses(20);
      setJobs(data);
    } catch {
      // silently fail on polling
    }
  }, []);

  useEffect(() => {
    loadJobs();
    const interval = setInterval(loadJobs, 3000);
    return () => clearInterval(interval);
  }, [loadJobs]);

  const toggleModule = (key: string) => {
    setModules((m) => ({ ...m, [key]: !m[key as keyof typeof m] }));
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError("");
    try {
      const enabled = Object.entries(modules)
        .filter(([, v]) => v)
        .map(([k]) => k);
      await api.createAnalysis({
        target_url: url.trim(),
        modules: enabled,
        provider,
        model: model || undefined,
        fmt,
      });
      setUrl("");
      await loadJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start analysis");
    } finally {
      setLoading(false);
    }
  };

  const moduleLabels: Record<string, string> = {
    company_profile: "Company Profile",
    seo_keywords: "SEO & Keywords",
    competitor: "Competitors",
    social_content: "Social & Content",
    swot: "SWOT Analysis",
  };

  return (
    <div className="min-h-full grid-pattern">
      {/* Header */}
      <header className="border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center">
              <Radar className="w-4 h-4 text-accent" />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-wider text-foreground">RECONIQ</h1>
              <p className="text-[10px] text-muted uppercase tracking-widest">Marketing Intelligence</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs text-muted">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              API Online
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-12"
        >
          <h2 className="text-4xl font-bold text-foreground mb-3 tracking-tight">
            Competitive Intelligence
          </h2>
          <p className="text-muted max-w-xl text-sm leading-relaxed">
            Enter a company URL and ReconIQ will research the company, competitors,
            SEO signals, synthesize SWOT, and generate a strategy report — powered by AI.
          </p>
        </motion.div>

        {/* Input Form */}
        <motion.form
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          onSubmit={submit}
          className="bg-surface border border-border rounded-2xl p-6 mb-10"
        >
          <div className="flex gap-3 mb-5">
            <div className="flex-1 relative">
              <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com"
                className="w-full pl-10 pr-4 py-3 bg-background border border-border rounded-xl text-sm text-foreground placeholder:text-muted focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/20 transition-all"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 bg-accent text-background font-semibold text-sm rounded-xl hover:bg-amber-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              {loading ? "Starting..." : "Analyze"}
            </button>
          </div>

          {error && (
            <div className="mb-4 text-xs text-red-400 bg-red-400/5 border border-red-400/10 rounded-lg p-3">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-[10px] text-muted uppercase tracking-wider mb-1.5 block">Provider</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-amber-500/50"
              >
                <option value="deepseek">DeepSeek</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="groq">Groq</option>
                <option value="ollama">Ollama</option>
              </select>
            </div>
            <div>
              <label className="text-[10px] text-muted uppercase tracking-wider mb-1.5 block">Model Override</label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="Default"
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground placeholder:text-muted focus:outline-none focus:border-amber-500/50"
              />
            </div>
            <div>
              <label className="text-[10px] text-muted uppercase tracking-wider mb-1.5 block">Format</label>
              <select
                value={fmt}
                onChange={(e) => setFmt(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-amber-500/50"
              >
                <option value="md">Markdown</option>
                <option value="html">HTML</option>
                <option value="pdf">PDF</option>
              </select>
            </div>
          </div>

          <div className="mt-4">
            <label className="text-[10px] text-muted uppercase tracking-wider mb-2 block">Modules</label>
            <div className="flex flex-wrap gap-2">
              {Object.entries(moduleLabels).map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => toggleModule(key)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                    modules[key as keyof typeof modules]
                      ? "bg-cyan-400/10 text-cyan-400 border-cyan-400/30"
                      : "bg-background text-muted border-border hover:border-muted"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </motion.form>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          {[
            { icon: Terminal, label: "Total", value: jobs.length },
            { icon: Zap, label: "Running", value: jobs.filter((j) => j.status === "running").length },
            { icon: Shield, label: "Completed", value: jobs.filter((j) => j.status === "completed").length },
            { icon: Radar, label: "Failed", value: jobs.filter((j) => j.status === "failed").length },
          ].map((stat) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4 }}
              className="bg-surface border border-border rounded-xl p-4"
            >
              <div className="flex items-center gap-2 mb-2">
                <stat.icon className="w-3.5 h-3.5 text-muted" />
                <span className="text-[10px] text-muted uppercase tracking-wider">{stat.label}</span>
              </div>
              <p className="text-2xl font-bold text-foreground font-mono">{stat.value}</p>
            </motion.div>
          ))}
        </div>

        {/* Job List */}
        <div>
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">Recent Analyses</h3>
            <button
              onClick={loadJobs}
              className="text-xs text-muted hover:text-foreground transition-colors flex items-center gap-1"
            >
              <RefreshCw className="w-3 h-3" />
              Refresh
            </button>
          </div>

          <AnimatePresence>
            {jobs.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-16 text-muted border border-dashed border-border rounded-xl"
              >
                <Radar className="w-8 h-8 mx-auto mb-3 opacity-30" />
                <p className="text-sm">No analyses yet. Enter a URL above to begin.</p>
              </motion.div>
            ) : (
              <div className="space-y-3">
                {jobs.map((job) => (
                  <motion.div
                    key={job.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                  >
                    <AnalysisCard job={job} />
                  </motion.div>
                ))}
              </div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border mt-auto">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between text-[10px] text-muted">
          <span>ReconIQ v1.0.0 — Marketing Intelligence Platform</span>
          <span className="font-mono">Powered by AI</span>
        </div>
      </footer>
    </div>
  );
}
