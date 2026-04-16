"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, X, FileText, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

interface UploadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UploadDialog({ open, onOpenChange }: UploadDialogProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<string>("");
  const queryClient = useQueryClient();

  const { data: customersData } = useQuery({
    queryKey: ["customers"],
    queryFn: () => api.customers.list(),
    enabled: open,
  });

  const customers = customersData?.data ?? [];

  const { mutate: uploadFile, isPending } = useMutation({
    mutationFn: () => api.documents.upload(selectedFile!, selectedCustomer),
    onSuccess: () => {
      toast.success("Document uploaded and processing started");
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      handleClose();
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

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedFile || !selectedCustomer) return;
    uploadFile();
  }

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="upload-dialog-title"
      className="fixed inset-0 z-50 flex items-center justify-center"
    >
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
        aria-hidden="true"
      />
      <div className="relative z-10 w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 id="upload-dialog-title" className="text-lg font-semibold text-card-foreground">
            Upload Document
          </h2>
          <button
            onClick={handleClose}
            className="rounded-md p-1 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Close dialog"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Drop zone */}
          <div
            {...getRootProps()}
            className={cn(
              "flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-colors cursor-pointer",
              isDragActive
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50 hover:bg-accent/30",
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
            <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
              <span>Only PDF files are accepted</span>
            </div>
          )}

          {/* Customer selector */}
          <div className="space-y-1">
            <label htmlFor="customer-select" className="text-sm font-medium text-foreground">
              Customer
            </label>
            <select
              id="customer-select"
              value={selectedCustomer}
              onChange={(e) => setSelectedCustomer(e.target.value)}
              disabled={isPending}
              required
              className={cn(
                "w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
                "text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                "disabled:opacity-60",
              )}
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
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={handleClose}
              disabled={isPending}
              className="rounded-md px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent transition-colors disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!selectedFile || !selectedCustomer || isPending}
              className={cn(
                "rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground",
                "hover:bg-primary/90 transition-colors disabled:opacity-60",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              )}
            >
              {isPending ? "Uploading…" : "Upload"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
