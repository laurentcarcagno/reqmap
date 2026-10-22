"use client";

import { useCallback, useState } from "react";
import { Header } from "./header";
import { Sidebar } from "./sidebar";
import { DocumentViewer } from "@/components/features/documents/document-viewer";
import type { Document } from "@/lib/api";

export function AppShell() {
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);

  const handleDocumentReady = useCallback((doc: Document) => {
    setSelectedDocumentId(doc.id);
  }, []);

  const handleDocumentDeleted = useCallback((id: string) => {
    setSelectedDocumentId((current) => (current === id ? null : current));
  }, []);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          selectedDocumentId={selectedDocumentId}
          onSelectDocument={setSelectedDocumentId}
          onDocumentDeleted={handleDocumentDeleted}
          onDocumentReady={handleDocumentReady}
        />
        <main
          id="main-content"
          className="flex flex-1 flex-col overflow-hidden"
          aria-label="Document content"
        >
          <DocumentViewer documentId={selectedDocumentId} />
        </main>
      </div>
    </div>
  );
}
