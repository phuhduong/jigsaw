import { useEffect, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { Link } from "react-router";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  Download,
  Loader2,
  PencilLine,
  RefreshCw,
  Square,
  X,
} from "lucide-react";
import AppHeader from "../components/AppHeader";
import DeviceRequest from "../components/DeviceRequest";
import { API_CONFIG } from "../services/api/config";
import { getExportUrl } from "../services/api/designRunApi";
import type {
  DesignSnapshot,
  InitialRequest,
  RunRequest,
} from "../services/api/designRunApi";
import { useDesignRun } from "./useDesignRun";
import SystemMap from "./SystemMap";
import PartsList from "./PartsList";
import ReviewPanel from "./ReviewPanel";
import ComponentDetail from "./ComponentDetail";
import { getCompatibilityFailures } from "./reportHelpers";
import { getRunStopMessage } from "./runFeedback";
import PartIllustration from "./PartIllustration";

const DESIGN_VIEWS = [
  ["system", "Map"],
  ["bom", "Parts"],
] as const;
type View = (typeof DESIGN_VIEWS)[number][0];
const COMPATIBILITY_LABELS = {
  checked: "Checks passed",
  issues_found: "Checks failed",
};
const REPAIR_INSTRUCTION =
  "Resolve the remaining functional or electrical compatibility failures. Preserve the original device requirements and already suitable components, and review the revised BOM.";
const RETRY_INSTRUCTION =
  "Finish selecting and reviewing this device. Preserve the original requirements and reuse suitable selected parts and available evidence.";

function ClarificationForm({
  snapshot,
  disabled,
  onRun,
}: {
  snapshot: DesignSnapshot;
  disabled: boolean;
  onRun: (request: RunRequest) => Promise<void>;
}) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const hasAnswers = snapshot.pending_questions.every((question) =>
    answers[question.id]?.trim(),
  );

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (disabled || !hasAnswers) return;
    void onRun({
      base_run_id: snapshot.id,
      answers: Object.fromEntries(
        Object.entries(answers).map(([id, answer]) => [id, answer.trim()]),
      ),
    });
  }

  return (
    <section className="clarification" aria-labelledby="clarification-title">
      <h2 id="clarification-title">Clarify your request</h2>
      <form onSubmit={handleSubmit}>
        {snapshot.pending_questions.map((question) => (
          <label key={question.id}>
            {question.question}
            {question.guidance && <span>{question.guidance}</span>}
            <textarea
              value={answers[question.id] ?? ""}
              onChange={(event) =>
                setAnswers((previous) => ({
                  ...previous,
                  [question.id]: event.target.value,
                }))
              }
              maxLength={10000}
              required
              disabled={disabled}
              rows={2}
            />
          </label>
        ))}
        <button
          type="submit"
          className="button button-primary"
          disabled={
            disabled || !snapshot.pending_questions.length || !hasAnswers
          }
        >
          Continue with answers <ArrowRight size={15} aria-hidden="true" />
        </button>
      </form>
    </section>
  );
}

function RefinementForm({
  snapshot,
  disabled,
  active,
  onRun,
  onClose,
}: {
  snapshot: DesignSnapshot;
  disabled: boolean;
  active: boolean;
  onRun: (request: RunRequest) => Promise<void>;
  onClose: () => void;
}) {
  const [modification, setModification] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const trimmedModification = modification.trim();
  useEffect(() => {
    if (active) inputRef.current?.focus();
  }, [active]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (disabled || !trimmedModification) return;
    void onRun({ base_run_id: snapshot.id, modification: trimmedModification });
  }

  return (
    <section className="refinement" aria-labelledby="refinement-title">
      <div className="form-heading">
        <h2 id="refinement-title">What should change?</h2>
        <button
          type="button"
          className="button button-quiet"
          aria-label="Close changes"
          onClick={onClose}
        >
          <X size={18} />
        </button>
      </div>
      <form onSubmit={handleSubmit}>
        <label htmlFor="modification" className="sr-only">
          Changes to the device
        </label>
        <textarea
          id="modification"
          ref={inputRef}
          value={modification}
          onChange={(event) => setModification(event.target.value)}
          maxLength={10000}
          disabled={disabled}
          placeholder="Add another sensor, change the power source…"
          rows={2}
        />
        <div className="refinement-actions">
          <button
            type="submit"
            className="button button-primary"
            disabled={disabled || !trimmedModification}
          >
            Update & recheck <ArrowUpRight size={16} aria-hidden="true" />
          </button>
        </div>
      </form>
    </section>
  );
}

function GenerationProgress({
  stage,
  onStop,
}: {
  stage?: string;
  onStop: () => void;
}) {
  let activeStep = 0;
  if (stage === "select" || stage === "sourcing") activeStep = 1;
  else if (stage === "evidence") activeStep = 2;
  else if (stage === "review" || stage === "correct") activeStep = 3;
  const label =
    stage === "correct"
      ? "Adjusting the parts to resolve issues…"
      : [
          "Planning your device…",
          "Finding components…",
          "Reading datasheets…",
          "Checking compatibility…",
        ][activeStep];
  return (
    <section className="activity-panel" aria-label="Generation progress">
      <div className="activity-current" role="status">
        <Loader2 size={17} className="spin" aria-hidden="true" />
        {label}
      </div>
      <ol className="activity-steps" aria-label="Current stage">
        {["Plan", "Parts", "Sources", "Review"].map((name, index) => (
          <li
            key={name}
            aria-current={index === activeStep ? "step" : undefined}
          >
            <span>{index + 1}</span>
            {name}
          </li>
        ))}
      </ol>
      <button
        type="button"
        className="button button-small button-quiet"
        onClick={onStop}
      >
        <Square size={12} aria-hidden="true" />
        Stop
      </button>
    </section>
  );
}

export default function DesignPage({
  initialRequest,
  runId = null,
}: {
  initialRequest?: InitialRequest;
  runId?: string | null;
}) {
  const {
    snapshot,
    busy,
    streaming,
    loading,
    stage,
    error,
    failedRequest,
    run,
    reload,
    stop,
  } = useDesignRun({ initialRequest, runId });
  const [view, setView] = useState<View>("system");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isRefining, setIsRefining] = useState(false);
  const notesRef = useRef<HTMLDetailsElement>(null);
  const exportMenuRef = useRef<HTMLDetailsElement>(null);
  const changeButtonRef = useRef<HTMLButtonElement>(null);
  const [lastRequest, setLastRequest] = useState(initialRequest);
  const inspectorRef = useRef<HTMLDivElement>(null);
  const shouldRevealSelectionRef = useRef(false);
  const selectionTriggerRef = useRef<HTMLElement | null>(null);
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const selectedComponentId = snapshot?.components.some(
    (part) => part.id === selectedId,
  )
    ? selectedId
    : null;
  const blockingFindings = snapshot ? getCompatibilityFailures(snapshot) : [];
  const disabled =
    busy || snapshot?.lifecycle === "running" || API_CONFIG.generationDisabled;
  const isReviewing = streaming || snapshot?.lifecycle === "running";
  const stopMessage = snapshot ? getRunStopMessage(snapshot) : null;
  const hasFailures =
    !isReviewing &&
    (snapshot?.compatibility === "issues_found" || blockingFindings.length > 0);
  const canRetry =
    snapshot !== null && !disabled && snapshot.lifecycle !== "needs_input";

  const handleRetry = () => {
    if (failedRequest && !busy) {
      void run(failedRequest);
      return;
    }
    if (!snapshot || !canRetry) return;
    // A planning failure has not incorporated the requested change yet. Once
    // planning succeeds, repeat the checks against the updated requirements.
    const modification =
      snapshot.stage === "plan" && snapshot.modification
        ? snapshot.modification
        : hasFailures
          ? REPAIR_INSTRUCTION
          : RETRY_INSTRUCTION;
    void run({ base_run_id: snapshot.id, modification });
  };

  useEffect(() => {
    setSelectedId(null);
    setIsRefining(false);
  }, [runId]);
  useEffect(() => {
    const handlePointerDown = (event: PointerEvent) => {
      if (
        exportMenuRef.current &&
        !exportMenuRef.current.contains(event.target as Node)
      )
        exportMenuRef.current.open = false;
    };
    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, []);
  const revealInspector = () => {
    inspectorRef.current?.focus({ preventScroll: true });
    const rect = inspectorRef.current?.getBoundingClientRect();
    if (
      view === "bom" ||
      window.matchMedia("(max-width: 1179px)").matches ||
      (rect && (rect.bottom < 0 || rect.top > window.innerHeight))
    )
      inspectorRef.current?.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
        block: "start",
      });
  };
  useEffect(() => {
    if (selectedComponentId && shouldRevealSelectionRef.current) {
      shouldRevealSelectionRef.current = false;
      revealInspector();
    }
  }, [selectedComponentId, view]);

  const handleSelectComponent = (id: string) => {
    selectionTriggerRef.current =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    if (selectedComponentId === id) {
      revealInspector();
      return;
    }
    shouldRevealSelectionRef.current = true;
    setSelectedId(id);
  };
  const handleCloseInspector = () => {
    setSelectedId(null);
    if (selectionTriggerRef.current?.isConnected)
      selectionTriggerRef.current.focus();
    else tabRefs.current[view === "bom" ? 1 : 0]?.focus();
  };
  const handleShowNotes = () => {
    if (notesRef.current) {
      notesRef.current.open = true;
      notesRef.current.querySelector("summary")?.focus({ preventScroll: true });
      notesRef.current.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
        block: "start",
      });
    }
  };
  const handleCloseRefinement = () => {
    setIsRefining(false);
    changeButtonRef.current?.focus();
  };
  const handleInspectorKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape") handleCloseInspector();
  };
  const handleExportKeyDown = (event: KeyboardEvent<HTMLDetailsElement>) => {
    if (event.key === "Escape" && exportMenuRef.current) {
      exportMenuRef.current.open = false;
      exportMenuRef.current.querySelector("summary")?.focus();
    }
  };
  const handleTabKeyDown = (
    event: KeyboardEvent<HTMLButtonElement>,
    index: number,
  ) => {
    let nextIndex: number;
    switch (event.key) {
      case "ArrowRight":
        nextIndex = (index + 1) % DESIGN_VIEWS.length;
        break;
      case "ArrowLeft":
        nextIndex = (index - 1 + DESIGN_VIEWS.length) % DESIGN_VIEWS.length;
        break;
      case "Home":
        nextIndex = 0;
        break;
      case "End":
        nextIndex = DESIGN_VIEWS.length - 1;
        break;
      default:
        return;
    }
    event.preventDefault();
    setView(DESIGN_VIEWS[nextIndex][0]);
    tabRefs.current[nextIndex]?.focus();
  };
  const hasWorkspace = Boolean(snapshot || runId || busy);
  const isRestoring = loading || Boolean(runId && !streaming);
  const inspector = snapshot && selectedComponentId && (
    <div
      className={view === "system" ? "selection-inspector" : "bom-inspector"}
      ref={inspectorRef}
      tabIndex={-1}
      aria-label="Component details"
      onKeyDown={handleInspectorKeyDown}
    >
      <ComponentDetail
        snapshot={snapshot}
        componentId={selectedComponentId}
        onSelect={handleSelectComponent}
        onClose={handleCloseInspector}
      />
    </div>
  );

  return (
    <div className="app-shell">
      <AppHeader workspace />
      {!hasWorkspace ? (
        <main id="main-content">
          {error && (
            <div className="request-error notice notice-error" role="alert">
              {error}
            </div>
          )}
          <DeviceRequest
            initialRequest={lastRequest ?? initialRequest}
            onSubmit={(request) => {
              setLastRequest(request);
              void run(request);
            }}
          />
        </main>
      ) : (
        <main id="main-content" className="workspace">
          {API_CONFIG.generationDisabled && (
            <p className="notice notice-info">
              Generation is disabled in this preview.
            </p>
          )}
          <header className="workspace-header">
            <div className="workspace-heading">
              <h1>
                {snapshot?.original_request ||
                  (error
                    ? "Result unavailable"
                    : isRestoring
                      ? "Loading result…"
                      : lastRequest?.query ||
                        initialRequest?.query ||
                        "Selecting components…")}
              </h1>
              {snapshot?.modification &&
                ![REPAIR_INSTRUCTION, RETRY_INSTRUCTION].includes(
                  snapshot.modification,
                ) && (
                  <p className="latest-change">
                    <span>Latest change</span>
                    {snapshot.modification}
                  </p>
                )}
            </div>
            {snapshot && (
              <div className="workspace-tools">
                <button
                  ref={changeButtonRef}
                  className={`button button-small button-quiet${isRefining ? " is-active" : ""}`}
                  type="button"
                  onClick={() => setIsRefining(!isRefining)}
                  disabled={disabled || snapshot.lifecycle === "needs_input"}
                  aria-expanded={isRefining}
                  aria-controls="refine-device"
                >
                  <PencilLine size={15} aria-hidden="true" />
                  Change
                </button>
                <details
                  className="workspace-menu"
                  ref={exportMenuRef}
                  onKeyDown={handleExportKeyDown}
                >
                  <summary>
                    <Download size={15} aria-hidden="true" />
                    Export
                    <ChevronDown size={12} aria-hidden="true" />
                  </summary>
                  <div>
                    <a href={getExportUrl(snapshot.id, "csv")}>
                      Parts CSV <ArrowUpRight size={14} aria-hidden="true" />
                    </a>
                    <a href={getExportUrl(snapshot.id, "json")}>
                      Full JSON <ArrowUpRight size={14} aria-hidden="true" />
                    </a>
                  </div>
                </details>
              </div>
            )}
          </header>
          {snapshot && (
            <div id="refine-device" hidden={!isRefining}>
              <RefinementForm
                key={snapshot.id}
                snapshot={snapshot}
                disabled={disabled}
                active={isRefining}
                onRun={run}
                onClose={handleCloseRefinement}
              />
            </div>
          )}
          <div className="workspace-messages">
            {!streaming && (error || stopMessage || hasFailures) && (
              <section
                className={`result-notice${hasFailures ? " result-needs-attention" : ""}`}
                role={error ? "alert" : "status"}
                aria-label={
                  hasFailures ? "Compatibility issues" : "Generation status"
                }
              >
                <div>
                  <h2>
                    {hasFailures
                      ? "Compatibility issues remain"
                      : error && !error.startsWith("Generation stopped")
                        ? "Couldn’t complete the request"
                        : "Generation stopped"}
                  </h2>
                  <p>
                    {error ||
                      stopMessage ||
                      "The review found compatibility issues in this selection."}
                  </p>
                  {failedRequest && "base_run_id" in failedRequest && (
                    <p>Showing your previous result.</p>
                  )}
                </div>
                <div className="result-actions">
                  {hasFailures && blockingFindings.length > 0 && (
                    <button
                      type="button"
                      className="button button-quiet"
                      onClick={handleShowNotes}
                    >
                      View issues <ArrowRight size={15} aria-hidden="true" />
                    </button>
                  )}
                  {error && runId && !busy && (
                    <button type="button" className="button" onClick={reload}>
                      <RefreshCw size={14} aria-hidden="true" />
                      Reload saved result
                    </button>
                  )}
                  {(canRetry || (failedRequest && !busy)) && (
                    <button
                      type="button"
                      className="button button-primary"
                      onClick={handleRetry}
                    >
                      <RefreshCw size={14} aria-hidden="true" />
                      {hasFailures && !failedRequest
                        ? "Try to fix issues"
                        : "Try again"}
                    </button>
                  )}
                </div>
              </section>
            )}
            {!error &&
              snapshot?.lifecycle === "running" &&
              !streaming &&
              !loading && (
                <div className="notice notice-info notice-row">
                  <p>
                    This design hasn’t finished. Check for its latest saved
                    result.
                  </p>
                  <button
                    className="button button-small"
                    type="button"
                    onClick={reload}
                  >
                    Check progress
                  </button>
                </div>
              )}
          </div>
          {streaming && (
            <GenerationProgress
              stage={stage || snapshot?.stage}
              onStop={stop}
            />
          )}
          {snapshot?.lifecycle === "needs_input" && (
            <ClarificationForm
              key={snapshot.id}
              snapshot={snapshot}
              disabled={disabled}
              onRun={run}
            />
          )}
          {!snapshot ? (
            <>
              {!error && (
                <section className="loading-workspace">
                  <div className="loading-part">
                    <PartIllustration role="controller" />
                  </div>
                  <p>
                    {isRestoring
                      ? "Opening your saved design…"
                      : "The component map will take shape here."}
                  </p>
                </section>
              )}
              {error && runId && (
                <div className="empty-state">
                  <Link to="/" className="button">
                    New device <ArrowUpRight size={14} aria-hidden="true" />
                  </Link>
                </div>
              )}
            </>
          ) : (
            <>
              <div className="workbench">
                <div className="workspace-navigation">
                  <div
                    className="workspace-tabs"
                    role="tablist"
                    aria-label="Design views"
                  >
                    {DESIGN_VIEWS.map(([id, label], index) => (
                      <button
                        key={id}
                        type="button"
                        ref={(element) => {
                          tabRefs.current[index] = element;
                        }}
                        id={`tab-${id}`}
                        role="tab"
                        aria-selected={view === id}
                        aria-controls={`view-${id}`}
                        tabIndex={view === id ? 0 : -1}
                        onClick={() => setView(id)}
                        onKeyDown={(event) => handleTabKeyDown(event, index)}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  <span
                    role="status"
                    className={`review-status ${!isReviewing && snapshot.compatibility ? `status-${snapshot.compatibility}` : ""}`}
                    title={
                      !isReviewing && snapshot.compatibility === "checked"
                        ? "No explicit functional or electrical error was identified by the performed checks."
                        : undefined
                    }
                  >
                    {!isReviewing && snapshot.compatibility === "checked" && (
                      <Check size={14} aria-hidden="true" />
                    )}
                    {isReviewing
                      ? error
                        ? "Not finished"
                        : "Review in progress"
                      : snapshot.compatibility
                        ? COMPATIBILITY_LABELS[snapshot.compatibility]
                        : "No review result"}
                  </span>
                </div>
                <section
                  id="view-system"
                  role="tabpanel"
                  aria-labelledby="tab-system"
                  hidden={view !== "system"}
                  className="workspace-view"
                >
                  {view === "system" && (
                    <div
                      className={`system-layout${selectedComponentId ? " has-selection" : ""}`}
                    >
                      <div className="system-main">
                        <SystemMap
                          snapshot={snapshot}
                          selectedId={selectedComponentId}
                          onSelect={handleSelectComponent}
                        />
                      </div>
                      {inspector}
                    </div>
                  )}
                </section>
                <section
                  id="view-bom"
                  role="tabpanel"
                  aria-labelledby="tab-bom"
                  hidden={view !== "bom"}
                  className="workspace-view"
                >
                  {view === "bom" && (
                    <>
                      <PartsList
                        snapshot={snapshot}
                        selectedId={selectedComponentId}
                        onSelect={handleSelectComponent}
                      />
                      {inspector}
                    </>
                  )}
                </section>
              </div>
              {(snapshot.assumptions.length > 0 ||
                snapshot.configuration_notes.length > 0 ||
                blockingFindings.length > 0 ||
                snapshot.support_needs.length > 0 ||
                snapshot.source_support_needs.length > 0) && (
                <details
                  className="build-notes"
                  ref={notesRef}
                  open={blockingFindings.length > 0 || undefined}
                >
                  <summary>
                    Build notes <ChevronDown size={15} aria-hidden="true" />
                  </summary>
                  <ReviewPanel
                    snapshot={snapshot}
                    onSelect={handleSelectComponent}
                  />
                </details>
              )}
            </>
          )}
        </main>
      )}
    </div>
  );
}
