"use client";

import { Button } from "@/components/ui/button";

export type WorkspaceMode = "ai" | "manual";

export function ModeToggle({
  mode,
  onChange,
}: {
  mode: WorkspaceMode;
  onChange: (next: WorkspaceMode) => void;
}) {
  return (
    <div className="inline-flex rounded-lg border p-1">
      <Button
        size="sm"
        variant={mode === "ai" ? "default" : "ghost"}
        onClick={() => onChange("ai")}
      >
        AI Question mode
      </Button>
      <Button
        size="sm"
        variant={mode === "manual" ? "default" : "ghost"}
        onClick={() => onChange("manual")}
      >
        Manual Analysis mode
      </Button>
    </div>
  );
}

