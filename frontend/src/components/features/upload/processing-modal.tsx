"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
import { api, type Document } from "@/lib/api";

interface ProcessingModalProps {
  documentId: string | null;
  onComplete: (doc: Document) => void;
  onClose: () => void;
}

function useElapsedTimer(running: boolean): number {
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef<number>(Date.now());

  useEffect(() => {
    if (!running) return;
    startRef.current = Date.now();
    setElapsed(0);
    const id = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startRef.current) / 1000));
    }, 1000);
    return () => clearInterval(id);
  }, [running]);

  return elapsed;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export function ProcessingModal({ documentId, onComplete, onClose }: ProcessingModalProps) {
  const [isDone, setIsDone] = useState(false);

  const { data: doc } = useQuery({
    queryKey: ["documents", documentId],
    queryFn: () => api.documents.get(documentId!),
    enabled: !!documentId && !isDone,
    refetchInterval: (query) => {
      const d = query.state.data;
      if (d?.status === "completed" || d?.status === "failed") return false;
      return 1500;
    },
  });

  const status = doc?.status ?? "pending";
  const isProcessing = status === "pending" || status === "processing";
  const elapsed = useElapsedTimer(isProcessing);

  useEffect(() => {
    if (doc?.status === "completed" || doc?.status === "failed") {
      setIsDone(true);
    }
  }, [doc?.status]);

  useEffect(() => {
    if (isDone && doc?.status === "completed") {
      const timeout = setTimeout(() => onComplete(doc), 800);
      return () => clearTimeout(timeout);
    }
  }, [isDone, doc, onComplete]);

  if (!documentId) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="processing-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center"
    >
      <div className="absolute inset-0 bg-[hsl(206_100%_7%/0.55)]" aria-hidden="true" />
      <div className="relative z-10 w-full max-w-sm border border-deep bg-card p-8 text-center">
        {isProcessing && (
          <>
            <Loader2 className="mx-auto h-10 w-10 animate-spin text-primary mb-4" aria-hidden="true" />
            <h2 id="processing-modal-title" className="text-base font-semibold text-card-foreground">
              Processing document…
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Extracting requirements from PDF
            </p>
            <div className="mt-4 inline-flex items-center gap-1.5 bg-muted px-3 py-1 text-xs font-mono text-muted-foreground">
              <span className="h-1.5 w-1.5 bg-primary animate-pulse" aria-hidden="true" />
              {formatTime(elapsed)} elapsed
            </div>
          </>
        )}

        {status === "completed" && (
          <>
            <CheckCircle2 className="mx-auto h-10 w-10 text-[hsl(var(--status-completed))] mb-4" aria-hidden="true" />
            <h2 id="processing-modal-title" className="text-base font-semibold text-card-foreground">
              Processing complete
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              {doc?.requirement_count} requirements · {doc?.title_count} titles extracted
            </p>
          </>
        )}

        {status === "failed" && (
          <>
            <XCircle className="mx-auto h-10 w-10 text-destructive mb-4" aria-hidden="true" />
            <h2 id="processing-modal-title" className="text-base font-semibold text-card-foreground">
              Processing failed
            </h2>
            <p className="mt-2 text-sm text-muted-foreground line-clamp-3">
              {doc?.error_message ?? "An unexpected error occurred"}
            </p>
            <button
              type="button"
              onClick={onClose}
              className="mt-5 hem-btn hem-btn-primary"
            >
              Close
            </button>
          </>
        )}
      </div>
    </div>
  );
}
