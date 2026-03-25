"use client";

import * as React from "react";

import type { AnalysisParameterInfo } from "@/types/analytics";
import { cn } from "@/lib/utils";

function isoDate(d: Date) {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function getSuggestedDefaultValue(paramName: string): string | number {
  const now = new Date();
  const end = isoDate(now);
  const start = isoDate(new Date(now.getTime() - 60 * 24 * 60 * 60 * 1000));

  if (paramName === "start_date") return start;
  if (paramName === "end_date") return end;
  if (paramName === "as_of_date") return end;
  if (paramName === "top_n") return 10;
  if (paramName === "margin_threshold") return 0.35;
  if (paramName === "volume_threshold") return 100;
  if (paramName === "return_rate_threshold") return 0.07;
  return "";
}

function isDateParam(name: string) {
  return name.includes("date") || name.endsWith("_date");
}

function isIdParam(name: string) {
  return name.endsWith("_id");
}

function isThresholdParam(name: string) {
  return name.includes("threshold") || name.includes("rate") || name.includes("margin");
}

export function ParameterForm({
  parameters,
  values,
  onValuesChange,
  useBackendDefaults,
  onUseBackendDefaultsChange,
}: {
  parameters: AnalysisParameterInfo[];
  values: Record<string, unknown>;
  onValuesChange: (next: Record<string, unknown>) => void;
  useBackendDefaults: boolean;
  onUseBackendDefaultsChange: (next: boolean) => void;
}) {
  function handleChange(name: string, raw: string) {
    const trimmed = raw.trim();
    const next = { ...values };

    if (!trimmed) {
      delete next[name];
      onValuesChange(next);
      return;
    }

    if (isIdParam(name) || name === "top_n") {
      const n = Number(trimmed);
      if (!Number.isFinite(n)) return;
      next[name] = n;
      onValuesChange(next);
      return;
    }

    if (isThresholdParam(name)) {
      const n = Number(trimmed);
      if (!Number.isFinite(n)) return;
      next[name] = n;
      onValuesChange(next);
      return;
    }

    // Dates stay as YYYY-MM-DD strings.
    next[name] = trimmed;
    onValuesChange(next);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="text-sm font-medium">Parameters</div>
          <div className="text-xs text-muted-foreground">
            When enabled, the backend will apply sensible defaults.
          </div>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={useBackendDefaults}
            onChange={(e) => onUseBackendDefaultsChange(e.target.checked)}
          />
          Use backend defaults
        </label>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {parameters.map((p) => {
          const suggested = getSuggestedDefaultValue(p.name);
          const current = values[p.name];
          const disabled = useBackendDefaults;

          let placeholder: string | number = suggested;
          const valueStr =
            typeof current === "string" ? current : typeof current === "number" ? String(current) : "";

          return (
            <div key={p.name} className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">
                {p.name}
                {!p.required ? (
                  <span className="ml-2 font-normal text-muted-foreground/80">(optional)</span>
                ) : null}
              </label>

              {isDateParam(p.name) ? (
                <input
                  type="date"
                  className={cn(
                    "h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60",
                  )}
                  placeholder={String(placeholder)}
                  value={typeof current === "string" ? valueStr : ""}
                  disabled={disabled}
                  onChange={(e) => handleChange(p.name, e.target.value)}
                />
              ) : (
                <input
                  type="number"
                  step={isThresholdParam(p.name) ? 0.01 : 1}
                  className={cn(
                    "h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60",
                  )}
                  placeholder={String(placeholder)}
                  value={typeof current === "number" ? valueStr : ""}
                  disabled={disabled}
                  onChange={(e) => handleChange(p.name, e.target.value)}
                />
              )}

              {p.description ? <div className="text-xs text-muted-foreground">{p.description}</div> : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}

