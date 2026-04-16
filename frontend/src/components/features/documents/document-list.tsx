"use client";

import { useQuery } from "@tanstack/react-query";
import { FileText, Loader2, AlertCircle } from "lucide-react";
import { api, type Document } from "@/lib/api";
import { DocumentCard } from "./document-card";

interface DocumentListProps {
  selectedDocumentId: string | null;
  onSelectDocument: (id: string) => void;
}

export function DocumentList({ selectedDocumentId, onSelectDocument }: DocumentListProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["documents"],
    queryFn: () => api.documents.list({ limit: 100 }),
    refetchInterval: (query) => {
      const docs: Document[] = query.state.data?.data ?? [];
      return docs.some((d) => d.status === "processing" || d.status === "pending")
        ? 3000
        : false;
    },
  });

  const documents = data?.data ?? [];

  if (isLoading) {
    return (
      <div className="flex flex-col gap-2 p-3" aria-label="Loading documents">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="h-16 rounded-md bg-sidebar-accent/50 animate-pulse"
            aria-hidden="true"
          />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 p-6 text-center">
        <AlertCircle className="h-6 w-6 text-destructive" aria-hidden="true" />
        <p className="text-sm text-muted-foreground">Failed to load documents</p>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 p-6 text-center">
        <FileText className="h-8 w-8 text-muted-foreground/40" aria-hidden="true" />
        <div>
          <p className="text-sm font-medium text-foreground">No documents yet</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Upload a PDF to get started
          </p>
        </div>
      </div>
    );
  }

  return (
    <ul className="flex flex-col gap-1 p-2" role="listbox" aria-label="Processed documents">
      {documents.map((doc) => (
        <DocumentCard
          key={doc.id}
          document={doc}
          isSelected={doc.id === selectedDocumentId}
          onSelect={() => onSelectDocument(doc.id)}
        />
      ))}
    </ul>
  );
}
