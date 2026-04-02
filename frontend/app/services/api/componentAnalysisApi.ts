import type { PartObject } from "./types";
import { API_CONFIG } from "./config";
import { mockStartAnalysis } from "./mockImplementations";

export interface ComponentReasoning {
  componentId: string;
  componentName: string;
  reasoning: string;
  status: "reasoning" | "selected" | "validated";
  hierarchyLevel?: number;
}

export interface ComponentSelection {
  componentId: string;
  componentName: string;
  partData: PartObject;
  position?: { x: number; y: number };
}

export interface ComponentAnalysisResponse {
  type: "reasoning" | "selection" | "complete" | "error" | "context_request" | "remove";
  componentId?: string;
  componentName?: string;
  reasoning?: string;
  partData?: ComponentSelection["partData"];
  position?: ComponentSelection["position"];
  message?: string;
  hierarchyLevel?: number;
  queryId?: string;
  requestId?: string;
}

export interface ComponentAnalysisConfig {
  baseUrl: string;
  analysisEndpoint: string;
  timeout?: number;
}

const defaultConfig: ComponentAnalysisConfig = {
  baseUrl: "http://localhost:3001",
  analysisEndpoint: "/api/component-analysis",
  timeout: 60000,
};

async function streamSSE(
  url: string,
  body: Record<string, unknown>,
  onUpdate: (update: ComponentAnalysisResponse) => void,
  signal?: AbortSignal,
  timeout?: number,
): Promise<void> {
  const controller = signal ? undefined : new AbortController();
  const abortSignal = signal || controller?.signal;
  const timeoutId = timeout ? setTimeout(() => controller?.abort(), timeout) : null;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: abortSignal,
    });

    if (timeoutId) clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text().catch(() => "Unknown error");
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    if (!reader) throw new Error("Response body is not readable");

    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      let eventEndIndex;
      while ((eventEndIndex = buffer.indexOf("\n\n")) !== -1) {
        const eventText = buffer.slice(0, eventEndIndex);
        buffer = buffer.slice(eventEndIndex + 2);

        const dataLine = eventText.split("\n").find((line) => line.startsWith("data: "));
        if (dataLine) {
          try {
            const data: ComponentAnalysisResponse = JSON.parse(dataLine.slice(6));
            onUpdate(data);
            if (data.type === "complete" || data.type === "error") return;
          } catch (e) {
            console.error("Failed to parse SSE data:", e);
          }
        }
      }
    }

    if (buffer.trim()) {
      const dataLine = buffer.split("\n").find((line) => line.startsWith("data: "));
      if (dataLine) {
        try {
          const data: ComponentAnalysisResponse = JSON.parse(dataLine.slice(6));
          onUpdate(data);
        } catch (e) {
          console.error("Failed to parse final SSE data:", e);
        }
      }
    }
  } catch (error: any) {
    if (timeoutId) clearTimeout(timeoutId);
    if (error.name === "AbortError") throw new Error("Analysis timeout or cancelled");
    if (error.message?.includes("Failed to fetch") || error.name === "TypeError") {
      throw new Error("Failed to connect to backend. Make sure it is running.");
    }
    throw error;
  }
}

async function realStartAnalysis(
  query: string,
  config: ComponentAnalysisConfig,
  onUpdate: (update: ComponentAnalysisResponse) => void,
  signal?: AbortSignal,
  contextQueryId?: string,
  context?: string
): Promise<void> {
  const body: Record<string, unknown> = { query };
  if (contextQueryId && context) {
    body.contextQueryId = contextQueryId;
    body.context = context;
  }
  return streamSSE(
    `${config.baseUrl}${config.analysisEndpoint}`,
    body,
    onUpdate,
    signal,
    config.timeout,
  );
}

class ComponentAnalysisService {
  private config: ComponentAnalysisConfig;
  private useMock: boolean;
  private currentAnalysis: AbortController | null = null;

  constructor(config?: Partial<ComponentAnalysisConfig>, useMock: boolean = false) {
    this.config = { ...defaultConfig, ...config };
    this.useMock = useMock;
  }

  async startAnalysis(
    query: string,
    onUpdate: (update: ComponentAnalysisResponse) => void,
    signal?: AbortSignal,
    contextQueryId?: string,
    context?: string
  ): Promise<void> {
    if (this.currentAnalysis) this.currentAnalysis.abort();

    const controller = signal ? undefined : new AbortController();
    this.currentAnalysis = controller ?? null;
    const abortSignal = signal || controller?.signal;

    try {
      if (this.useMock) {
        await mockStartAnalysis(query, this.config, onUpdate, abortSignal, contextQueryId, context);
      } else {
        await realStartAnalysis(query, this.config, onUpdate, abortSignal, contextQueryId, context);
      }
    } catch (error: any) {
      if (error.name === "AbortError" || error.message?.includes("cancelled")) {
        onUpdate({ type: "error", message: "Analysis cancelled" });
        return;
      }
      onUpdate({ type: "error", message: error.message || "Analysis failed" });
      throw error;
    } finally {
      if (this.currentAnalysis === controller) this.currentAnalysis = null;
    }
  }

  async startRefinement(
    modification: string,
    currentComponents: Array<{ component_id: string; component_name: string; part_data: Record<string, unknown> }>,
    projectSummary: string,
    onUpdate: (update: ComponentAnalysisResponse) => void,
    signal?: AbortSignal,
  ): Promise<void> {
    if (this.currentAnalysis) this.currentAnalysis.abort();

    const controller = signal ? undefined : new AbortController();
    this.currentAnalysis = controller ?? null;
    const abortSignal = signal || controller?.signal;

    try {
      await streamSSE(
        `${this.config.baseUrl}/api/refine`,
        {
          modification,
          current_components: currentComponents,
          project_summary: projectSummary,
        },
        onUpdate,
        abortSignal,
        this.config.timeout,
      );
    } catch (error: any) {
      if (error.name === "AbortError" || error.message?.includes("cancelled")) {
        onUpdate({ type: "error", message: "Refinement cancelled" });
        return;
      }
      onUpdate({ type: "error", message: error.message || "Refinement failed" });
      throw error;
    } finally {
      if (this.currentAnalysis === controller) this.currentAnalysis = null;
    }
  }

  cancelAnalysis(): void {
    if (this.currentAnalysis) {
      this.currentAnalysis.abort();
      this.currentAnalysis = null;
    }
  }

  updateConfig(config: Partial<ComponentAnalysisConfig>) {
    this.config = { ...this.config, ...config };
  }

  setUseMock(useMock: boolean) {
    this.useMock = useMock;
  }
}

export const componentAnalysisApi = new ComponentAnalysisService(
  { baseUrl: API_CONFIG.baseUrl },
  API_CONFIG.useMock
);

export { ComponentAnalysisService };
