"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function MetadataCard({
  rowCount,
  executionTimeMs,
}: {
  rowCount: number;
  executionTimeMs: number;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Metadata</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm text-muted-foreground">
        <div className="flex items-center justify-between gap-4">
          <span>Rows</span>
          <span className="font-medium text-foreground">{rowCount.toLocaleString()}</span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span>Execution time</span>
          <span className="font-medium text-foreground">{executionTimeMs} ms</span>
        </div>
      </CardContent>
    </Card>
  );
}

