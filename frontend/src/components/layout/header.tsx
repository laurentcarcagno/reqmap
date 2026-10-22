"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

export function Header() {
  const { theme, setTheme } = useTheme();

  return (
    <header className="flex h-16 shrink-0 items-center border-b border-border bg-card px-4 gap-3">
      <div className="flex items-stretch gap-3.5 py-3">
        <div className="hem-stripe" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <div className="flex flex-col justify-center">
          <span className="hem-eyebrow hidden sm:block">Requirements Extraction</span>
          <h1 className="text-[18px] font-semibold leading-tight tracking-[0.04em] text-deep dark:text-foreground">
            REQMAP<span className="text-tricolor-red">·</span>
          </h1>
        </div>
      </div>

      <div className="flex-1" />

      <button
        onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        className="hem-btn hem-btn-ghost w-8 px-0"
        aria-label="Toggle theme"
      >
        <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" aria-hidden="true" />
        <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" aria-hidden="true" />
      </button>

    </header>
  );
}
