import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageContainer } from "@/components/layout/PageContainer";

export default function Page() {
  return (
    <PageContainer>
      <div className="py-10 sm:py-14">
        <div className="max-w-3xl">
          <h1 className="text-3xl font-semibold tracking-tight">About</h1>
          <p className="mt-3 text-muted-foreground">
            Retail Decision Copilot is a SQL-first analytics assistant designed for retail business analysts.
            It turns natural-language questions into safe, read-only SQL and returns the query, results, and
            business-ready recommendations.
          </p>

          <div className="mt-8 grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl">Built for production habits</CardTitle>
                <CardDescription>Clarity, safety, and maintainability.</CardDescription>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                <ul className="space-y-2">
                  <li>Strict SQL guardrails (SELECT-only)</li>
                  <li>Allowlisted schema validation</li>
                  <li>Row caps and statement timeouts</li>
                  <li>Typed API contracts</li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-xl">Tech stack</CardTitle>
                <CardDescription>Frontend + backend separated cleanly.</CardDescription>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                <ul className="space-y-2">
                  <li>Next.js (App Router) + TypeScript</li>
                  <li>Tailwind CSS + shadcn/ui</li>
                  <li>FastAPI + SQLAlchemy + Alembic</li>
                  <li>PostgreSQL + Neon (hosting)</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}

