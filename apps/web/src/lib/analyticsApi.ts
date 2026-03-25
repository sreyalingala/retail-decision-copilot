import type {
  ListAnalysesResponse,
  RunAnalysisRequest,
  RunAnalysisResponse,
} from "@/types/analytics";
import type { QueryRequest, QueryResponse } from "@/types/api";

function getApiBaseUrl() {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (configured && configured.trim()) {
    return configured.trim().replace(/\/+$/, "");
  }

  if (process.env.NODE_ENV !== "production") {
    return "http://localhost:8000";
  }

  throw new Error(
    "NEXT_PUBLIC_API_BASE_URL is required in production builds.",
  );
}

export async function listAnalyses(): Promise<ListAnalysesResponse> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/analytics`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Failed to list analyses (${res.status}): ${text || res.statusText}`);
  }

  return (await res.json()) as ListAnalysesResponse;
}

export async function runAnalysis(
  payload: RunAnalysisRequest,
): Promise<RunAnalysisResponse> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/analytics/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Failed to run analysis (${res.status}): ${text || res.statusText}`);
  }

  return (await res.json()) as RunAnalysisResponse;
}

export async function askBusinessQuestion(
  payload: QueryRequest,
): Promise<QueryResponse> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Failed to run AI query (${res.status}): ${text || res.statusText}`);
  }

  return (await res.json()) as QueryResponse;
}

