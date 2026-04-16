"use client";

import type { ConformityValue } from "@/lib/api";
import { cn } from "@/lib/utils";

const CONFORMITY_VALUES: ConformityValue[] = ["NA", "C", "C TBC", "PC", "NC", "TBC", "T"];

const VALUE_STYLES: Record<ConformityValue, string> = {
  NA: "text-muted-foreground",
  C: "text-[hsl(var(--status-completed))]",
  "C TBC": "text-[hsl(var(--status-pending))]",
  PC: "text-[hsl(var(--status-processing))]",
  NC: "text-[hsl(var(--status-failed))]",
  TBC: "text-[hsl(var(--status-pending))]",
  T: "text-muted-foreground",
};

interface ConformitySelectProps {
  value: ConformityValue;
  onChange: (value: ConformityValue) => void;
  disabled?: boolean;
}

export function ConformitySelect({ value, onChange, disabled }: ConformitySelectProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as ConformityValue)}
      disabled={disabled}
      aria-label="Conformity"
      className={cn(
        "rounded border border-transparent bg-transparent px-1.5 py-0.5 text-xs font-medium",
        "hover:border-input hover:bg-background cursor-pointer transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
        "disabled:cursor-not-allowed disabled:opacity-50",
        VALUE_STYLES[value],
      )}
    >
      {CONFORMITY_VALUES.map((v) => (
        <option key={v} value={v}>
          {v}
        </option>
      ))}
    </select>
  );
}
