"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ReasoningCard({ reasoningShort }: { reasoningShort: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Routing reasoning</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{reasoningShort}</p>
      </CardContent>
    </Card>
  );
}

