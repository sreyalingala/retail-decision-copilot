export type AnalysisParameterInfo = {
  name: string;
  required: boolean;
  description: string;
};

export type AnalysisInfo = {
  analysis_name: string;
  short_description: string;
  parameters: AnalysisParameterInfo[];
};

export type ListAnalysesResponse = {
  analyses: AnalysisInfo[];
};

export type RunAnalysisRequest = {
  analysis_name: string;
  parameters?: Record<string, unknown>;
  max_rows?: number;
};

export type RunAnalysisResponse = {
  analysis_name: string;
  sql: string;
  columns: string[];
  rows: unknown[][];
  metadata: {
    row_count: number;
    execution_time_ms: number;
  };
};

