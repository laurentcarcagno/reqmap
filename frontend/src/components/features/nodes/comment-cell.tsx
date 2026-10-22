"use client";

interface CommentCellProps {
  value: string;
  onSave: (comment: string) => void;
}

/** Free-text justification, saved when the field loses focus and the text changed. */
export function CommentCell({ value, onSave }: CommentCellProps) {
  return (
    <textarea
      key={value}
      defaultValue={value}
      rows={2}
      aria-label="Comment / Justification"
      placeholder="Comment / Justification"
      maxLength={5000}
      onBlur={(e) => {
        if (e.target.value !== value) onSave(e.target.value);
      }}
      className="hem-input min-h-[2.5rem] resize-y text-xs"
    />
  );
}
