import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PageContainer } from "@/components/layout/PageContainer";

export default function Page() {
  return (
    <PageContainer>
      <div className="py-10 sm:py-14">
        <div className="max-w-4xl">
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Analyst chat</CardTitle>
              <CardDescription>
                Placeholder route for the SQL-first chat experience. The backend + guardrails will be
                connected in a later phase.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="rounded-lg border bg-background p-4">
                <div className="text-sm font-medium">Try a question (coming soon)</div>
                <div className="mt-2 grid gap-2 sm:grid-cols-2">
                  <div className="rounded-md border bg-background px-3 py-2 text-sm text-muted-foreground">
                    Top categories by margin
                  </div>
                  <div className="rounded-md border bg-background px-3 py-2 text-sm text-muted-foreground">
                    Sales trend by week
                  </div>
                  <div className="rounded-md border bg-background px-3 py-2 text-sm text-muted-foreground">
                    Store performance (revenue)
                  </div>
                  <div className="rounded-md border bg-background px-3 py-2 text-sm text-muted-foreground">
                    Impact of discounts
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                <Input disabled placeholder="Type your question here..." />
              </div>
              <div className="text-xs text-muted-foreground">
                Next phase: send the question to `POST /query`, receive the SQL + results, then render
                them in a structured assistant turn.
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </PageContainer>
  );
}

