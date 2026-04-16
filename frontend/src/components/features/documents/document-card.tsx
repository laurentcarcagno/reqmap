"use client";

import { FileText, Loader2, CheckCircle2, XCircle, Clock } from "lucide-react";
import type { Document, DocumentStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

interface DocumentCardProps {
  document: Document;
  isSelected: boolean;
  onSelect: () => void;
}

const STATUS_ICONS: Record<DocumentStatus, React.ReactNode> = {
  pending: <Clock className="h-3.5 w-3.5 text-[hsl(var(--status-pending))]" aria-hidden="true" />,
  processing: <Loader2 className="h-3.5 w-3.5 text-[hsl(var(--status-processing))] animate-spin" aria-hidden="true" />,
  completed: <CheckCircle2 className="h-3.5 w-3.5 text-[hsl(var(--status-completed))]" aria-hidden="true" />,
  failed: <XCircle className="h-3.5 w-3.5 text-[hsl(var(--status-failed))]" aria-hidden="true" />,
};

const STATUS_LABELS: Record<DocumentStatus, string> = {
  pending: "Pending",
  processing: "Processing",
  completed: "Completed",
  failed: "Failed",
};

export function DocumentCard({ document, isSelected, onSelect }: DocumentCardProps) {
  const date = new Date(document.created_at).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });

  return (
    <li role="option" aria-selected={isSelected}>
      <button
        onClick={onSelect}
        className={cn(
          "w-full rounded-md px-3 py-2.5 text-left transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
          isSelected
            ? "bg-sidebar-accent text-sidebar-accent-foreground"
            : "text-sidebar-foreground hover:bg-sidebar-accent/60",
        )}
      >
        <div className="flex items-start gap-2">
          <FileText className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
          <div className="min-w-0 flex-1">
            <p
              className="truncate text-sm font-medium leading-tight"
              title={document.original_filename}
            >
              {document.original_filename}
            </p>
            <div className="mt-1 flex items-center gap-2">
              <span
                className="flex items-center gap-1 text-xs text-muted-foreground"
                aria-label={`Status: ${STATUS_LABELS[document.status]}`}
              >
                {STATUS_ICONS[document.status]}
                {STATUS_LABELS[document.status]}
              </span>
              {document.status === "completed" && (
                <span className="text-xs text-muted-foreground">
                  · {document.node_count} nodes
                </span>
              )}
              <span className="ml-auto text-xs text-muted-foreground">{date}</span>
            </div>
            {document.status === "failed" && document.error_message && (
              <p className="mt-0.5 truncate text-xs text-destructive" title={document.error_message}>
                {document.error_message}
              </p>
            )}
          </div>
        </div>
      </button>
    </li>
  );
}
