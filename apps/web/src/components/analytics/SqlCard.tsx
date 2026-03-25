"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function SqlCard({ sql }: { sql: string }) {
  const [copied, setCopied] = React.useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {
      // Clipboard can fail in some browser contexts; keep UX simple.
      setCopied(false);
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <CardTitle className="text-base">SQL query</CardTitle>
        <Button variant="outline" size="sm" onClick={copy}>
          {copied ? "Copied" : "Copy SQL"}
        </Button>
      </CardHeader>
      <CardContent className="pt-0">
        <pre className="overflow-auto rounded-lg bg-muted p-3 text-xs leading-relaxed">
          <code>{sql}</code>
        </pre>
      </CardContent>
    </Card>
  );
}

