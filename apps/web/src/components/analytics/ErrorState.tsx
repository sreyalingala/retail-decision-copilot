"use client";

import { Card, CardContent } from "@/components/ui/card";

export function ErrorState({ title, message }: { title: string; message?: string }) {
  return (
    <Card>
      <CardContent className="py-8">
        <div className="space-y-2">
          <div className="text-sm font-medium text-foreground">{title}</div>
          {message ? <div className="text-sm text-muted-foreground">{message}</div> : null}
        </div>
      </CardContent>
    </Card>
  );
}

