"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";

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
      className="btn"
      aria-label={`Copy ${label}`}
    >
      {copied ? (
        <>
          <Check className="w-3 h-3" />
          Copied
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

const assetFields: { key: string; label: string }[] = [
  { key: "cold_email", label: "Cold email" },
  { key: "linkedin_dm", label: "LinkedIn DM" },
  { key: "discovery_call_opener", label: "Discovery call opener" },
  { key: "proposal_outline", label: "Proposal outline" },
];

export function OutreachBlock({ data }: OutreachBlockProps) {
  if (!data || data.error) {
    return <p className="text-sm text-muted">No outreach pack data available.</p>;
  }

  const followUps = data.follow_up_sequence as string[] | undefined;
  const confidence = data.data_confidence as string | undefined;
  const limitations = data.data_limitations as string[] | undefined;

  return (
    <div className="divide-y divide-border border-y border-border max-w-3xl">
      {assetFields.map(({ key, label }) => {
        const value = data[key] as string | undefined;
        if (!value) return null;
        return (
          <div key={key} className="py-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold">{label}</h3>
              <CopyButton text={value} label={label} />
            </div>
            <p className="text-sm text-muted whitespace-pre-wrap leading-relaxed">{value}</p>
          </div>
        );
      })}

      {followUps && Array.isArray(followUps) && followUps.length > 0 && (
        <div className="py-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold">Follow-up sequence</h3>
            <CopyButton text={followUps.map((f, i) => `${i + 1}. ${f}`).join("\n")} label="Follow-up sequence" />
          </div>
          <ol className="list-decimal pl-5 space-y-1 text-sm text-muted">
            {followUps.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ol>
        </div>
      )}

      {(confidence || (limitations && limitations.length > 0)) && (
        <div className="py-3 text-xs text-muted">
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
  );
}
