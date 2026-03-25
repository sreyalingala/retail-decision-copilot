"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";

export function RunAnalysisButton({
  disabled,
  onClick,
  loading,
}: {
  disabled?: boolean;
  onClick: () => void;
  loading?: boolean;
}) {
  return (
    <Button onClick={onClick} disabled={disabled || loading} className="min-w-[160px]">
      {loading ? "Running..." : "Run analysis"}
    </Button>
  );
}

