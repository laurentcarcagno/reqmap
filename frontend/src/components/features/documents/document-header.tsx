"use client";

import { useMemo, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { User, Building2, BookOpen, Tag, Download } from "lucide-react";
import type { Node, Document } from "@/lib/api";
import { ExportDialog } from "@/components/features/export/export-dialog";

interface DocumentHeaderProps {
  document: Document;
  nodes: Node[];
}

const CONFORMITY_COLORS: Record<string, string> = {
  C: "#1F8A4C",
  "C TBC": "#65BD86",
  PC: "#C68A00",
  NC: "#BA1A1A",
  TBC: "#73777D",
  NA: "#C2DDF0",
  T: "#006EB1",
};

interface MetaItemProps {
  icon: React.ReactNode;
  label: string;
  value: string | null | undefined;
}

function MetaItem({ icon, label, value }: MetaItemProps) {
  if (!value) return null;
  return (
    <div className="flex items-center gap-1.5 text-xs text-muted-foreground min-w-0">
      <span className="shrink-0 text-muted-foreground/60">{icon}</span>
      <span className="text-muted-foreground/60 shrink-0">{label}:</span>
      <span className="font-mono font-medium text-foreground truncate" title={value}>{value}</span>
    </div>
  );
}

export function DocumentHeader({ document, nodes }: DocumentHeaderProps) {
  const [exportOpen, setExportOpen] = useState(false);
  const pieData = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const node of nodes) {
      if (node.type !== "requirement") continue;
      counts[node.conformity] = (counts[node.conformity] ?? 0) + 1;
    }
    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);
  }, [nodes]);

  const totalReqs = pieData.reduce((s, d) => s + d.value, 0);
  const hasMetadata = document.doc_title || document.doc_reference || document.doc_author || document.doc_company;

  return (
    <div className="border-b border-border bg-card px-4 py-3">
      <div className="grid grid-cols-[1fr_auto_1fr] items-start gap-6">
        {/* Left: doc metadata */}
        <div className="min-w-0 space-y-1.5">
          {document.doc_title ? (
            <h2 className="text-[18px] font-medium tracking-[0.04em] text-deep dark:text-foreground leading-tight" title={document.doc_title}>
              {document.doc_title}
            </h2>
          ) : (
            <h2 className="text-[18px] font-medium tracking-[0.04em] text-deep dark:text-foreground leading-tight truncate" title={document.original_filename}>
              {document.original_filename}
            </h2>
          )}
          {hasMetadata && (
            <div className="flex flex-wrap gap-x-4 gap-y-1">
              <MetaItem icon={<Tag className="h-3 w-3" />} label="Ref" value={document.doc_reference} />
              <MetaItem icon={<User className="h-3 w-3" />} label="Author" value={document.doc_author} />
              <MetaItem icon={<Building2 className="h-3 w-3" />} label="Company" value={document.doc_company} />
            </div>
          )}
          {document.status === "completed" && (
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <BookOpen className="h-3 w-3" aria-hidden="true" />
                {document.title_count} titles
              </span>
              <span>·</span>
              <span>{document.requirement_count} requirements</span>
            </div>
          )}
          {document.status === "completed" && (
            <>
              <button
                type="button"
                onClick={() => setExportOpen(true)}
                className="hem-btn hem-btn-ghost"
                aria-label="Export as Excel compliance matrix"
              >
                <Download className="h-3.5 w-3.5" aria-hidden="true" />
                Export
              </button>
              <ExportDialog documentId={document.id} open={exportOpen} onOpenChange={setExportOpen} />
            </>
          )}
        </div>

        {/* Center: conformity pie (the empty third column keeps it centered) */}
        <div className="flex justify-center">
        {totalReqs > 0 && (
          <div className="shrink-0 flex items-center gap-3">
            <div className="w-28 h-24">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={22}
                    outerRadius={40}
                    paddingAngle={2}
                    dataKey="value"
                    aria-label="Conformity distribution"
                  >
                    {pieData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={CONFORMITY_COLORS[entry.name] ?? "#73777D"}
                        stroke="transparent"
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value) => {
                      const n = typeof value === "number" ? value : 0;
                      return [`${n} (${Math.round((n / totalReqs) * 100)}%)`, ""];
                    }}
                    contentStyle={{
                      fontSize: 11,
                      padding: "4px 8px",
                      borderRadius: 0,
                      border: "1px solid hsl(var(--border))",
                      background: "hsl(var(--card))",
                      color: "hsl(var(--card-foreground))",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {/* Legend */}
            <div className="flex flex-col gap-0.5">
              {pieData.map((entry) => (
                <div key={entry.name} className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                  <span
                    className="h-2 w-2 shrink-0"
                    style={{ background: CONFORMITY_COLORS[entry.name] ?? "#73777D" }}
                    aria-hidden="true"
                  />
                  <span className="font-mono">{entry.name}</span>
                  <span className="tabular-nums text-foreground font-medium">{entry.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        </div>
        <div aria-hidden="true" />
      </div>
    </div>
  );
}
