"use client";

import { Moon, Sun, Upload } from "lucide-react";
import { useTheme } from "next-themes";
import { useState } from "react";
import { UploadDialog } from "@/components/features/upload/upload-dialog";
import { cn } from "@/lib/utils";

interface HeaderProps {
  onDocumentReady?: (doc: import("@/lib/api").Document) => void;
}

export function Header({ onDocumentReady }: HeaderProps) {
  const { theme, setTheme } = useTheme();
  const [uploadOpen, setUploadOpen] = useState(false);

  return (
    <header className="flex h-14 shrink-0 items-center border-b border-border bg-card px-4 gap-3">
      <div className="flex items-center gap-2 font-semibold text-foreground">
        <span className="text-primary text-lg font-bold tracking-tight">ReqMap</span>
        <span className="text-muted-foreground text-sm font-normal hidden sm:inline">
          Requirements Extraction
        </span>
      </div>

      <div className="flex-1" />

      <button
        onClick={() => setUploadOpen(true)}
        className={cn(
          "flex items-center gap-2 rounded-md bg-primary px-3 py-1.5 text-sm font-medium",
          "text-primary-foreground hover:bg-primary/90 transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        )}
        aria-label="Upload document"
      >
        <Upload className="h-4 w-4" aria-hidden="true" />
        <span>Upload</span>
      </button>

      <button
        onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        className={cn(
          "flex h-8 w-8 items-center justify-center rounded-md border border-border",
          "text-muted-foreground hover:text-foreground hover:bg-accent transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        )}
        aria-label="Toggle theme"
      >
        <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" aria-hidden="true" />
        <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" aria-hidden="true" />
      </button>

      <UploadDialog open={uploadOpen} onOpenChange={setUploadOpen} {...(onDocumentReady ? { onDocumentReady } : {})} />
    </header>
  );
}
