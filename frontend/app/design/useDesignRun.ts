import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";
import { getSavedRun, streamRun } from "../services/api/designRunApi";
import type {
  DesignSnapshot,
  InitialRequest,
  RunRequest,
} from "../services/api/designRunApi";
import { getRunErrorMessage } from "./runFeedback";

export function useDesignRun({
  initialRequest,
  runId,
}: {
  initialRequest?: InitialRequest;
  runId: string | null;
}) {
  const navigate = useNavigate();
  const navigateRef = useRef(navigate);
  navigateRef.current = navigate;
  const routeRunIdRef = useRef(runId);
  routeRunIdRef.current = runId;
  const [snapshot, setSnapshot] = useState<DesignSnapshot | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [failedRequest, setFailedRequest] = useState<RunRequest | null>(null);
  const controllerRef = useRef<AbortController | null>(null);
  const requestVersionRef = useRef(0);
  const activeRunIdRef = useRef<string | null>(null);
  const clearingInitialRequestRef = useRef(false);

  const run = useCallback(async (request: RunRequest): Promise<void> => {
    controllerRef.current?.abort();
    const requestController = new AbortController();
    controllerRef.current = requestController;
    const requestVersion = ++requestVersionRef.current;
    let started = false;
    setStreaming(true);
    setLoading(false);
    setError(null);
    setFailedRequest(null);
    setStage("plan");
    if ("query" in request) {
      activeRunIdRef.current = null;
      setSnapshot(null);
    }
    try {
      await streamRun(
        request,
        (event) => {
          if (requestVersionRef.current !== requestVersion) return;
          if (!started) {
            started = true;
            activeRunIdRef.current = event.run_id;
            // A child must never briefly show the parent's BOM or export links.
            setSnapshot(event.snapshot ?? null);
            void navigateRef.current(
              `/design?run=${encodeURIComponent(event.run_id)}`,
              { replace: "query" in request, state: null },
            );
          } else if (event.snapshot) {
            setSnapshot(event.snapshot);
          }
          const nextStage = event.stage || event.snapshot?.stage;
          // Show workflow stages, not individual model-call labels.
          if (
            nextStage &&
            [
              "started",
              "plan",
              "select",
              "sourcing",
              "evidence",
              "review",
              "correct",
              "complete",
            ].includes(nextStage)
          )
            setStage(nextStage);
          if (event.type === "error") {
            setError(
              getRunErrorMessage(
                event.message || event.snapshot?.terminal_reason,
              ),
            );
          }
        },
        requestController.signal,
      );
    } catch (failure) {
      if (requestVersionRef.current === requestVersion) {
        setError(getRunErrorMessage(failure));
        if (!started) setFailedRequest(request);
      }
    } finally {
      if (requestVersionRef.current === requestVersion) {
        setStreaming(false);
        setStage("");
        controllerRef.current = null;
      }
    }
  }, []);

  const loadSavedRun = useCallback(async (id: string) => {
    controllerRef.current?.abort();
    const requestController = new AbortController();
    controllerRef.current = requestController;
    const requestVersion = ++requestVersionRef.current;
    activeRunIdRef.current = id;
    setLoading(true);
    setStreaming(false);
    setError(null);
    setFailedRequest(null);
    setStage("");
    try {
      const saved = await getSavedRun(id, requestController.signal);
      if (requestVersionRef.current !== requestVersion) return;
      setSnapshot(saved);
      setStage(saved.stage);
    } catch (failure) {
      if (requestVersionRef.current === requestVersion) {
        setError(getRunErrorMessage(failure, "load"));
      }
    } finally {
      if (requestVersionRef.current === requestVersion) {
        setLoading(false);
        controllerRef.current = null;
      }
    }
  }, []);

  const query = initialRequest?.query ?? "";
  const quantity = initialRequest?.options?.board_quantity;
  const region = initialRequest?.options?.region;
  const currency = initialRequest?.options?.currency;
  useEffect(() => {
    // Publishing the current stream's ID is navigation, not a restoration.
    if (runId && runId === activeRunIdRef.current) {
      clearingInitialRequestRef.current = false;
      return;
    }
    // Consuming a navigation request must not abort its just-started stream.
    if (!runId && !query && clearingInitialRequestRef.current) {
      clearingInitialRequestRef.current = false;
      return;
    }
    clearingInitialRequestRef.current = false;
    controllerRef.current?.abort();
    requestVersionRef.current += 1;
    activeRunIdRef.current = null;
    setSnapshot(null);
    setStreaming(false);
    setLoading(false);
    setError(null);
    setStage("");
    let cancelled = false;
    // Cancel development effect replays before they can submit a second POST.
    queueMicrotask(() => {
      if (cancelled) return;
      if (runId) void loadSavedRun(runId);
      else if (query.trim()) {
        // A failed or stopped initial POST must not replay on browser Back.
        clearingInitialRequestRef.current = true;
        void navigateRef.current("/design", { replace: true, state: null });
        void run({
          query,
          options: { board_quantity: quantity, region, currency },
        });
      }
    });
    return () => {
      cancelled = true;
    };
  }, [runId, query, quantity, region, currency, loadSavedRun, run]);

  useEffect(
    () => () => {
      requestVersionRef.current += 1;
      controllerRef.current?.abort();
    },
    [],
  );

  const reload = useCallback(() => {
    const id = routeRunIdRef.current ?? activeRunIdRef.current;
    if (id) void loadSavedRun(id);
  }, [loadSavedRun]);

  const stop = useCallback(() => {
    if (!controllerRef.current) return;
    requestVersionRef.current += 1;
    controllerRef.current.abort();
    controllerRef.current = null;
    setStreaming(false);
    setLoading(false);
    setStage("");
    setError(
      activeRunIdRef.current
        ? "Generation stopped. Reload to see the last saved result."
        : "Generation stopped before a result was saved.",
    );
  }, []);

  return {
    // The URL is authoritative even during the render before its effect runs.
    snapshot: snapshot?.id === runId ? snapshot : null,
    busy: loading || streaming,
    streaming,
    loading,
    stage,
    error,
    failedRequest,
    run,
    reload,
    stop,
  };
}
