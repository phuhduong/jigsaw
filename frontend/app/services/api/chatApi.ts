import { API_CONFIG } from "./config";
import { mockQuery, mockContinue } from "./mockImplementations";

export interface ChatQueryRequest {
  query: string;
}

export interface ChatQueryResponse {
  type: "response" | "context_request";
  queryId?: string;
  requestId?: string;
  message: string;
  response?: string;
}

export interface ChatContinueRequest {
  context: string;
  queryId: string;
}

export interface ChatContinueResponse {
  type: "response" | "context_request";
  queryId?: string;
  requestId?: string;
  message: string;
  response?: string;
}

export interface ChatApiConfig {
  baseUrl: string;
  queryEndpoint: string;
  continueEndpoint: string;
  timeout?: number;
}

const defaultConfig: ChatApiConfig = {
  baseUrl: "http://localhost:3001",
  queryEndpoint: "/api/query",
  continueEndpoint: "/api/continue",
  timeout: 30000,
};

async function realQuery(
  request: ChatQueryRequest,
  config: ChatApiConfig,
  signal?: AbortSignal
): Promise<ChatQueryResponse> {
  const controller = signal ? undefined : new AbortController();
  const abortSignal = signal || controller?.signal;
  const timeoutId = config.timeout ? setTimeout(() => controller?.abort(), config.timeout) : null;

  try {
    const response = await fetch(`${config.baseUrl}${config.queryEndpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal: abortSignal,
    });

    if (timeoutId) clearTimeout(timeoutId);
    if (!response.ok) {
      const errorText = await response.text().catch(() => "Unknown error");
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
    }
    return await response.json();
  } catch (error: any) {
    if (timeoutId) clearTimeout(timeoutId);
    if (error.name === "AbortError") throw new Error("Request timeout or cancelled");
    if (error.message?.includes("Failed to fetch") || error.name === "TypeError") {
      throw new Error(
        `Failed to connect to backend at ${config.baseUrl}. Make sure the backend is running.`
      );
    }
    throw error;
  }
}

async function realContinue(
  request: ChatContinueRequest,
  config: ChatApiConfig,
  signal?: AbortSignal
): Promise<ChatContinueResponse> {
  const controller = signal ? undefined : new AbortController();
  const abortSignal = signal || controller?.signal;
  const timeoutId = config.timeout ? setTimeout(() => controller?.abort(), config.timeout) : null;

  try {
    const response = await fetch(`${config.baseUrl}${config.continueEndpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal: abortSignal,
    });

    if (timeoutId) clearTimeout(timeoutId);
    if (!response.ok) {
      const errorText = await response.text().catch(() => "Unknown error");
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
    }
    return await response.json();
  } catch (error: any) {
    if (timeoutId) clearTimeout(timeoutId);
    if (error.name === "AbortError") throw new Error("Request timeout or cancelled");
    if (error.message?.includes("Failed to fetch") || error.name === "TypeError") {
      throw new Error(
        `Failed to connect to backend at ${config.baseUrl}. Make sure the backend is running.`
      );
    }
    throw error;
  }
}

class ChatApiService {
  private config: ChatApiConfig;
  private useMock: boolean;

  constructor(config?: Partial<ChatApiConfig>, useMock: boolean = false) {
    this.config = { ...defaultConfig, ...config };
    this.useMock = useMock;
  }

  async sendQuery(query: string, signal?: AbortSignal): Promise<ChatQueryResponse> {
    const request: ChatQueryRequest = { query };
    return this.useMock ? mockQuery(request, this.config) : realQuery(request, this.config, signal);
  }

  async sendContext(
    context: string,
    queryId: string,
    signal?: AbortSignal
  ): Promise<ChatContinueResponse> {
    const request: ChatContinueRequest = { context, queryId };
    return this.useMock
      ? mockContinue(request, this.config)
      : realContinue(request, this.config, signal);
  }

  updateConfig(config: Partial<ChatApiConfig>) {
    this.config = { ...this.config, ...config };
  }

  setUseMock(useMock: boolean) {
    this.useMock = useMock;
  }
}

export const chatApi = new ChatApiService(
  { baseUrl: API_CONFIG.baseUrl },
  API_CONFIG.useMock
);

export { ChatApiService };
