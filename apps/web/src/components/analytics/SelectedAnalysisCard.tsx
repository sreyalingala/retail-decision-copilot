"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function formatValue(value: unknown) {
  if (value === null) return "null";
  if (value === undefined) return "undefined";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function SelectedAnalysisCard({
  analysisName,
  parameters,
}: {
  analysisName: string;
  parameters: Record<string, unknown>;
}) {
  const entries = Object.entries(parameters ?? {});

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Selected analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-sm">
          <span className="text-muted-foreground">analysis_name:</span>{" "}
          <span className="font-medium">{analysisName}</span>
        </div>
        <div className="space-y-2">
          <div className="text-xs font-medium text-muted-foreground">Parameters</div>
          {entries.length === 0 ? (
            <div className="text-sm text-muted-foreground">No parameters provided.</div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {entries.map(([k, v]) => (
                <div
                  key={k}
                  className="rounded-md border bg-background px-2 py-1 text-xs"
                >
                  <span className="text-muted-foreground">{k}:</span>{" "}
                  <span className="font-medium">{formatValue(v)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

