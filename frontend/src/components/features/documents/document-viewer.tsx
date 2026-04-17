"use client";

import { useQuery } from "@tanstack/react-query";
import { FileText } from "lucide-react";
import { api } from "@/lib/api";
import { NodeTable } from "@/components/features/nodes/node-table";
import { DocumentHeader } from "./document-header";

interface DocumentViewerProps {
  documentId: string | null;
}

export function DocumentViewer({ documentId }: DocumentViewerProps) {
  const { data: doc } = useQuery({
    queryKey: ["documents", documentId],
    queryFn: () => api.documents.get(documentId!),
    enabled: !!documentId,
  });

  const { data: nodesData } = useQuery({
    queryKey: ["nodes", documentId],
    queryFn: () => api.nodes.list(documentId!, { limit: 500 }),
    enabled: !!documentId && doc?.status === "completed",
  });

  const nodes = nodesData?.data ?? [];

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
      {doc && <DocumentHeader document={doc} nodes={nodes} />}
      <div className="flex-1 overflow-auto">
        <NodeTable documentId={documentId} />
      </div>
    </div>
  );
}
