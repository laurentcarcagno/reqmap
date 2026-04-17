"use client";

import { DocumentList } from "@/components/features/documents/document-list";

interface SidebarProps {
  selectedDocumentId: string | null;
  onSelectDocument: (id: string) => void;
  onDocumentDeleted: (id: string) => void;
}

export function Sidebar({ selectedDocumentId, onSelectDocument, onDocumentDeleted }: SidebarProps) {
  return (
    <aside
      className="flex w-72 shrink-0 flex-col border-r border-sidebar-border bg-sidebar overflow-hidden"
      aria-label="Document list"
    >
      <div className="flex h-10 shrink-0 items-center border-b border-sidebar-border px-4">
        <h2 className="text-sm font-semibold text-sidebar-foreground">Documents</h2>
      </div>
      <div className="flex-1 overflow-y-auto">
        <DocumentList
          selectedDocumentId={selectedDocumentId}
          onSelectDocument={onSelectDocument}
          onDocumentDeleted={onDocumentDeleted}
        />
      </div>
    </aside>
  );
}
