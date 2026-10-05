import assert from "node:assert/strict";
import { test } from "node:test";
import {
  getExportUrl,
  getSavedRun,
  getSafeUrl,
  streamRun,
} from "../app/services/api/designRunApi.ts";
import type { RunEvent } from "../app/services/api/designRunApi.ts";
import { savedRun } from "./fixtures/designRun.ts";

function createEventResponse(events: RunEvent[]) {
  return new Response(
    events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join(""),
    {
      headers: { "Content-Type": "text/event-stream" },
    },
  );
}

test("fresh runs send purchasing options and accept ordered snapshots only", async (t) => {
  const started: RunEvent = {
    type: "started",
    run_id: savedRun.id,
    sequence: 1,
    snapshot: savedRun,
  };
  const complete: RunEvent = {
    ...started,
    type: "complete",
    sequence: 2,
    snapshot: { ...savedRun, compatibility: "checked", review_completed: true },
  };
  const request = {
    query: savedRun.original_request,
    options: { board_quantity: 5 },
  };
  t.mock.method(
    globalThis,
    "fetch",
    async (url: RequestInfo | URL, init?: RequestInit) => {
      assert.equal(String(url), "http://localhost:3001/api/component-analysis");
      assert.deepEqual(JSON.parse(init!.body as string), request);
      return createEventResponse([
        started,
        started,
        { ...complete, run_id: "obsolete" },
        complete,
      ]);
    },
  );
  const received: RunEvent[] = [];
  await streamRun(request, (event) => received.push(event));
  assert.deepEqual(received, [started, complete]);
});

test("refinement sends the saved parent ID and retains terminal error snapshots", async (t) => {
  const request = {
    base_run_id: savedRun.id,
    modification: "Add a humidity sensor",
  };
  const child = {
    ...savedRun,
    id: "22222222222222222222222222222222",
    parent_run_id: savedRun.id,
  };
  t.mock.method(
    globalThis,
    "fetch",
    async (url: RequestInfo | URL, init?: RequestInit) => {
      assert.equal(String(url), "http://localhost:3001/api/refine");
      assert.deepEqual(JSON.parse(init!.body as string), request);
      return createEventResponse([
        { type: "error", run_id: child.id, sequence: 1, snapshot: child },
      ]);
    },
  );
  const received: RunEvent[] = [];
  await streamRun(request, (event) => received.push(event));
  assert.equal(received[0].snapshot?.parent_run_id, savedRun.id);
});

test("clarification sends every question ID and keeps needs_input distinct from finished", async (t) => {
  const request = {
    base_run_id: savedRun.id,
    answers: { "question:environment": "Indoor", "question:power": "USB" },
  };
  const clarification = {
    ...savedRun,
    lifecycle: "needs_input" as const,
    compatibility: null,
  };
  t.mock.method(
    globalThis,
    "fetch",
    async (url: RequestInfo | URL, init?: RequestInit) => {
      assert.equal(String(url), "http://localhost:3001/api/refine");
      assert.deepEqual(JSON.parse(init!.body as string), request);
      return createEventResponse([
        {
          type: "complete",
          run_id: savedRun.id,
          sequence: 1,
          snapshot: clarification,
        },
      ]);
    },
  );
  const received: RunEvent[] = [];
  await streamRun(request, (event) => received.push(event));
  assert.equal(received[0].snapshot?.lifecycle, "needs_input");
  assert.equal(received[0].snapshot?.compatibility, null);
});

test("fragmented CRLF and UTF-8 events complete without waiting for the body to close", async (t) => {
  const complete: RunEvent = {
    type: "complete",
    run_id: savedRun.id,
    sequence: 1,
    message: "Review → complete",
    snapshot: savedRun,
  };
  const bytes = new TextEncoder().encode(
    `: heartbeat\r\n\r\ndata: ${JSON.stringify(complete)}\r\n\r\n`,
  );
  let cancelled = false;
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const byte of bytes) controller.enqueue(new Uint8Array([byte]));
      // Deliberately stay open: a terminal event is sufficient to finish.
    },
    cancel() {
      cancelled = true;
    },
  });
  t.mock.method(globalThis, "fetch", async () => new Response(body));
  const received: RunEvent[] = [];
  await streamRun({ query: "sensor" }, (event) => received.push(event));
  assert.deepEqual(received, [complete]);
  assert.equal(cancelled, true);
});

test("restoration uses GET and exports the saved run ID", async (t) => {
  t.mock.method(
    globalThis,
    "fetch",
    async (url: RequestInfo | URL, init?: RequestInit) => {
      assert.equal(
        String(url),
        `http://localhost:3001/api/runs/${savedRun.id}`,
      );
      assert.equal(init?.method ?? "GET", "GET");
      return Response.json(savedRun);
    },
  );
  assert.deepEqual(await getSavedRun(savedRun.id), savedRun);
  assert.equal(
    getExportUrl(savedRun.id, "json"),
    `http://localhost:3001/api/runs/${savedRun.id}/export?format=json`,
  );
});

test("saved review outcomes preserve nonblocking details without changing the result", async (t) => {
  const notes = [
    {
      id: "source-note",
      revision: 1,
      area: "evidence",
      method: "code",
      kind: "check",
      status: "unknown",
      subject_ids: ["U1"],
      evidence_ids: [],
      document_id: null,
      explanation: "A source reference could not be resolved.",
      remedy: "",
    },
  ];
  const fetchMock = t.mock.method(globalThis, "fetch");
  for (const compatibility of ["checked", "issues_found", null] as const) {
    fetchMock.mock.mockImplementation(async () =>
      Response.json({ ...savedRun, compatibility, findings: notes }),
    );
    const snapshot = await getSavedRun(savedRun.id);
    assert.equal(snapshot.compatibility, compatibility);
    assert.deepEqual(snapshot.findings, notes);
  }
});

test("missing and mismatched saved results remain visible errors", async (t) => {
  const fetchMock = t.mock.method(globalThis, "fetch", async () =>
    Response.json({ error: "Run not found" }, { status: 404 }),
  );
  await assert.rejects(getSavedRun(savedRun.id), /Run not found/);
  fetchMock.mock.mockImplementation(async () =>
    Response.json({ ...savedRun, id: "wrong-run" }),
  );
  await assert.rejects(getSavedRun(savedRun.id), /mismatched saved design/);
});

test("initial HTTP failures and missing terminal events are not success", async (t) => {
  const fetchMock = t.mock.method(globalThis, "fetch", async () =>
    Response.json({ error: "A run is already active" }, { status: 409 }),
  );
  await assert.rejects(
    streamRun({ query: "sensor" }, () => {}),
    /A run is already active/,
  );
  fetchMock.mock.mockImplementation(async () =>
    createEventResponse([
      { type: "started", run_id: savedRun.id, sequence: 1 },
    ]),
  );
  await assert.rejects(
    streamRun({ query: "sensor" }, () => {}),
    /interrupted before completion/,
  );
});

test("mismatched snapshots fail before they reach the UI", async (t) => {
  t.mock.method(globalThis, "fetch", async () =>
    createEventResponse([
      {
        type: "complete",
        run_id: savedRun.id,
        sequence: 1,
        snapshot: { ...savedRun, id: "another-run" },
      },
    ]),
  );
  let delivered = false;
  await assert.rejects(
    streamRun({ query: "sensor" }, () => {
      delivered = true;
    }),
    /mismatched design snapshot/,
  );
  assert.equal(delivered, false);
});

test("stopping a pending request aborts its transport and explains retrieval", async (t) => {
  const controller = new AbortController();
  t.mock.method(
    globalThis,
    "fetch",
    async (_url: RequestInfo | URL, init?: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        init!.signal!.addEventListener(
          "abort",
          () => reject(new DOMException("Aborted", "AbortError")),
          { once: true },
        );
      }),
  );
  const request = streamRun({ query: "sensor" }, () => {}, controller.signal);
  controller.abort();
  await assert.rejects(request, /Analysis stopped.*Reload the saved result/);
});

test("source and purchasing links accept web URLs only", () => {
  assert.equal(
    getSafeUrl("https://example.com/datasheet.pdf#page=2"),
    "https://example.com/datasheet.pdf#page=2",
  );
  for (const value of [
    "javascript:alert(1)",
    "data:text/html,test",
    "file:///secret",
    "/relative",
    null,
  ]) {
    assert.equal(getSafeUrl(value), undefined);
  }
});
