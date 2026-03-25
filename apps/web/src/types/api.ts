export type QueryRequest = {
  question: string;
  context?: {
    timezone?: string;
    currency?: string;
    top_k?: number;
  };
  max_rows?: number;
};

export type QueryResponse = {
  sql: string;
  result: {
    columns: string[];
    rows: any[][];
  };
  business_explanation: string;
  recommended_actions: string[];
  meta?: {
    row_count: number;
    execution_ms: number;
  };
};

