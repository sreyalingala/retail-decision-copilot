"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function QuestionInput({
  value,
  onChange,
  onSubmit,
  loading,
  samplePrompts,
  onSelectSample,
}: {
  value: string;
  onChange: (next: string) => void;
  onSubmit: () => void;
  loading?: boolean;
  samplePrompts: string[];
  onSelectSample: (prompt: string) => void;
}) {
  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      onSubmit();
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Ask a business question</CardTitle>
        <CardDescription>
          Ask in natural language. Use Cmd/Ctrl+Enter to submit quickly.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <textarea
          className="min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm outline-none focus-visible:ring-1 focus-visible:ring-ring"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Example: Which categories had the biggest month-over-month revenue decline and what should we do next?"
        />

        <div className="flex flex-wrap gap-2">
          {samplePrompts.map((p) => (
            <button
              key={p}
              type="button"
              className="rounded-md border px-2 py-1 text-xs text-muted-foreground hover:bg-muted"
              onClick={() => onSelectSample(p)}
            >
              {p}
            </button>
          ))}
        </div>

        <div className="flex items-center justify-end">
          <Button onClick={onSubmit} disabled={loading || !value.trim()}>
            {loading ? "Asking..." : "Ask"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

