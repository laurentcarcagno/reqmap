"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FileText, Loader2, CheckCircle2, XCircle, Clock, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api, type Document, type DocumentStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

interface DocumentCardProps {
  document: Document;
  isSelected: boolean;
  onSelect: () => void;
  onDeleted: (id: string) => void;
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

export function DocumentCard({ document, isSelected, onSelect, onDeleted }: DocumentCardProps) {
  const queryClient = useQueryClient();
  const [confirmDelete, setConfirmDelete] = useState(false);

  const date = new Date(document.created_at).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });

  const { mutate: doDelete, isPending: isDeleting } = useMutation({
    mutationFn: () => api.documents.delete(document.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      onDeleted(document.id);
      toast.success(`"${document.original_filename}" deleted`);
    },
    onError: () => {
      toast.error("Failed to delete document");
      setConfirmDelete(false);
    },
  });

  return (
    <li role="option" aria-selected={isSelected} className="group relative">
      <button
        onClick={onSelect}
        className={cn(
          "w-full border-l-[3px] px-3 py-2.5 text-left transition-colors pr-8",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
          isSelected
            ? "border-primary bg-sidebar-accent text-sidebar-accent-foreground"
            : "border-transparent text-sidebar-foreground/70 hover:bg-sidebar-accent/60",
        )}
      >
        <div className="flex items-start gap-2">
          <FileText className="mt-0.5 h-4 w-4 shrink-0 text-sidebar-foreground/50" aria-hidden="true" />
          <div className="min-w-0 flex-1">
            <p
              className="truncate text-sm font-medium leading-tight"
              title={document.original_filename}
            >
              {document.original_filename}
            </p>
            <div className="mt-1 flex items-center gap-2">
              <span
                className="flex items-center gap-1 text-xs text-sidebar-foreground/60"
                aria-label={`Status: ${STATUS_LABELS[document.status]}`}
              >
                {STATUS_ICONS[document.status]}
                {STATUS_LABELS[document.status]}
              </span>
              {document.status === "completed" && (
                <span className="font-mono text-xs text-sidebar-foreground/60">
                  · {document.node_count} nodes
                </span>
              )}
              <span className="ml-auto font-mono text-xs text-sidebar-foreground/60">{date}</span>
            </div>
            {document.status === "failed" && document.error_message && (
              <p className="mt-0.5 truncate text-xs text-destructive" title={document.error_message}>
                {document.error_message}
              </p>
            )}
          </div>
        </div>
      </button>

      {/* Delete button — appears on hover */}
      {!confirmDelete && (
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); setConfirmDelete(true); }}
          disabled={isDeleting}
          aria-label={`Delete ${document.original_filename}`}
          className={cn(
            "absolute right-1.5 top-1/2 -translate-y-1/2 p-1",
            "text-sidebar-foreground/40 hover:text-destructive hover:bg-destructive/10 transition-colors",
            "opacity-0 group-hover:opacity-100 focus-visible:opacity-100",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
          )}
        >
          <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
        </button>
      )}

      {/* Inline confirm */}
      {confirmDelete && (
        <div className="absolute inset-0 flex items-center justify-between gap-1 bg-sidebar px-3 py-2 z-10 border-l-[3px] border-destructive">
          <span className="text-xs font-medium text-destructive truncate">Delete?</span>
          <div className="flex items-center gap-1 shrink-0">
            <button
              type="button"
              onClick={() => doDelete()}
              disabled={isDeleting}
              className="hem-label px-2 py-0.5 bg-destructive text-destructive-foreground hover:bg-destructive/90 disabled:opacity-60 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              {isDeleting ? <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" /> : "Yes"}
            </button>
            <button
              type="button"
              onClick={() => setConfirmDelete(false)}
              disabled={isDeleting}
              className="hem-label px-2 py-0.5 bg-muted text-muted-foreground hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              No
            </button>
          </div>
        </div>
      )}
    </li>
  );
}
