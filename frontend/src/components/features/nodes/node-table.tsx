"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, AlertCircle, ChevronsDownUp, ChevronsUpDown } from "lucide-react";
import { toast } from "sonner";
import { api, type Node, type ApplicabilityValue, type ConformityValue } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ApplicabilitySelect } from "./applicability-select";
import { ConformitySelect } from "./conformity-select";
import { DescriptionCell } from "./description-cell";

interface NodeTableProps {
  documentId: string;
}

export function NodeTable({ documentId }: NodeTableProps) {
  const queryClient = useQueryClient();
  const [expandAll, setExpandAll] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["nodes", documentId],
    queryFn: () => api.nodes.list(documentId, { limit: 500 }),
    enabled: !!documentId,
  });

  const { mutate: updateNode } = useMutation({
    mutationFn: ({
      nodeId,
      patch,
    }: {
      nodeId: string;
      patch: { applicability?: ApplicabilityValue; conformity?: ConformityValue };
    }) => api.nodes.update(nodeId, patch),
    onMutate: async ({ nodeId, patch }) => {
      await queryClient.cancelQueries({ queryKey: ["nodes", documentId] });
      const previous = queryClient.getQueryData(["nodes", documentId]);
      queryClient.setQueryData(["nodes", documentId], (old: typeof data) => {
        if (!old) return old;
        return {
          ...old,
          data: old.data.map((n: Node) =>
            n.id === nodeId ? { ...n, ...patch } : n,
          ),
        };
      });
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["nodes", documentId], context.previous);
      }
      toast.error("Failed to update node");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["nodes", documentId] });
    },
  });

  const nodes = data?.data ?? [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12 gap-3 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
        <span className="text-sm">Loading nodes…</span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center p-12 gap-3 text-destructive">
        <AlertCircle className="h-5 w-5" aria-hidden="true" />
        <span className="text-sm">Failed to load nodes</span>
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div className="flex items-center justify-center p-12 text-muted-foreground">
        <span className="text-sm">No nodes found</span>
      </div>
    );
  }

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full border-collapse text-sm" aria-label="Requirement nodes">
        <thead>
          <tr className="border-b border-border bg-deep">
            <th scope="col" className="hem-label sticky top-0 bg-deep px-3 py-2.5 text-left text-deep-foreground w-12">
              #
            </th>
            <th scope="col" className="hem-label sticky top-0 bg-deep px-3 py-2.5 text-left text-deep-foreground w-28">
              ID / Section
            </th>
            <th scope="col" className="hem-label sticky top-0 bg-deep px-3 py-2.5 text-left text-deep-foreground">
              Title
            </th>
            <th scope="col" className="hem-label sticky top-0 bg-deep px-3 py-2.5 text-left text-deep-foreground w-full hidden lg:table-cell">
              <div className="flex items-center gap-1.5">
                <span>Description</span>
                <button
                  type="button"
                  onClick={() => setExpandAll((v) => !v)}
                  className="inline-flex items-center gap-1 px-1 py-0.5 text-[10px] text-deep-foreground/70 hover:bg-white/10 hover:text-deep-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring transition-colors"
                  aria-label={expandAll ? "Collapse all descriptions" : "Expand all descriptions"}
                  title={expandAll ? "Collapse all" : "Expand all"}
                >
                  {expandAll
                    ? <><ChevronsDownUp className="h-3 w-3" aria-hidden="true" /><span>Collapse all</span></>
                    : <><ChevronsUpDown className="h-3 w-3" aria-hidden="true" /><span>Expand all</span></>}
                </button>
              </div>
            </th>
            <th scope="col" className="hem-label sticky top-0 bg-deep px-3 py-2.5 text-left text-deep-foreground w-28">
              Applicability
            </th>
            <th scope="col" className="hem-label sticky top-0 bg-deep px-3 py-2.5 text-left text-deep-foreground w-32">
              Conformity
            </th>
          </tr>
        </thead>
        <tbody>
          {nodes.map((node) => (
            <tr
              key={node.id}
              className={cn(
                "border-b border-border transition-colors",
                node.type === "title"
                  ? "bg-selection/60 hover:bg-selection font-medium"
                  : "hover:bg-accent",
              )}
            >
              <td className="px-3 py-2 font-mono text-muted-foreground">{node.order}</td>
              <td className="px-3 py-2">
                {node.type === "title" ? (
                  <span className="font-mono text-xs text-muted-foreground">{node.section}</span>
                ) : (
                  <span className="font-mono text-xs text-deep dark:text-foreground">{node.req_id}</span>
                )}
              </td>
              <td className="px-3 py-2 whitespace-nowrap">
                <span
                  className={cn(
                    node.type === "title"
                      ? "font-semibold text-foreground"
                      : "text-foreground",
                  )}
                >
                  {node.title}
                </span>
              </td>
              <td className="px-3 py-2 hidden lg:table-cell">
                <DescriptionCell text={node.description} expandAll={expandAll} />
              </td>
              <td className="px-3 py-2">
                <ApplicabilitySelect
                  value={node.applicability}
                  onChange={(v) => updateNode({ nodeId: node.id, patch: { applicability: v } })}
                />
              </td>
              <td className="px-3 py-2">
                <ConformitySelect
                  value={node.conformity}
                  onChange={(v) => updateNode({ nodeId: node.id, patch: { conformity: v } })}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
