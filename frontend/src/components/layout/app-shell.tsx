"use client";

import { useState } from "react";
import { Header } from "./header";
import { Sidebar } from "./sidebar";
import { DocumentViewer } from "@/components/features/documents/document-viewer";

export function AppShell() {
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          selectedDocumentId={selectedDocumentId}
          onSelectDocument={setSelectedDocumentId}
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
