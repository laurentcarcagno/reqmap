"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";

interface DescriptionCellProps {
  text: string;
  expandAll: boolean;
}

export function DescriptionCell({ text, expandAll }: DescriptionCellProps) {
  const [localExpanded, setLocalExpanded] = useState(false);

  if (!text) return <span className="text-muted-foreground text-xs">—</span>;

  const expanded = expandAll || localExpanded;

  return (
    <div className="relative">
      <div
        className={cn(
          "prose prose-xs dark:prose-invert max-w-none text-xs text-muted-foreground",
          "prose-p:my-0.5 prose-ul:my-0.5 prose-ol:my-0.5 prose-li:my-0",
          "prose-headings:text-foreground prose-headings:font-semibold prose-headings:my-1",
          "prose-code:text-[11px] prose-code:bg-muted prose-code:px-1 ",
          "prose-strong:text-foreground",
          !expanded && "line-clamp-2",
        )}
      >
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
      </div>
      {!expandAll && (
        <button
          type="button"
          onClick={() => setLocalExpanded((v) => !v)}
          className="mt-0.5 text-[11px] text-primary hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          aria-label={expanded ? "Collapse description" : "Expand description"}
        >
          {expanded ? "Show less" : "…more"}
        </button>
      )}
    </div>
  );
}
