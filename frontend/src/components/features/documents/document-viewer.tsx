"use client";

import { useQuery } from "@tanstack/react-query";
import { FileText } from "lucide-react";
import { api } from "@/lib/api";
import { NodeTable } from "@/components/features/nodes/node-table";

interface DocumentViewerProps {
  documentId: string | null;
}

export function DocumentViewer({ documentId }: DocumentViewerProps) {
  const { data: doc } = useQuery({
    queryKey: ["documents", documentId],
    queryFn: () => api.documents.get(documentId!),
    enabled: !!documentId,
  });

  if (!documentId) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center p-8">
        <FileText className="h-12 w-12 text-muted-foreground/30" aria-hidden="true" />
        <div>
          <p className="text-base font-medium text-foreground">No document selected</p>
          <p className="text-sm text-muted-foreground mt-1">
            Select a document from the sidebar or upload a new one
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {doc && (
        <div className="flex h-10 shrink-0 items-center border-b border-border px-4 gap-3">
          <h1 className="text-sm font-semibold text-foreground truncate" title={doc.original_filename}>
            {doc.original_filename}
          </h1>
          {doc.status === "completed" && (
            <span className="text-xs text-muted-foreground shrink-0">
              {doc.title_count} titles · {doc.requirement_count} requirements
            </span>
          )}
        </div>
      )}
      <div className="flex-1 overflow-auto">
        <NodeTable documentId={documentId} />
      </div>
    </div>
  );
}
