import assert from "node:assert/strict";
import { test } from "node:test";
import {
  getRunErrorMessage,
  getRunStopMessage,
} from "../app/design/runFeedback.ts";
import { savedRun } from "./fixtures/designRun.ts";

test("runtime errors use safe copy and retain actionable categories", () => {
  assert.match(
    getRunErrorMessage(
      new Error("Another design run is active; retry when it finishes"),
    ),
    /Another design/,
  );
  assert.match(
    getRunErrorMessage(
      "429 RESOURCE_EXHAUSTED: gemini-3.5-flash-lite quota account=secret",
    ),
    /temporarily unavailable/,
  );
  assert.match(
    getRunErrorMessage(new TypeError("Failed to fetch")),
    /connection/,
  );
  assert.match(
    getRunErrorMessage("ModelError: GEMINI_API_KEY is not configured"),
    /unavailable/,
  );
  assert.match(
    getRunErrorMessage("Run input_tokens budget exhausted"),
    /reached its limit/,
  );
  assert.match(
    getRunErrorMessage("Client disconnected; no further operations started"),
    /stopped before finishing/,
  );
  assert.equal(
    getRunErrorMessage("Traceback: File /private/run.py: account=secret"),
    "Generation could not finish. Try again or start with a simpler request.",
  );
});

test("restoration errors do not claim generation stopped", () => {
  assert.match(
    getRunErrorMessage("Run not found", "load"),
    /could not be found/,
  );
  assert.equal(
    getRunErrorMessage(
      new Error("NetworkError: backend host unreachable"),
      "load",
    ),
    "The saved design could not be loaded. Check your connection and try again.",
  );
});

test("failed reviews explain why automatic corrections stopped", () => {
  const run = {
    ...savedRun,
    compatibility: "issues_found" as const,
    terminal_reason: "Checks failed; correction allowance reached",
  };
  assert.equal(
    getRunStopMessage(run),
    "Automatic corrections finished with issues still unresolved.",
  );
  assert.match(
    getRunStopMessage({
      ...run,
      terminal_reason: "No further supported correction was found",
    })!,
    /No further automatic fix/,
  );
  assert.match(
    getRunStopMessage({
      ...run,
      terminal_reason: "Run input_tokens budget exhausted",
    })!,
    /reached its limit/,
  );
});

test("saved states expose only useful stop explanations", () => {
  for (const lifecycle of ["running", "needs_input"] as const)
    assert.equal(getRunStopMessage({ ...savedRun, lifecycle }), null);
  assert.equal(
    getRunStopMessage({ ...savedRun, compatibility: "checked" }),
    null,
  );
  assert.match(
    getRunStopMessage({ ...savedRun, lifecycle: "interrupted" })!,
    /progress was saved/,
  );
  assert.match(
    getRunStopMessage({
      ...savedRun,
      terminal_reason: "Request exceeds the supported BOM size",
    })!,
    /fewer functions/,
  );
  assert.match(getRunStopMessage(savedRun)!, /review did not finish/);
  assert.equal(
    getRunStopMessage({
      ...savedRun,
      lifecycle: "error",
      terminal_reason: "ValueError: raw_trace id=1234",
    }),
    "Generation could not finish. Try again or start with a simpler request.",
  );
});
