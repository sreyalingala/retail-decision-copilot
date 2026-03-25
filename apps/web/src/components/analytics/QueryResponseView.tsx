"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MetadataCard } from "@/components/analytics/MetadataCard";
import { RecommendedActionsCard } from "@/components/analytics/RecommendedActionsCard";
import { ReasoningCard } from "@/components/analytics/ReasoningCard";
import { ResultTable } from "@/components/analytics/ResultTable";
import { SelectedAnalysisCard } from "@/components/analytics/SelectedAnalysisCard";
import { SqlCard } from "@/components/analytics/SqlCard";
import type { QueryResponse } from "@/types/api";

export function QueryResponseView({ response }: { response: QueryResponse }) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Original question</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{response.question}</p>
        </CardContent>
      </Card>

      <SelectedAnalysisCard
        analysisName={response.selected_analysis_name}
        parameters={response.selected_parameters}
      />
      <ReasoningCard reasoningShort={response.reasoning_short} />
      <SqlCard sql={response.sql} />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Result</CardTitle>
        </CardHeader>
        <CardContent>
          <ResultTable columns={response.columns} rows={response.rows} />
        </CardContent>
      </Card>

      <MetadataCard
        rowCount={response.metadata.row_count}
        executionTimeMs={response.metadata.execution_time_ms}
      />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Business explanation</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{response.business_explanation}</p>
        </CardContent>
      </Card>

      <RecommendedActionsCard actions={response.recommended_actions} />
    </div>
  );
}

