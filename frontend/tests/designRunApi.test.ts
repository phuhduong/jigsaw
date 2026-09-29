import assert from "node:assert/strict";
import { test } from "node:test";
import { exportUrl, getSavedRun, streamRun } from "../app/services/api/designRunApi.ts";
import type { RunEvent } from "../app/services/api/designRunApi.ts";
import { savedRun } from "./fixtures/designRun.ts";

function eventsResponse(events: RunEvent[]) {
  return new Response(events.map(event => `data: ${JSON.stringify(event)}\n\n`).join(""), {
    headers: { "Content-Type": "text/event-stream" },
  });
}

test("fresh runs send purchasing options and accept ordered snapshots only", async t => {
  const started: RunEvent = { type: "started", run_id: savedRun.id, sequence: 1, snapshot: savedRun };
  const complete: RunEvent = { ...started, type: "complete", sequence: 2 };
  const request = { query: savedRun.original_request, options: { board_quantity: 5 } };
  t.mock.method(globalThis, "fetch", async (url: RequestInfo | URL, init?: RequestInit) => {
    assert.equal(String(url), "http://localhost:3001/api/component-analysis");
    assert.deepEqual(JSON.parse(init!.body as string), request);
    return eventsResponse([started, started, { ...complete, run_id: "obsolete" }, complete]);
  });
  const received: RunEvent[] = [];
  await streamRun(request, event => received.push(event));
  assert.deepEqual(received, [started, complete]);
});

test("refinement sends the saved parent ID and retains terminal error snapshots", async t => {
  const request = { base_run_id: savedRun.id, modification: "Add a humidity sensor" };
  const child = { ...savedRun, id: "22222222222222222222222222222222", parent_run_id: savedRun.id };
  t.mock.method(globalThis, "fetch", async (url: RequestInfo | URL, init?: RequestInit) => {
    assert.equal(String(url), "http://localhost:3001/api/refine");
    assert.deepEqual(JSON.parse(init!.body as string), request);
    return eventsResponse([{ type: "error", run_id: child.id, sequence: 1, snapshot: child }]);
  });
  const received: RunEvent[] = [];
  await streamRun(request, event => received.push(event));
  assert.equal(received[0].snapshot?.parent_run_id, savedRun.id);
});

test("restoration uses GET and exports the saved run ID", async t => {
  t.mock.method(globalThis, "fetch", async (url: RequestInfo | URL, init?: RequestInit) => {
    assert.equal(String(url), `http://localhost:3001/api/runs/${savedRun.id}`);
    assert.equal(init?.method ?? "GET", "GET");
    return Response.json(savedRun);
  });
  assert.deepEqual(await getSavedRun(savedRun.id), savedRun);
  assert.equal(exportUrl(savedRun.id, "json"), `http://localhost:3001/api/runs/${savedRun.id}/export?format=json`);
});

test("missing and mismatched saved results remain visible errors", async t => {
  const fetch = t.mock.method(globalThis, "fetch", async () => Response.json({ error: "Run not found" }, { status: 404 }));
  await assert.rejects(getSavedRun(savedRun.id), /Run not found/);
  fetch.mock.mockImplementation(async () => Response.json({ ...savedRun, id: "wrong-run" }));
  await assert.rejects(getSavedRun(savedRun.id), /mismatched saved design/);
});

test("initial HTTP failures and missing terminal events are not success", async t => {
  const fetch = t.mock.method(globalThis, "fetch", async () => Response.json({ error: "A run is already active" }, { status: 409 }));
  await assert.rejects(streamRun({ query: "sensor" }, () => {}), /A run is already active/);
  fetch.mock.mockImplementation(async () => eventsResponse([{ type: "started", run_id: savedRun.id, sequence: 1 }]));
  await assert.rejects(streamRun({ query: "sensor" }, () => {}), /interrupted before completion/);
});
