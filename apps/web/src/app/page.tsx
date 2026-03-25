import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageContainer } from "@/components/layout/PageContainer";

export default function Page() {
  return (
    <PageContainer>
      <div className="py-10 sm:py-14">
        <div className="max-w-3xl">
          <div className="flex items-center gap-3">
            <Badge variant="secondary">SQL-first</Badge>
            <Badge variant="outline">Read-only guardrails</Badge>
          </div>

          <h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl">
            Retail Decision Copilot
          </h1>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground sm:text-lg">
            Ask retail questions in natural language. The system routes to a vetted SQL analysis,
            runs it on PostgreSQL, and returns transparent SQL, results, business explanation,
            and recommended actions.
          </p>

          <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Button asChild size="lg">
              <Link href="/app">Open analyst chat</Link>
            </Button>
            <div className="text-sm text-muted-foreground">
              Includes both AI-assisted question mode and manual analyst mode.
            </div>
          </div>
        </div>

        <div className="mt-10 grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">How it works</CardTitle>
              <CardDescription>Designed for business analysts.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
                <li>Ask a question (e.g., “top categories by margin”).</li>
                <li>Generate SELECT-only SQL with schema validation.</li>
                <li>Execute safely and return results + explanation.</li>
              </ol>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Safety & transparency</CardTitle>
              <CardDescription>Guardrails that keep SQL read-only.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <ul className="space-y-2">
                <li>Allow only `SELECT` queries.</li>
                <li>Validate referenced tables and columns.</li>
                <li>Block destructive/multi-statement SQL.</li>
                <li>Cap result rows and enforce statement timeouts.</li>
              </ul>
            </CardContent>
          </Card>
        </div>

        <div className="mt-8">
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">What you’ll see in each answer</CardTitle>
              <CardDescription>Every assistant turn is structured.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg border bg-background p-4">
                <div className="text-sm font-medium">1) The SQL query</div>
                <div className="mt-1 text-sm text-muted-foreground">Displayed and copyable for analysts.</div>
              </div>
              <div className="rounded-lg border bg-background p-4">
                <div className="text-sm font-medium">2) The result</div>
                <div className="mt-1 text-sm text-muted-foreground">Returned as a capped table.</div>
              </div>
              <div className="rounded-lg border bg-background p-4">
                <div className="text-sm font-medium">3) Business explanation</div>
                <div className="mt-1 text-sm text-muted-foreground">Credible narrative tied to the metrics.</div>
              </div>
              <div className="rounded-lg border bg-background p-4">
                <div className="text-sm font-medium">4) Recommended actions</div>
                <div className="mt-1 text-sm text-muted-foreground">Practical next steps for ops/merch.</div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </PageContainer>
  );
}

