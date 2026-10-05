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

export interface Requirement {
  id: string;
  clause: string;
  description: string;
  component_ids: string[];
}

export interface Product {
  manufacturer: string;
  mpn: string;
  package: string | null;
  description: string;
  datasheet_url: string | null;
  product_url: string | null;
  parameters: Array<Record<string, unknown>>;
  retrieved_at: string;
}

export interface Component {
  id: string;
  name: string;
  kind: "active" | "module" | "passive" | "connector";
  purpose: string;
  support_for: string[];
  selection_reason: string;
  selection_error: string | null;
  product: Product | null;
  document_ids: string[];
  document_errors: string[];
}

export interface Evidence {
  id: string;
  component_ids: string[];
  document_id: string;
  page: number;
  kind: "text" | "figure";
  quote: string;
  fact: string;
  conditions: string;
}

export interface SourceDocument {
  document_id: string;
  url: string;
  requested_url: string;
  title: string;
  content_hash: string;
  media_type: string;
  fetched_at: string;
  page_count: number;
  pages_interpreted?: number[];
}

export interface Quantity {
  value: number;
  unit: string;
  basis:
    | "min"
    | "max"
    | "typical"
    | "nominal"
    | "estimate"
    | "absolute_maximum";
  source_ids?: string[];
  binding_error?: string;
  source_conditions?: string[];
  evidence_ids: string[];
  assumption_id: string | null;
}

export interface Rail {
  id: string;
  source_component_id: string;
  description: string;
  voltage_min: Quantity | null;
  voltage_max: Quantity | null;
  available_current: Quantity | null;
  loads: Array<{
    component_id: string;
    voltage_min: Quantity | null;
    voltage_max: Quantity | null;
    current: Quantity | null;
  }>;
  evidence_ids: string[];
}

export interface Interface {
  id: string;
  protocol: string;
  endpoints: Array<{
    component_id: string;
    address: string | null;
    assumption_id: string | null;
  }>;
  configuration: string;
  evidence_ids: string[];
}

export interface SourceSupportNeed {
  id: string;
  purpose: string;
  parent_ids: string[];
  necessity: "required" | "recommended";
  connection_requirement: string;
  evidence_ids: string[];
  document_id: string | null;
}

export interface SupportNeed {
  id: string;
  purpose: string;
  parent_ids: string[];
  necessity: "required" | "recommended" | "optional";
  status: "satisfied" | "included" | "not_applicable" | "unresolved";
  component_ids: string[];
  connections: string;
  evidence_ids: string[];
  explanation: string;
}

export interface SignalCheck {
  id: string;
  source_component_id: string;
  receiver_component_id: string;
  description: string;
  pullup_rail_id: string | null;
  output_high_min: Quantity | null;
  input_high_min: Quantity | null;
  output_low_max: Quantity | null;
  input_low_max: Quantity | null;
}

export interface RegulatorCheck {
  component_id: string;
  kind: "linear" | "switching";
  input_rail_id: string;
  output_rail_id: string;
  dropout: Quantity | null;
  ambient_max: Quantity | null;
  junction_target: Quantity | null;
  theta_ja: Quantity | null;
  average_output_current: Quantity | null;
}

export interface DesignSnapshot {
  id: string;
  parent_run_id: string | null;
  revision: number;
  created_at: string;
  updated_at: string;
  lifecycle: "running" | "needs_input" | "finished" | "interrupted" | "error";
  compatibility: "checked" | "issues_found" | null;
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
  requirements: Requirement[];
  components: Component[];
  source_support_needs: SourceSupportNeed[];
  support_needs: SupportNeed[];
  rails: Rail[];
  interfaces: Interface[];
  signal_checks: SignalCheck[];
  regulator_checks: RegulatorCheck[];
  pending_questions: Array<{
    id: string;
    requirement_id: string;
    question: string;
    guidance: string;
  }>;
  configuration_notes: string[];
  findings: Finding[];
  evidence_errors: Finding[];
  evidence: Evidence[];
  documents: SourceDocument[];
  usage: {
    model_calls: number;
    input_tokens: number;
    output_tokens: number;
    supplier_calls: number;
    documents: number;
    pdf_pages: number;
    correction_rounds: number;
    elapsed_seconds: number;
  };
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

export type RunRequest =
  | { query: string; options?: Partial<PurchasingOptions> }
  | { base_run_id: string; modification: string }
  | {
      base_run_id: string;
      answers: Record<string, string>;
    };

export type InitialRequest = Extract<RunRequest, { query: string }>;

export function getSafeUrl(
  value: string | null | undefined,
): string | undefined {
  if (!value) return undefined;
  try {
    return ["http:", "https:"].includes(new URL(value).protocol)
      ? value
      : undefined;
  } catch {
    return undefined;
  }
}

function getBaseUrl(): string {
  return API_CONFIG.baseUrl.replace(/\/$/, "");
}

export function getExportUrl(id: string, format: "csv" | "json"): string {
  return `${getBaseUrl()}/api/runs/${encodeURIComponent(id)}/export?format=${format}`;
}

async function getResponseError(response: Response): Promise<Error> {
  const data = await response.json().catch(() => null);
  return new Error(
    data?.error || `Backend request failed (HTTP ${response.status})`,
  );
}

export async function getSavedRun(
  id: string,
  signal?: AbortSignal,
): Promise<DesignSnapshot> {
  const timeout = AbortSignal.timeout(20000);
  const response = await fetch(
    `${getBaseUrl()}/api/runs/${encodeURIComponent(id)}`,
    {
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    },
  );
  if (!response.ok) throw await getResponseError(response);
  const snapshot = (await response.json()) as DesignSnapshot;
  if (snapshot.id !== id)
    throw new Error("The backend returned a mismatched saved design.");
  return snapshot;
}

/** One POST stream, with a deadline covering headers and the entire response body. */
export async function streamRun(
  request: RunRequest,
  onEvent: (event: RunEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  if (API_CONFIG.generationDisabled)
    throw new Error(
      "Demo mode is enabled. Live design generation is unavailable in this mode.",
    );
  const controller = new AbortController();
  const handleAbort = () => controller.abort();
  signal?.addEventListener("abort", handleAbort, { once: true });
  if (signal?.aborted) controller.abort();
  let timedOut = false;
  const timer = setTimeout(
    () => {
      timedOut = true;
      controller.abort();
    },
    10 * 60 * 1000,
  );
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
  let receivedTerminalEvent = false;
  try {
    const path = "query" in request ? "/api/component-analysis" : "/api/refine";
    const response = await fetch(`${getBaseUrl()}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal: controller.signal,
    });
    if (!response.ok) throw await getResponseError(response);
    reader = response.body?.getReader();
    if (!reader) throw new Error("The backend returned no progress stream.");
    const decoder = new TextDecoder();
    let buffer = "";
    let runId: string | undefined;
    let lastSequence = 0;
    const handleFrame = (frame: string) => {
      const data = frame
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trimStart())
        .join("\n");
      if (!data) return;
      const event = JSON.parse(data) as RunEvent;
      if (
        !event?.run_id ||
        !Number.isInteger(event.sequence) ||
        !["started", "progress", "snapshot", "complete", "error"].includes(
          event.type,
        )
      ) {
        throw new Error("Invalid backend progress event.");
      }
      if (runId && event.run_id !== runId) return;
      if (event.sequence <= lastSequence) return;
      runId = event.run_id;
      lastSequence = event.sequence;
      if (event.snapshot && event.snapshot.id !== runId)
        throw new Error("The backend returned a mismatched design snapshot.");
      onEvent(event);
      receivedTerminalEvent =
        event.type === "complete" || event.type === "error";
    };
    while (!receivedTerminalEvent) {
      const { value, done } = await reader.read();
      buffer = (buffer + decoder.decode(value, { stream: !done })).replace(
        /\r\n/g,
        "\n",
      );
      let frameEnd: number;
      while (
        !receivedTerminalEvent &&
        (frameEnd = buffer.indexOf("\n\n")) !== -1
      ) {
        handleFrame(buffer.slice(0, frameEnd));
        buffer = buffer.slice(frameEnd + 2);
      }
      if (done) break;
    }
    if (!receivedTerminalEvent && buffer.trim()) handleFrame(buffer);
    if (!receivedTerminalEvent)
      throw new Error(
        "Connection interrupted before completion. Reload the saved result to check its status.",
      );
  } catch (error) {
    if (controller.signal.aborted) {
      throw new Error(
        timedOut
          ? "The 10-minute connection limit was reached. Reload the saved result."
          : "Analysis stopped. Reload the saved result after the current operation finishes.",
      );
    }
    throw error;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", handleAbort);
    if (!receivedTerminalEvent) controller.abort();
    // Terminal events finish the operation even if a proxy keeps the body open.
    await reader?.cancel().catch(() => {});
    reader?.releaseLock();
  }
}
