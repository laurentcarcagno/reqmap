"use client";

import { useCallback, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Pencil } from "lucide-react";
import { cn } from "@/lib/utils";

interface DescriptionCellProps {
  text: string;
  expandAll: boolean;
  onSave: (text: string) => void;
}

export function DescriptionCell({ text, expandAll, onSave }: DescriptionCellProps) {
  const [localExpanded, setLocalExpanded] = useState(false);
  const [isTruncated, setIsTruncated] = useState(false);
  const [draft, setDraft] = useState<string | null>(null); // null = not editing

  const expanded = expandAll || localExpanded;

  // Measure whether the clamped text is cut off; re-measure when the column is resized.
  // While expanded the clamp is gone, so the last measurement is kept for "Show less".
  const measure = useCallback(
    (el: HTMLDivElement | null) => {
      if (!el || expanded) return;
      const check = () => setIsTruncated(el.scrollHeight > el.clientHeight + 1);
      check();
      const observer = new ResizeObserver(check);
      observer.observe(el);
      return () => observer.disconnect();
    },
    [expanded, text],
  );

  function commit() {
    if (draft !== null && draft !== text) onSave(draft);
    setDraft(null);
  }

  if (draft !== null) {
    return (
      <div className="space-y-1.5">
        <textarea
          autoFocus
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Escape") setDraft(null);
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) commit();
          }}
          rows={Math.min(Math.max(draft.split("\n").length + 1, 4), 20)}
          aria-label="Description (markdown)"
          className="hem-input resize-y font-mono text-xs"
        />
        <div className="flex items-center gap-2">
          <button type="button" onClick={commit} className="hem-btn hem-btn-primary h-6 px-2 text-[10px]">
            Save
          </button>
          <button type="button" onClick={() => setDraft(null)} className="hem-btn hem-btn-ghost h-6 px-2 text-[10px]">
            Cancel
          </button>
          <span className="text-[10px] text-muted-foreground">Markdown · Ctrl+Enter saves · Esc cancels</span>
        </div>
      </div>
    );
  }

  const editButton = (
    <button
      type="button"
      onClick={() => setDraft(text)}
      aria-label="Edit description"
      title="Edit description"
      className="absolute right-0 top-0 p-1 text-muted-foreground opacity-0 hover:bg-accent hover:text-foreground focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring group-hover/desc:opacity-100"
    >
      <Pencil className="h-3 w-3" aria-hidden="true" />
    </button>
  );

  if (!text) {
    return (
      <div className="group/desc relative min-h-5 pr-6">
        <span className="text-muted-foreground text-xs">—</span>
        {editButton}
      </div>
    );
  }

  return (
    <div className="group/desc relative">
      <div className="pr-6" onDoubleClick={() => setDraft(text)}>
        <div ref={measure} className={cn("hem-md text-xs text-muted-foreground", !expanded && "line-clamp-2")}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
        </div>
      </div>
      {editButton}
      {!expandAll && (isTruncated || localExpanded) && (
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
