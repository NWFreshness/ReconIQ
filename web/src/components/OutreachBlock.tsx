"use client";

import { useState } from "react";
import { Check, Copy, Mail, MessageSquare, Phone, FileText, ListChecks, Shield } from "lucide-react";

interface OutreachBlockProps {
  data: Record<string, unknown>;
}

function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement("textarea");
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="text-xs px-2 py-1 rounded-md bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20 transition-all flex items-center gap-1.5"
      aria-label={`Copy ${label}`}
    >
      {copied ? (
        <>
          <Check className="w-3 h-3" />
          Copied!
        </>
      ) : (
        <>
          <Copy className="w-3 h-3" />
          Copy
        </>
      )}
    </button>
  );
}

const assetFields: { key: string; label: string; icon: React.ReactNode }[] = [
  { key: "cold_email", label: "Cold Email", icon: <Mail className="w-3.5 h-3.5" /> },
  { key: "linkedin_dm", label: "LinkedIn DM", icon: <MessageSquare className="w-3.5 h-3.5" /> },
  { key: "discovery_call_opener", label: "Discovery Call Opener", icon: <Phone className="w-3.5 h-3.5" /> },
  { key: "proposal_outline", label: "Proposal Outline", icon: <FileText className="w-3.5 h-3.5" /> },
];

export function OutreachBlock({ data }: OutreachBlockProps) {
  if (!data || data.error) {
    return (
      <div className="bg-surface border border-border rounded-xl p-5 text-center">
        <p className="text-xs text-muted">No outreach pack data available.</p>
      </div>
    );
  }

  const followUps = data.follow_up_sequence as string[] | undefined;
  const confidence = data.data_confidence as string | undefined;
  const limitations = data.data_limitations as string[] | undefined;

  return (
    <div className="bg-surface border border-border rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-border bg-accent/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-3.5 h-3.5 text-accent" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">
            Outreach Pack
          </h3>
        </div>
      </div>
      <div className="divide-y divide-border">
        {assetFields.map(({ key, label, icon }) => {
          const value = data[key] as string | undefined;
          if (!value) return null;
          return (
            <div key={key} className="p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-accent">{icon}</span>
                  <span className="text-xs font-medium text-foreground">{label}</span>
                </div>
                <CopyButton text={value} label={label} />
              </div>
              <p className="text-xs text-muted whitespace-pre-wrap leading-relaxed">{value}</p>
            </div>
          );
        })}

        {followUps && Array.isArray(followUps) && followUps.length > 0 && (
          <div className="p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <ListChecks className="w-3.5 h-3.5 text-accent" />
                <span className="text-xs font-medium text-foreground">Follow-up Sequence</span>
              </div>
              <CopyButton text={followUps.map((f, i) => `${i + 1}. ${f}`).join("\n")} label="Follow-up Sequence" />
            </div>
            <ul className="text-xs text-muted space-y-1">
              {followUps.map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-accent mt-0.5 min-w-[14px]">{i + 1}.</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {(confidence || (limitations && limitations.length > 0)) && (
          <div className="px-4 py-3 bg-background/50 text-[11px] text-muted">
            {confidence && (
              <p>
                <span className="font-medium text-foreground">Confidence:</span> {confidence}
              </p>
            )}
            {limitations && limitations.length > 0 && (
              <p className="mt-1">
                <span className="font-medium text-foreground">Limitations:</span>{" "}
                {limitations.join("; ")}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
