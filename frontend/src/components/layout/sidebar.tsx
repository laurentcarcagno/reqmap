"use client";

import { useState } from "react";
import { Upload } from "lucide-react";
import { DocumentList } from "@/components/features/documents/document-list";
import { UploadDialog } from "@/components/features/upload/upload-dialog";
import type { Document } from "@/lib/api";

interface SidebarProps {
  selectedDocumentId: string | null;
  onSelectDocument: (id: string) => void;
  onDocumentDeleted: (id: string) => void;
  onDocumentReady?: (doc: Document) => void;
}

export function Sidebar({ selectedDocumentId, onSelectDocument, onDocumentDeleted, onDocumentReady }: SidebarProps) {
  const [uploadOpen, setUploadOpen] = useState(false);

  return (
    <aside
      className="flex w-72 shrink-0 flex-col border-r border-sidebar-border bg-sidebar overflow-hidden"
      aria-label="Document list"
    >
      <div className="flex h-10 shrink-0 items-center justify-between border-b border-sidebar-border px-4">
        <h2 className="hem-label tracking-[0.18em] text-sidebar-foreground/70">Documents</h2>
        <button
          type="button"
          onClick={() => setUploadOpen(true)}
          className="hem-btn hem-btn-primary h-6 gap-1.5 px-2 text-[10px]"
          aria-label="Upload document"
        >
          <Upload className="h-3 w-3" aria-hidden="true" />
          <span>Upload</span>
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        <DocumentList
          selectedDocumentId={selectedDocumentId}
          onSelectDocument={onSelectDocument}
          onDocumentDeleted={onDocumentDeleted}
        />
      </div>
      <UploadDialog open={uploadOpen} onOpenChange={setUploadOpen} {...(onDocumentReady ? { onDocumentReady } : {})} />
    </aside>
  );
}
