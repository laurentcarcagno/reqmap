"use client";

import type { ApplicabilityValue } from "@/lib/api";
import { cn } from "@/lib/utils";

const APPLICABILITY_VALUES: ApplicabilityValue[] = ["NA", "A", "A/M", "TBC", "T"];

const VALUE_STYLES: Record<ApplicabilityValue, string> = {
  NA: "text-muted-foreground",
  A: "text-[hsl(var(--status-completed))]",
  "A/M": "text-[hsl(var(--status-processing))]",
  TBC: "text-[hsl(var(--status-pending))]",
  T: "text-muted-foreground",
};

interface ApplicabilitySelectProps {
  value: ApplicabilityValue;
  onChange: (value: ApplicabilityValue) => void;
  disabled?: boolean;
}

export function ApplicabilitySelect({ value, onChange, disabled }: ApplicabilitySelectProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as ApplicabilityValue)}
      disabled={disabled}
      aria-label="Applicability"
      className={cn(
        "border border-transparent bg-transparent px-1.5 py-0.5 text-xs font-medium",
        "hover:border-input hover:bg-background cursor-pointer transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
        "disabled:cursor-not-allowed disabled:opacity-50",
        VALUE_STYLES[value],
      )}
    >
      {APPLICABILITY_VALUES.map((v) => (
        <option key={v} value={v}>
          {v}
        </option>
      ))}
    </select>
  );
}
