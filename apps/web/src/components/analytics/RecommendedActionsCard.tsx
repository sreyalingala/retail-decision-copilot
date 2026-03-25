"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function RecommendedActionsCard({ actions }: { actions: string[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Recommended actions</CardTitle>
      </CardHeader>
      <CardContent>
        {actions.length === 0 ? (
          <div className="text-sm text-muted-foreground">No recommendations returned.</div>
        ) : (
          <ul className="list-disc space-y-2 pl-5 text-sm text-muted-foreground">
            {actions.map((a, idx) => (
              <li key={`${idx}-${a}`}>{a}</li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

