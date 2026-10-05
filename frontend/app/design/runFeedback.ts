import type { DesignSnapshot } from "../services/api/designRunApi.ts";

// Runtime details belong in the saved JSON. Never use an unknown error as UI copy.
function getOperationalMessage(reason: string): string | null {
  if (
    /another design run is active|a run is already active|base run is still running|http 409/i.test(
      reason,
    )
  ) {
    return "Another design is being worked on. Try again when it finishes.";
  }
  if (/quota|rate.?limit|resource.exhausted|\b429\b/i.test(reason)) {
    return "Generation is temporarily unavailable. Try again later.";
  }
  if (
    /budget|configured model allowance|initial reading plan exceeds|additional documents may be requested/i.test(
      reason,
    )
  ) {
    return "Generation reached its limit before finishing. Try a smaller request or continue from the parts already selected.";
  }
  if (/supported BOM size|initial functional.block scope/i.test(reason)) {
    return "This device is too large to work through in one request. Try focusing on fewer functions.";
  }
  if (
    /disconnect|interrupted|response closed|analysis stopped|abort/i.test(
      reason,
    )
  ) {
    return "Generation stopped before finishing. Reload to see the last saved result.";
  }
  if (
    /failed to fetch|fetch failed|network|load failed|connection|timeout|timed out/i.test(
      reason,
    )
  ) {
    return "The connection was lost. Reload to check for a saved result.";
  }
  if (
    /model|provider|api.key|\b50[234]\b|unavailable|overloaded/i.test(reason)
  ) {
    return "Part selection is unavailable right now. Try again later.";
  }
  return null;
}

export function getRunErrorMessage(
  failure: unknown,
  context: "generate" | "load" = "generate",
): string {
  const reason =
    failure instanceof Error
      ? failure.message
      : typeof failure === "string"
        ? failure
        : "";
  if (/run not found|http 404/i.test(reason))
    return "This saved design could not be found. Check the link or start a new design.";
  if (/invalid request|must not be blank|answers must match/i.test(reason))
    return "The request could not be submitted. Check your description and try again.";
  // A failed retrieval says nothing about whether generation has stopped.
  if (context === "load")
    return "The saved design could not be loaded. Check your connection and try again.";
  return (
    getOperationalMessage(reason) ??
    "Generation could not finish. Try again or start with a simpler request."
  );
}

export function getRunStopMessage(snapshot: DesignSnapshot): string | null {
  if (snapshot.lifecycle === "running" || snapshot.lifecycle === "needs_input")
    return null;
  if (snapshot.lifecycle === "interrupted")
    return "Generation stopped before finishing. Your progress was saved.";
  if (snapshot.lifecycle === "error")
    return getRunErrorMessage(snapshot.terminal_reason);
  const reason = snapshot.terminal_reason;
  if (snapshot.compatibility === "issues_found") {
    if (/no further supported correction/i.test(reason))
      return "No further automatic fix was found. The remaining issues need a change to the design.";
    if (/correction allowance/i.test(reason))
      return "Automatic corrections finished with issues still unresolved.";
    return (
      getOperationalMessage(reason) ??
      "These issues remain unresolved after review."
    );
  }
  if (snapshot.compatibility === "checked") return null;
  if (/no supported device requirements/i.test(reason))
    return "No parts were selected. Describe the device’s functions and how it will be powered.";
  return (
    getOperationalMessage(reason) ??
    "The compatibility review did not finish. The selected parts can still be inspected."
  );
}
