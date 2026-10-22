"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, Download, Loader2, Plus, Trash2, X } from "lucide-react";
import { toast } from "sonner";
import {
  api,
  type Classification,
  type ExportControl,
  type ExportSettings,
} from "@/lib/api";
import { cn } from "@/lib/utils";

interface ExportDialogProps {
  documentId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type TabId = "document" | "applicable" | "reference" | "acronyms";

const TABS: { id: TabId; label: string }[] = [
  { id: "document", label: "Document" },
  { id: "applicable", label: "Applicable docs" },
  { id: "reference", label: "Reference docs" },
  { id: "acronyms", label: "Acronyms" },
];

const CLASSIFICATIONS: { value: Classification; label: string }[] = [
  { value: "", label: "Not set" },
  { value: "public", label: "Public" },
  { value: "commercial", label: "Commer. In confidence" },
  { value: "internal", label: "Internal Only" },
];

const EXPORT_CONTROLS: { value: ExportControl; label: string }[] = [
  { value: "", label: "Not set" },
  { value: "Not Listed/Not Controlled", label: "Not Listed / Not Controlled" },
  { value: "Listed/Controlled", label: "Listed / Controlled" },
];

type TextKey = {
  [K in keyof ExportSettings]: ExportSettings[K] extends string ? K : never;
}[keyof ExportSettings];

export function ExportDialog({ documentId, open, onOpenChange }: ExportDialogProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["export-settings", documentId],
    queryFn: () => api.documents.getExportSettings(documentId),
    enabled: open,
    // The form owns the values once loaded: never refetch under the user's hands
    staleTime: Infinity,
  });

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="export-dialog-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <div
        className="absolute inset-0 bg-[hsl(206_100%_7%/0.55)]"
        onClick={() => onOpenChange(false)}
        aria-hidden="true"
      />
      <div className="relative z-10 flex max-h-full w-full max-w-3xl flex-col border border-deep bg-card">
        <div className="flex shrink-0 items-center justify-between bg-deep p-3.5 text-deep-foreground">
          <h2 id="export-dialog-title" className="text-[15px] font-semibold uppercase tracking-[0.04em]">
            Export compliance matrix
          </h2>
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="flex h-6 w-6 items-center justify-center border border-white/40 transition-colors hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Close dialog"
          >
            <X className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center gap-3 p-12 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
            <span className="text-sm">Loading settings…</span>
          </div>
        )}
        {isError && (
          <div className="flex items-center justify-center gap-3 p-12 text-destructive">
            <AlertCircle className="h-5 w-5" aria-hidden="true" />
            <span className="text-sm">Failed to load export settings</span>
          </div>
        )}
        {data && (
          <ExportForm
            documentId={documentId}
            initial={data}
            onCancel={() => onOpenChange(false)}
            onDone={() => onOpenChange(false)}
          />
        )}
      </div>
    </div>
  );
}

interface ExportFormProps {
  documentId: string;
  initial: ExportSettings;
  onCancel: () => void;
  onDone: () => void;
}

function ExportForm({ documentId, initial, onCancel, onDone }: ExportFormProps) {
  const queryClient = useQueryClient();
  const [values, setValues] = useState<ExportSettings>(initial);
  const [tab, setTab] = useState<TabId>("document");

  const { mutate: save, isPending } = useMutation({
    mutationFn: () => api.documents.saveExportSettings(documentId, values),
    onSuccess: (saved) => {
      queryClient.setQueryData(["export-settings", documentId], saved);
      window.location.assign(api.documents.exportUrl(documentId));
      onDone();
    },
    onError: (err: Error) => toast.error(err.message ?? "Failed to save export settings"),
  });

  function setText(key: TextKey, value: string) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function field(key: TextKey, label: string, type: "text" | "date" = "text") {
    return (
      <Field key={key} label={label}>
        <input
          type={type}
          value={values[key]}
          onChange={(e) => setText(key, e.target.value)}
          className="hem-input"
        />
      </Field>
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    save();
  }

  return (
    <form onSubmit={handleSubmit} className="flex min-h-0 flex-col">
      <div role="tablist" aria-label="Export settings" className="flex shrink-0 border-b-2 border-border px-[18px] pt-3">
        {TABS.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            role="tab"
            id={`export-tab-${id}`}
            aria-selected={tab === id}
            aria-controls={`export-panel-${id}`}
            onClick={() => setTab(id)}
            className={cn(
              "hem-label -mb-0.5 border-b-2 px-3 py-2 transition-colors",
              tab === id
                ? "border-primary text-deep dark:text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {/* The Document panel always sets the height; the table panels overlay it and scroll,
          so switching tabs never resizes the dialog. */}
      <div className="relative flex min-h-0 flex-1 flex-col">
        <div
          role="tabpanel"
          id="export-panel-document"
          aria-labelledby="export-tab-document"
          inert={tab !== "document"}
          className={cn("min-h-0 flex-1 overflow-y-auto p-[18px]", tab !== "document" && "invisible")}
        >
          <div className="space-y-5">
            <Section title="Header">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {field("client", "Client")}
                {field("project", "Project")}
                {field("reference", "Reference")}
                {field("edition", "Edition")}
                {field("date", "Date", "date")}
                {field("subject", "Matrix subject")}
              </div>
              {field("subtitle", "Subtitle")}
            </Section>

            <Section title="Classification">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <fieldset>
                  <legend className="hem-label mb-1.5 text-muted-foreground">Document classification</legend>
                  <div className="flex flex-col gap-1.5">
                    {CLASSIFICATIONS.map(({ value, label }) => (
                      <label key={label} className="flex cursor-pointer items-center gap-2 text-[13px]">
                        <input
                          type="radio"
                          name="classification"
                          checked={values.classification === value}
                          onChange={() => setValues((c) => ({ ...c, classification: value }))}
                          className="accent-[hsl(var(--primary))]"
                        />
                        {label}
                      </label>
                    ))}
                  </div>
                </fieldset>
                <Field label="Export control status">
                  <select
                    value={values.export_control}
                    onChange={(e) => setValues((c) => ({ ...c, export_control: e.target.value as ExportControl }))}
                    className="hem-input"
                  >
                    {EXPORT_CONTROLS.map(({ value, label }) => (
                      <option key={label} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
            </Section>

            <Section title="Signatories">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {field("quality_manager", "Quality Manager")}
                {field("project_manager", "Project Manager")}
                {field("redactor", "Redaction")}
              </div>
            </Section>

            <Section title="Revision">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {field("doc_type", "Document type")}
                {field("author", "Author")}
              </div>
              {field("revision_description", "Description of the modifications")}
            </Section>
          </div>
        </div>

        {tab !== "document" && (
          <div
            role="tabpanel"
            id={`export-panel-${tab}`}
            aria-labelledby={`export-tab-${tab}`}
            className="absolute inset-0 overflow-y-auto bg-card p-[18px]"
          >
        {tab === "applicable" && (
          <RowsEditor
            label="Applicable document"
            rows={values.applicable_docs}
            columns={[
              { key: "title", label: "Title" },
              { key: "reference", label: "Reference" },
              { key: "edition", label: "Edition", narrow: true },
            ]}
            empty={{ title: "", reference: "", edition: "" }}
            onChange={(rows) => setValues((c) => ({ ...c, applicable_docs: rows }))}
          />
        )}
        {tab === "reference" && (
          <RowsEditor
            label="Reference document"
            rows={values.reference_docs}
            columns={[
              { key: "title", label: "Title" },
              { key: "reference", label: "Reference" },
              { key: "edition", label: "Edition", narrow: true },
            ]}
            empty={{ title: "", reference: "", edition: "" }}
            onChange={(rows) => setValues((c) => ({ ...c, reference_docs: rows }))}
          />
        )}
        {tab === "acronyms" && (
          <RowsEditor
            label="Acronym"
            rows={values.acronyms}
            columns={[
              { key: "acronym", label: "Acronym", narrow: true },
              { key: "description", label: "Description" },
            ]}
            empty={{ acronym: "", description: "" }}
            onChange={(rows) => setValues((c) => ({ ...c, acronyms: rows }))}
          />
        )}
          </div>
        )}
      </div>

      <div className="flex shrink-0 items-center justify-between gap-2 border-t border-border p-3">
        <p className="text-xs text-muted-foreground">
          Empty fields keep the placeholder of the template. Values are saved with the document.
        </p>
        <div className="flex gap-2">
          <button type="button" onClick={onCancel} disabled={isPending} className="hem-btn hem-btn-ghost">
            Cancel
          </button>
          <button type="submit" disabled={isPending} className="hem-btn hem-btn-primary">
            {isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            ) : (
              <Download className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            Export
          </button>
        </div>
      </div>
    </form>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h3 className="hem-eyebrow border-b border-border pb-1">{title}</h3>
      {children}
    </section>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="hem-label text-muted-foreground">{label}</span>
      {children}
    </label>
  );
}

interface RowsEditorProps<T extends object> {
  label: string;
  rows: T[];
  columns: { key: keyof T & string; label: string; narrow?: boolean }[];
  empty: T;
  onChange: (rows: T[]) => void;
}

/** Editable table: one input per cell, add and remove rows. */
function RowsEditor<T extends object>({
  label,
  rows,
  columns,
  empty,
  onChange,
}: RowsEditorProps<T>) {
  function update(index: number, key: keyof T & string, value: string) {
    onChange(rows.map((row, i) => (i === index ? { ...row, [key]: value } : row)));
  }

  return (
    <div className="space-y-3">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="bg-deep">
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={cn("hem-label px-2 py-2 text-left text-deep-foreground", column.narrow && "w-36")}
              >
                {column.label}
              </th>
            ))}
            <th scope="col" className="w-10">
              <span className="sr-only">Remove</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td colSpan={columns.length + 1} className="border border-border p-4 text-center text-xs text-muted-foreground">
                No entry. The template rows stay empty.
              </td>
            </tr>
          )}
          {rows.map((row, index) => (
            <tr key={index} className="border-b border-border">
              {columns.map((column) => (
                <td key={column.key} className="p-1">
                  <input
                    value={String(row[column.key])}
                    onChange={(e) => update(index, column.key, e.target.value)}
                    aria-label={`${label} ${index + 1} — ${column.label}`}
                    className="hem-input"
                  />
                </td>
              ))}
              <td className="p-1 text-center">
                <button
                  type="button"
                  onClick={() => onChange(rows.filter((_, i) => i !== index))}
                  aria-label={`Remove ${label.toLowerCase()} ${index + 1}`}
                  className="p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button type="button" onClick={() => onChange([...rows, { ...empty }])} className="hem-btn hem-btn-ghost">
        <Plus className="h-3.5 w-3.5" aria-hidden="true" />
        Add {label.toLowerCase()}
      </button>
    </div>
  );
}
