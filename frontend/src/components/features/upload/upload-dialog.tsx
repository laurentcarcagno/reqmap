"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, X, FileText, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { api, type Document } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ProcessingModal } from "./processing-modal";

interface UploadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDocumentReady?: (doc: Document) => void;
}

export function UploadDialog({ open, onOpenChange, onDocumentReady }: UploadDialogProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<string>("");
  const [processingDocId, setProcessingDocId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: customersData } = useQuery({
    queryKey: ["customers"],
    queryFn: () => api.customers.list(),
    enabled: open,
  });

  const customers = customersData?.data ?? [];

  const { mutate: uploadFile, isPending } = useMutation({
    mutationFn: () => api.documents.upload(selectedFile!, selectedCustomer),
    onSuccess: (doc) => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      setSelectedFile(null);
      setSelectedCustomer("");
      onOpenChange(false);
      setProcessingDocId(doc.id);
    },
    onError: (err: Error) => {
      toast.error(err.message ?? "Upload failed");
    },
  });

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setSelectedFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    disabled: isPending,
  });

  function handleClose() {
    setSelectedFile(null);
    setSelectedCustomer("");
    onOpenChange(false);
  }

  function handleProcessingComplete(doc: Document) {
    setProcessingDocId(null);
    queryClient.invalidateQueries({ queryKey: ["documents"] });
    toast.success(`"${doc.original_filename}" processed — ${doc.requirement_count} requirements extracted`);
    onDocumentReady?.(doc);
  }

  function handleProcessingClose() {
    setProcessingDocId(null);
    queryClient.invalidateQueries({ queryKey: ["documents"] });
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedFile || !selectedCustomer) return;
    uploadFile();
  }

  return (
    <>
    {processingDocId && (
      <ProcessingModal
        documentId={processingDocId}
        onComplete={handleProcessingComplete}
        onClose={handleProcessingClose}
      />
    )}
    {!open ? null : (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="upload-dialog-title"
      className="fixed inset-0 z-50 flex items-center justify-center"
    >
      <div
        className="absolute inset-0 bg-[hsl(206_100%_7%/0.55)]"
        onClick={handleClose}
        aria-hidden="true"
      />
      <div className="relative z-10 w-full max-w-md border border-deep bg-card">
        <div className="flex items-center justify-between bg-deep p-3.5 text-deep-foreground">
          <h2 id="upload-dialog-title" className="text-[15px] font-semibold uppercase tracking-[0.04em]">
            Upload Document
          </h2>
          <button
            onClick={handleClose}
            className="flex h-6 w-6 items-center justify-center border border-white/40 hover:bg-white/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Close dialog"
          >
            <X className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-[18px]">
          {/* Drop zone */}
          <div
            {...getRootProps()}
            className={cn(
              "flex flex-col items-center justify-center border-2 border-dashed p-8 text-center transition-colors cursor-pointer",
              isDragActive
                ? "border-primary bg-accent"
                : "border-border hover:border-deep hover:bg-accent",
              isPending && "pointer-events-none opacity-60",
            )}
            aria-describedby="drop-zone-hint"
          >
            <input {...getInputProps()} aria-label="File input" />
            {selectedFile ? (
              <div className="flex items-center gap-2 text-sm text-foreground">
                <FileText className="h-5 w-5 text-primary" aria-hidden="true" />
                <span className="font-medium truncate max-w-[280px]">{selectedFile.name}</span>
              </div>
            ) : (
              <>
                <Upload className="h-8 w-8 text-muted-foreground mb-2" aria-hidden="true" />
                <p className="text-sm font-medium text-foreground">
                  {isDragActive ? "Drop the file here" : "Drag & drop or click to select"}
                </p>
                <p id="drop-zone-hint" className="text-xs text-muted-foreground mt-1">
                  PDF files only
                </p>
              </>
            )}
          </div>

          {fileRejections.length > 0 && (
            <div className="flex items-center gap-2 border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
              <span>Only PDF files are accepted</span>
            </div>
          )}

          {/* Customer selector */}
          <div className="space-y-1">
            <label htmlFor="customer-select" className="hem-label text-muted-foreground">
              Customer
            </label>
            <select
              id="customer-select"
              value={selectedCustomer}
              onChange={(e) => setSelectedCustomer(e.target.value)}
              disabled={isPending}
              required
              className="hem-input disabled:bg-accent disabled:text-muted-foreground disabled:cursor-not-allowed"
            >
              <option value="">Select a customer…</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 border-t border-border pt-3">
            <button
              type="button"
              onClick={handleClose}
              disabled={isPending}
              className="hem-btn hem-btn-ghost"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!selectedFile || !selectedCustomer || isPending}
              className="hem-btn hem-btn-primary"
            >
              {isPending ? "Uploading…" : "Upload"}
            </button>
          </div>
        </form>
      </div>
    </div>
    )}
    </>
  );
}
