"use client";

import { useState } from "react";
import { Upload } from "lucide-react";
import { toast } from "sonner";
import { DocumentList } from "@/components/features/documents/document-list";
import { UploadDialog } from "@/components/features/upload/upload-dialog";
import type { Document } from "@/lib/api";
import { cn } from "@/lib/utils";

function isPdf(file: File): boolean {
  return file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
}

function hasFiles(e: React.DragEvent): boolean {
  return Array.from(e.dataTransfer.types).includes("Files");
}

interface SidebarProps {
  selectedDocumentId: string | null;
  onSelectDocument: (id: string) => void;
  onDocumentDeleted: (id: string) => void;
  onDocumentReady?: (doc: Document) => void;
}

export function Sidebar({ selectedDocumentId, onSelectDocument, onDocumentDeleted, onDocumentReady }: SidebarProps) {
  const [uploadOpen, setUploadOpen] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  // A new drop remounts the dialog (via its key) so it starts from the dropped files.
  const [dropped, setDropped] = useState<{ id: number; files: File[] }>({ id: 0, files: [] });

  function handleDragOver(e: React.DragEvent) {
    if (!hasFiles(e)) return;
    e.preventDefault();
    setDragOver(true);
  }

  function handleDrop(e: React.DragEvent) {
    if (!hasFiles(e)) return;
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    const pdfs = files.filter(isPdf);
    if (pdfs.length < files.length) {
      toast.error(
        pdfs.length === 0 ? "Only PDF files are accepted" : `${files.length - pdfs.length} non-PDF file(s) ignored`,
      );
    }
    if (pdfs.length === 0) return;
    setDropped((prev) => ({ id: prev.id + 1, files: pdfs }));
    setUploadOpen(true);
  }

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
          onDragEnter={handleDragOver}
          onDragOver={handleDragOver}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          className={cn(
            "hem-btn hem-btn-primary h-6 gap-1.5 px-2 text-[10px]",
            dragOver && "ring-2 ring-ring ring-offset-1",
          )}
          aria-label="Upload document"
        >
          <Upload className="pointer-events-none h-3 w-3" aria-hidden="true" />
          <span className="pointer-events-none">{dragOver ? "Drop PDFs" : "Upload"}</span>
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        <DocumentList
          selectedDocumentId={selectedDocumentId}
          onSelectDocument={onSelectDocument}
          onDocumentDeleted={onDocumentDeleted}
        />
      </div>
      <UploadDialog
        key={dropped.id}
        open={uploadOpen}
        onOpenChange={setUploadOpen}
        initialFiles={dropped.files}
        {...(onDocumentReady ? { onDocumentReady } : {})}
      />
    </aside>
  );
}
