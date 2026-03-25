import type {
  ListAnalysesResponse,
  RunAnalysisRequest,
  RunAnalysisResponse,
} from "@/types/analytics";

function getApiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
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

