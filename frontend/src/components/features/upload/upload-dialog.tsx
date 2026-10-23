"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, X, FileText, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { api, type Document, type TableMode } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ProcessingModal } from "./processing-modal";

const TABLE_MODES: { value: TableMode; label: string; hint: string }[] = [
  { value: "image", label: "Image", hint: "Picture of the table in the PDF" },
  { value: "html", label: "HTML", hint: "Table with cell colours and text styles" },
  { value: "markdown", label: "Markdown", hint: "Plain text table, no formatting" },
];

interface UploadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDocumentReady?: (doc: Document) => void;
  /** Files dropped on the Upload button, already selected when the dialog opens. */
  initialFiles?: File[];
}

/** Files sent and processed one after the other, all with the same customer plugin. */
interface Batch {
  files: File[];
  index: number;
  customer: string;
  tables: TableMode;
}

function sameFile(a: File, b: File): boolean {
  return a.name === b.name && a.size === b.size && a.lastModified === b.lastModified;
}

export function UploadDialog({ open, onOpenChange, onDocumentReady, initialFiles }: UploadDialogProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>(initialFiles ?? []);
  const [selectedCustomer, setSelectedCustomer] = useState<string>("");
  const [tableMode, setTableMode] = useState<TableMode>("image");
  const [batch, setBatch] = useState<Batch | null>(null);
  const [processingDocId, setProcessingDocId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: customersData } = useQuery({
    queryKey: ["customers"],
    queryFn: () => api.customers.list(),
    enabled: open,
  });

  const customers = customersData?.data ?? [];

  const { mutateAsync: uploadFile, isPending } = useMutation({
    mutationFn: ({ file, customer, tables }: { file: File; customer: string; tables: TableMode }) =>
      api.documents.upload(file, customer, tables),
  });

  const onDrop = useCallback((accepted: File[]) => {
    setSelectedFiles((current) => [
      ...current,
      ...accepted.filter((file) => !current.some((c) => sameFile(c, file))),
    ]);
  }, []);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    disabled: isPending,
  });

  /** Upload the batch starting at its current file, skipping the files that fail to upload. */
  async function uploadFrom(b: Batch) {
    for (let index = b.index; index < b.files.length; index++) {
      const file = b.files[index]!;
      try {
        const doc = await uploadFile({ file, customer: b.customer, tables: b.tables });
        queryClient.invalidateQueries({ queryKey: ["documents"] });
        setSelectedFiles([]);
        setSelectedCustomer("");
        onOpenChange(false);
        setBatch({ ...b, index });
        setProcessingDocId(doc.id);
        return;
      } catch (err) {
        toast.error(`${file.name}: ${(err as Error).message ?? "Upload failed"}`);
      }
    }
    setBatch(null);
  }

  function processNextFile() {
    setProcessingDocId(null);
    if (batch && batch.index + 1 < batch.files.length) {
      void uploadFrom({ ...batch, index: batch.index + 1 });
    } else {
      setBatch(null);
    }
  }

  function removeFile(file: File) {
    setSelectedFiles((current) => current.filter((c) => c !== file));
  }

  function handleClose() {
    setSelectedFiles([]);
    setSelectedCustomer("");
    onOpenChange(false);
  }

  function handleProcessingComplete(doc: Document) {
    queryClient.invalidateQueries({ queryKey: ["documents"] });
    toast.success(`"${doc.original_filename}" processed — ${doc.requirement_count} requirements extracted`);
    onDocumentReady?.(doc);
    processNextFile();
  }

  function handleProcessingClose() {
    queryClient.invalidateQueries({ queryKey: ["documents"] });
    processNextFile();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (selectedFiles.length === 0 || !selectedCustomer) return;
    void uploadFrom({ files: selectedFiles, index: 0, customer: selectedCustomer, tables: tableMode });
  }

  const batchLabel =
    batch && batch.files.length > 1
      ? `File ${batch.index + 1} of ${batch.files.length} · ${batch.files[batch.index]!.name}`
      : "";

  return (
    <>
    {processingDocId && (
      <ProcessingModal
        documentId={processingDocId}
        {...(batchLabel ? { label: batchLabel } : {})}
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
            Upload Documents
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
              "flex flex-col items-center justify-center border-2 border-dashed text-center transition-colors cursor-pointer",
              selectedFiles.length > 0 ? "p-4" : "p-8",
              isDragActive
                ? "border-primary bg-accent"
                : "border-border hover:border-deep hover:bg-accent",
              isPending && "pointer-events-none opacity-60",
            )}
            aria-describedby="drop-zone-hint"
          >
            <input {...getInputProps()} aria-label="File input" />
            <Upload className="h-8 w-8 text-muted-foreground mb-2" aria-hidden="true" />
            <p className="text-sm font-medium text-foreground">
              {isDragActive
                ? "Drop the files here"
                : selectedFiles.length > 0
                  ? "Drop or click to add more files"
                  : "Drag & drop or click to select"}
            </p>
            <p id="drop-zone-hint" className="text-xs text-muted-foreground mt-1">
              PDF files only · several files allowed
            </p>
          </div>

          {fileRejections.length > 0 && (
            <div className="flex items-center gap-2 border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
              <span>Only PDF files are accepted</span>
            </div>
          )}

          {selectedFiles.length > 0 && (
            <div className="space-y-1">
              <ul
                aria-label="Selected files"
                className="max-h-40 divide-y divide-border overflow-y-auto border border-border"
              >
                {selectedFiles.map((file) => (
                  <li
                    key={`${file.name}-${file.size}-${file.lastModified}`}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm text-foreground"
                  >
                    <FileText className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
                    <span className="flex-1 truncate font-medium">{file.name}</span>
                    <button
                      type="button"
                      onClick={() => removeFile(file)}
                      disabled={isPending}
                      aria-label={`Remove ${file.name}`}
                      className="flex h-5 w-5 shrink-0 items-center justify-center hover:bg-accent disabled:opacity-50"
                    >
                      <X className="h-3 w-3" aria-hidden="true" />
                    </button>
                  </li>
                ))}
              </ul>
              {selectedFiles.length > 1 && (
                <p className="text-xs text-muted-foreground">
                  Files are processed one after the other, all with the same customer.
                </p>
              )}
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

          {/* Table handling */}
          <fieldset className="space-y-1" disabled={isPending}>
            <legend className="hem-label text-muted-foreground">Tables</legend>
            <div className="grid grid-cols-3 gap-2">
              {TABLE_MODES.map((mode) => (
                <label
                  key={mode.value}
                  title={mode.hint}
                  className={cn(
                    "cursor-pointer border px-3 py-2 text-center text-sm transition-colors",
                    tableMode === mode.value
                      ? "border-deep bg-deep text-deep-foreground"
                      : "border-border hover:border-deep hover:bg-accent",
                  )}
                >
                  <input
                    type="radio"
                    name="table-mode"
                    value={mode.value}
                    checked={tableMode === mode.value}
                    onChange={() => setTableMode(mode.value)}
                    className="sr-only"
                  />
                  {mode.label}
                </label>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">{TABLE_MODES.find((m) => m.value === tableMode)?.hint}</p>
          </fieldset>

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
              disabled={selectedFiles.length === 0 || !selectedCustomer || isPending}
              className="hem-btn hem-btn-primary"
            >
              {isPending
                ? "Uploading…"
                : selectedFiles.length > 1
                  ? `Upload ${selectedFiles.length} files`
                  : "Upload"}
            </button>
          </div>
        </form>
      </div>
    </div>
    )}
    </>
  );
}
