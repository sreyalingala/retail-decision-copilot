"use client";

import * as React from "react";

import type { AnalysisInfo } from "@/types/analytics";

export function AnalysisSelector({
  analyses,
  value,
  onChange,
}: {
  analyses: AnalysisInfo[];
  value: string;
  onChange: (analysisName: string) => void;
}) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-foreground">Select analysis</label>
      <select
        className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm outline-none focus-visible:ring-1 focus-visible:ring-ring"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {analyses.map((a) => (
          <option key={a.analysis_name} value={a.analysis_name}>
            {a.analysis_name}
          </option>
        ))}
      </select>
    </div>
  );
}

