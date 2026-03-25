"use client";

import * as React from "react";

import type { AnalysisInfo, RunAnalysisResponse } from "@/types/analytics";
import type { QueryResponse } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageContainer } from "@/components/layout/PageContainer";
import { AnalysisSelector } from "@/components/analytics/AnalysisSelector";
import { ErrorState } from "@/components/analytics/ErrorState";
import { EmptyState } from "@/components/analytics/EmptyState";
import { ModeToggle, type WorkspaceMode } from "@/components/analytics/ModeToggle";
import { MetadataCard } from "@/components/analytics/MetadataCard";
import { ParameterForm } from "@/components/analytics/ParameterForm";
import { QueryResponseView } from "@/components/analytics/QueryResponseView";
import { QuestionInput } from "@/components/analytics/QuestionInput";
import { ResultTable } from "@/components/analytics/ResultTable";
import { RunAnalysisButton } from "@/components/analytics/RunAnalysisButton";
import { SqlCard } from "@/components/analytics/SqlCard";
import { askBusinessQuestion, listAnalyses, runAnalysis } from "@/lib/analyticsApi";

function getFeaturedAnalyses() {
  return [
    { name: "revenue_by_month", label: "Revenue by month" },
    { name: "promotion_effectiveness", label: "Promotion effectiveness" },
    { name: "stockout_risk_ranking", label: "Stockout risk ranking" },
    { name: "supplier_delay_analysis", label: "Supplier delay analysis" },
  ];
}

export default function Page() {
  const [mode, setMode] = React.useState<WorkspaceMode>("ai");

  const [analyses, setAnalyses] = React.useState<AnalysisInfo[]>([]);
  const [loadingCatalog, setLoadingCatalog] = React.useState(true);
  const [catalogError, setCatalogError] = React.useState<string | null>(null);

  const [selectedAnalysis, setSelectedAnalysis] = React.useState<string>("revenue_by_month");
  const [useBackendDefaults, setUseBackendDefaults] = React.useState(true);
  const [parameters, setParameters] = React.useState<Record<string, unknown>>({});

  const [running, setRunning] = React.useState(false);
  const [runError, setRunError] = React.useState<string | null>(null);
  const [runResp, setRunResp] = React.useState<RunAnalysisResponse | null>(null);

  const [question, setQuestion] = React.useState(
    "Which categories had the biggest month-over-month revenue decline and what should we do next?",
  );
  const [asking, setAsking] = React.useState(false);
  const [askError, setAskError] = React.useState<string | null>(null);
  const [queryResp, setQueryResp] = React.useState<QueryResponse | null>(null);

  const selectedInfo = React.useMemo(
    () => analyses.find((a) => a.analysis_name === selectedAnalysis) ?? null,
    [analyses, selectedAnalysis],
  );

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoadingCatalog(true);
        const data = await listAnalyses();
        if (!alive) return;
        const list = data.analyses ?? [];
        setAnalyses(list);

        const fallback = list.find((a) => a.analysis_name === "revenue_by_month")
          ? "revenue_by_month"
          : list[0]?.analysis_name;

        if (fallback) setSelectedAnalysis(fallback);
      } catch (e) {
        if (!alive) return;
        setCatalogError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!alive) return;
        setLoadingCatalog(false);
      }
    })();

    return () => {
      alive = false;
    };
  }, []);

  function handleSelect(next: string) {
    setSelectedAnalysis(next);
    setUseBackendDefaults(true);
    setParameters({});
    setRunResp(null);
    setRunError(null);
  }

  async function handleRun() {
    if (!selectedAnalysis) return;
    setRunning(true);
    setRunError(null);

    try {
      const payload = {
        analysis_name: selectedAnalysis,
        parameters: useBackendDefaults ? {} : parameters,
      };
      const out = await runAnalysis(payload);
      setRunResp(out);
    } catch (e) {
      setRunError(e instanceof Error ? e.message : String(e));
      setRunResp(null);
    } finally {
      setRunning(false);
    }
  }

  async function handleAsk() {
    if (!question.trim()) return;
    setAsking(true);
    setAskError(null);
    try {
      const out = await askBusinessQuestion({ question: question.trim() });
      setQueryResp(out);
    } catch (e) {
      setAskError(e instanceof Error ? e.message : String(e));
      setQueryResp(null);
    } finally {
      setAsking(false);
    }
  }

  const featured = getFeaturedAnalyses().filter((f) =>
    analyses.some((a) => a.analysis_name === f.name),
  );
  const samplePrompts = [
    "Which categories have the lowest gross margin but high volume this quarter?",
    "Which suppliers are causing the most delay risk for inventory?",
    "What promotions lifted revenue but hurt margin the most?",
  ];

  return (
    <PageContainer>
      <div className="py-10 sm:py-14">
        <div className="flex flex-col gap-8">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <Badge variant="secondary">SQL analytics</Badge>
              <Badge variant="outline">AI-assisted routing</Badge>
            </div>
            <h1 className="text-3xl font-semibold tracking-tight">Analyst workspace</h1>
            <p className="text-sm text-muted-foreground">
              Ask a natural-language business question or run manual analyst-grade SQL analyses.
              In both modes, you see full SQL transparency and result details.
            </p>
          </div>

          <ModeToggle mode={mode} onChange={setMode} />

          {mode === "ai" ? (
            <div className="grid gap-6 lg:grid-cols-5">
              <div className="lg:col-span-2">
                <QuestionInput
                  value={question}
                  onChange={setQuestion}
                  onSubmit={handleAsk}
                  loading={asking}
                  samplePrompts={samplePrompts}
                  onSelectSample={(p) => setQuestion(p)}
                />
              </div>
              <div className="lg:col-span-3 space-y-4">
                {askError ? <ErrorState title="Question failed" message={askError} /> : null}
                {queryResp ? (
                  <QueryResponseView response={queryResp} />
                ) : (
                  <EmptyState
                    title="No AI response yet"
                    description="Ask a natural-language business question to see routed analysis, SQL, results, explanation, and actions."
                  />
                )}
              </div>
            </div>
          ) : (
            <div className="grid gap-6 lg:grid-cols-5">
              <div className="lg:col-span-2 space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Analysis catalog</CardTitle>
                    <CardDescription>Select a predefined analytics query.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {loadingCatalog ? (
                      <div className="text-sm text-muted-foreground">Loading available analyses...</div>
                    ) : catalogError ? (
                      <ErrorState title="Failed to load analyses" message={catalogError} />
                    ) : analyses.length === 0 ? (
                      <EmptyState
                        title="No analyses found"
                        description="The backend catalog is empty."
                      />
                    ) : (
                      <AnalysisSelector analyses={analyses} value={selectedAnalysis} onChange={handleSelect} />
                    )}

                    {featured.length > 0 ? (
                      <div className="space-y-2">
                        <div className="text-xs font-medium text-muted-foreground">
                          Featured analyses
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {featured.map((f) => (
                            <Button
                              key={f.name}
                              variant={f.name === selectedAnalysis ? "default" : "outline"}
                              size="sm"
                              onClick={() => handleSelect(f.name)}
                            >
                              {f.label}
                            </Button>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </CardContent>
                </Card>
              </div>

              <div className="lg:col-span-3 space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Run an analysis</CardTitle>
                    <CardDescription>
                      Parameters are optional because the backend applies sensible defaults.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-5">
                    {selectedInfo ? (
                      <div className="space-y-2">
                        <div className="text-sm font-medium">{selectedInfo.analysis_name}</div>
                        <div className="text-sm text-muted-foreground">{selectedInfo.short_description}</div>
                      </div>
                    ) : null}

                    <div className="rounded-lg border bg-background p-4">
                      {selectedInfo ? (
                        <ParameterForm
                          parameters={selectedInfo.parameters}
                          values={parameters}
                          onValuesChange={setParameters}
                          useBackendDefaults={useBackendDefaults}
                          onUseBackendDefaultsChange={(next) => {
                            setUseBackendDefaults(next);
                            if (next) setParameters({});
                          }}
                        />
                      ) : (
                        <div className="text-sm text-muted-foreground">Select an analysis to see parameters.</div>
                      )}
                    </div>

                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <div className="text-xs text-muted-foreground">
                        Manual mode is useful to demo deterministic SQL analytics.
                      </div>
                      <RunAnalysisButton onClick={handleRun} loading={running} disabled={!selectedAnalysis || loadingCatalog} />
                    </div>

                    {runError ? <ErrorState title="Analysis failed" message={runError} /> : null}
                  </CardContent>
                </Card>

                {runResp ? (
                  <div className="space-y-4">
                    <div className="space-y-1">
                      <div className="text-sm text-muted-foreground">Selected analysis</div>
                      <div className="text-xl font-semibold tracking-tight">{runResp.analysis_name}</div>
                    </div>

                    <SqlCard sql={runResp.sql} />

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Result</CardTitle>
                        <CardDescription>
                          Returned as a capped, scrollable table for analyst review.
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ResultTable columns={runResp.columns} rows={runResp.rows} />
                      </CardContent>
                    </Card>

                    <MetadataCard
                      rowCount={runResp.metadata.row_count}
                      executionTimeMs={runResp.metadata.execution_time_ms}
                    />
                  </div>
                ) : (
                  <EmptyState
                    title="No manual analysis run yet"
                    description="Select an analysis and click “Run analysis” to view the SQL and results."
                  />
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </PageContainer>
  );
}

