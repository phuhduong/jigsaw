import { API_CONFIG } from "./config.ts";

export interface PurchasingOptions {
  board_quantity: number;
  region: string;
  currency: string;
}

export interface BomRow {
  reference_ids: string[];
  purposes: string[];
  manufacturer: string;
  mpn: string;
  package: string | null;
  installed_quantity: number;
  board_quantity: number;
  required_quantity: number;
  order_quantity: number;
  unit_price: number | null;
  extended_price: number | null;
  currency: string;
  supplier_sku: string | null;
  purchase_url: string | null;
  datasheet_url: string | null;
  stock: number | null;
  moq: number | null;
  order_multiple: number | null;
  retrieved_at: string;
  availability: "available" | "out_of_stock" | "unknown";
  ordering_note: string;
  review_status: DesignSnapshot["compatibility"];
}

export interface Finding {
  id: string;
  revision: number;
  area: "requirements" | "power" | "signals" | "support" | "evidence";
  method: "code" | "model_review";
  kind: "check" | "guidance";
  status: "pass" | "fail" | "unknown" | "not_applicable";
  subject_ids: string[];
  evidence_ids: string[];
  document_id: string | null;
  explanation: string;
  remedy: string;
}

export interface DesignSnapshot {
  id: string;
  parent_run_id: string | null;
  revision: number;
  created_at: string;
  updated_at: string;
  lifecycle: "running" | "needs_input" | "finished" | "interrupted" | "error";
  compatibility: "checked" | "issues_found" | "incomplete";
  sourcing: "available" | "partial" | "unknown";
  stage: string;
  summary: string;
  original_request: string;
  modification: string | null;
  options: PurchasingOptions;
  model: string;
  model_configuration: Record<string, string>;
  prompt_version: string;
  terminal_reason: string;
  review_completed: boolean;
  assumptions: Array<{ id: string; description: string }>;
  components: Array<{ id: string; name: string; purpose: string; selection_error: string | null; product: { mpn: string } | null }>;
  pending_questions: Array<{ id: string; requirement_id: string; question: string; guidance: string }>;
  configuration_notes: string[];
  findings: Finding[];
  evidence_errors: Finding[];
  evidence: Array<{
    id: string; component_ids: string[]; document_id: string; page: number;
    kind: "text" | "figure"; quote: string; fact: string; conditions: string;
  }>;
  documents: Array<{
    document_id: string; url: string; requested_url: string; title: string;
    content_hash: string; media_type: string; fetched_at: string; page_count: number;
    pages_interpreted?: number[];
  }>;
  bom: BomRow[];
}

export interface RunEvent {
  type: "started" | "progress" | "snapshot" | "complete" | "error";
  run_id: string;
  sequence: number;
  stage?: string;
  message?: string;
  snapshot?: DesignSnapshot;
}

export type RunRequest = { query: string; options?: Partial<PurchasingOptions> } | { base_run_id: string; modification: string } | {
  base_run_id: string; answers: Record<string, string>;
};

export function safeUrl(value: string | null | undefined): string | undefined {
  if (!value) return undefined;
  try {
    return ["http:", "https:"].includes(new URL(value).protocol) ? value : undefined;
  } catch {
    return undefined;
  }
}

function baseUrl(): string {
  return API_CONFIG.baseUrl.replace(/\/$/, "");
}

export function exportUrl(id: string, format: "csv" | "json"): string {
  return `${baseUrl()}/api/runs/${encodeURIComponent(id)}/export?format=${format}`;
}

async function responseError(response: Response): Promise<Error> {
  const data = await response.json().catch(() => null);
  return new Error(data?.error || `Backend request failed (HTTP ${response.status})`);
}

export async function getSavedRun(id: string, signal?: AbortSignal): Promise<DesignSnapshot> {
  const timeout = AbortSignal.timeout(20000);
  const response = await fetch(`${baseUrl()}/api/runs/${encodeURIComponent(id)}`, {
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
  });
  if (!response.ok) throw await responseError(response);
  const snapshot = await response.json() as DesignSnapshot;
  if (snapshot.id !== id) throw new Error("The backend returned a mismatched saved design.");
  return snapshot;
}

/** One POST stream, with a deadline covering headers and the entire response body. */
export async function streamRun(request: RunRequest, onEvent: (event: RunEvent) => void, signal?: AbortSignal): Promise<void> {
  if (API_CONFIG.useMock) throw new Error("Demo mode is enabled. Live design generation is unavailable in this mode.");
  const controller = new AbortController();
  const cancel = () => controller.abort();
  signal?.addEventListener("abort", cancel, { once: true });
  if (signal?.aborted) controller.abort();
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, 10 * 60 * 1000);
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
  let finished = false;
  try {
    const path = "query" in request ? "/api/component-analysis" : "/api/refine";
    const response = await fetch(`${baseUrl()}${path}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request), signal: controller.signal,
    });
    if (!response.ok) throw await responseError(response);
    reader = response.body?.getReader();
    if (!reader) throw new Error("The backend returned no progress stream.");
    const decoder = new TextDecoder();
    let buffer = "";
    let terminal = false;
    let runId: string | undefined;
    let sequence = 0;
    const process = (frame: string) => {
      const data = frame.split("\n").filter(line => line.startsWith("data:")).map(line => line.slice(5).trimStart()).join("\n");
      if (!data) return;
      const event = JSON.parse(data) as RunEvent;
      if (!event.run_id || !Number.isInteger(event.sequence)) throw new Error("Invalid backend progress event.");
      if (runId && event.run_id !== runId) return;
      if (event.sequence <= sequence) return;
      runId = event.run_id;
      sequence = event.sequence;
      if (event.snapshot && event.snapshot.id !== runId) throw new Error("The backend returned a mismatched design snapshot.");
      onEvent(event);
      terminal = terminal || event.type === "complete" || event.type === "error";
    };
    while (true) {
      const { value, done } = await reader.read();
      buffer = (buffer + decoder.decode(value, { stream: !done })).replace(/\r\n/g, "\n");
      let end: number;
      while ((end = buffer.indexOf("\n\n")) !== -1) {
        process(buffer.slice(0, end));
        buffer = buffer.slice(end + 2);
      }
      if (done) break;
    }
    if (buffer.trim()) process(buffer);
    if (!terminal) throw new Error("Connection interrupted before completion. Reload the saved result to check its status.");
    finished = true;
  } catch (error) {
    if (controller.signal.aborted) {
      throw new Error(timedOut ? "The 10-minute connection limit was reached. Reload the saved result." : "Analysis stopped. Reload the saved result after the current operation finishes.");
    }
    throw error;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", cancel);
    if (!finished) controller.abort();
    reader?.releaseLock();
  }
}
