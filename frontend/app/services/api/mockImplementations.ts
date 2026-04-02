import { mockComponents, MOCK_CONFIG } from "./mockData";
import type { ComponentAnalysisResponse } from "./componentAnalysisApi";
import type { ComponentAnalysisConfig } from "./componentAnalysisApi";
import type { ChatQueryRequest, ChatQueryResponse, ChatContinueRequest, ChatContinueResponse, ChatApiConfig } from "./chatApi";

// ---- Shared helpers ----

export const waitWithAbort = (duration: number, signal?: AbortSignal): Promise<void> => {
  if (duration <= 0) return Promise.resolve();
  return new Promise<void>((resolve) => {
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    const cleanup = () => {
      if (timeoutId !== null) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }
      signal?.removeEventListener("abort", onAbort);
    };

    const onAbort = () => {
      cleanup();
      resolve();
    };

    if (signal) {
      signal.addEventListener("abort", onAbort, { once: true });
      if (signal.aborted) {
        onAbort();
        return;
      }
    }

    timeoutId = setTimeout(() => {
      cleanup();
      resolve();
    }, duration);
  });
};

// ---- Mock component analysis ----

export async function mockStartAnalysis(
  query: string,
  config: ComponentAnalysisConfig,
  onUpdate: (update: ComponentAnalysisResponse) => void,
  signal?: AbortSignal,
  contextQueryId?: string,
  context?: string
): Promise<void> {
  if (!contextQueryId && Math.random() < 0.1) {
    const testQueryId = `query_${Date.now()}`;
    onUpdate({
      type: "context_request",
      queryId: testQueryId,
      message: "I need more information about your power requirements. What is your target voltage range?",
    });
    return;
  }

  for (let i = 0; i < mockComponents.length; i++) {
    if (signal?.aborted) throw new Error("Analysis cancelled");

    const component = mockComponents[i];
    const reasoningCount =
      Math.floor(
        Math.random() * (MOCK_CONFIG.reasoningCount.max - MOCK_CONFIG.reasoningCount.min + 1)
      ) + MOCK_CONFIG.reasoningCount.min;

    for (let j = 0; j < reasoningCount; j++) {
      if (signal?.aborted) throw new Error("Analysis cancelled");
      await waitWithAbort(MOCK_CONFIG.reasoningDelay, signal);
      if (signal?.aborted) throw new Error("Analysis cancelled");

      const reasoningSnippet =
        component.reasoning[j] ||
        component.reasoning[Math.floor(Math.random() * component.reasoning.length)];

      onUpdate({
        type: "reasoning",
        componentId: component.id,
        componentName: component.name,
        reasoning: reasoningSnippet,
        hierarchyLevel: component.hierarchy,
      });
    }

    if (signal?.aborted) throw new Error("Analysis cancelled");
    await waitWithAbort(MOCK_CONFIG.selectionDelay, signal);
    if (signal?.aborted) throw new Error("Analysis cancelled");

    onUpdate({
      type: "selection",
      componentId: component.id,
      componentName: component.name,
      partData: component.partData,
      position: component.position,
      hierarchyLevel: component.hierarchy,
    });
  }

  if (signal?.aborted) throw new Error("Analysis cancelled");
  await waitWithAbort(500, signal);
  if (signal?.aborted) throw new Error("Analysis cancelled");

  onUpdate({
    type: "complete",
    message: "Component analysis complete. All components validated and optimized.",
  });
}

// ---- Mock chat ----

let mockQueryIdCounter = 0;
export const mockActiveQueries = new Map<string, { query: string; timestamp: number }>();

export async function mockQuery(
  request: ChatQueryRequest,
  config: ChatApiConfig
): Promise<ChatQueryResponse> {
  await new Promise((resolve) => setTimeout(resolve, 9000 + Math.random() * 11000));

  const queryId = `query_${++mockQueryIdCounter}_${Date.now()}`;
  mockActiveQueries.set(queryId, { query: request.query, timestamp: Date.now() });

  if (Math.random() > 0.5) {
    return {
      type: "context_request",
      queryId,
      message: `I need more information to process your query: "${request.query}". Please provide additional context.`,
    };
  }

  mockActiveQueries.delete(queryId);
  return {
    type: "response",
    message: `Response to: "${request.query}". Analysis complete.`,
  };
}

export async function mockContinue(
  request: ChatContinueRequest,
  config: ChatApiConfig
): Promise<ChatContinueResponse> {
  await new Promise((resolve) => setTimeout(resolve, 9000 + Math.random() * 11000));

  const queryData = mockActiveQueries.get(request.queryId);
  if (!queryData) throw new Error("Query ID not found. It may have expired.");

  if (Math.random() > 0.7) {
    return {
      type: "context_request",
      queryId: request.queryId,
      message: "Thank you. What is your preferred budget range?",
    };
  }

  mockActiveQueries.delete(request.queryId);
  return {
    type: "response",
    message: `Based on your context, here is the final response for "${queryData.query}".`,
  };
}
