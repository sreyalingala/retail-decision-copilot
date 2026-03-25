export type QueryRequest = {
  question: string;
};

export type QueryResponse = {
  question: string;
  selected_analysis_name: string;
  selected_parameters: Record<string, unknown>;
  reasoning_short: string;
  sql: string;
  columns: string[];
  rows: unknown[][];
  metadata: {
    row_count: number;
    execution_time_ms: number;
    error?: string;
  };
  business_explanation: string;
  recommended_actions: string[];
  status: string;
};

