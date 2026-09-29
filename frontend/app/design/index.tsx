import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";
import { ArrowLeft, Loader2, Square, RefreshCw } from "lucide-react";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Card } from "../components/ui/card";
import { API_CONFIG } from "../services/api/config";
import { getSavedRun, safeUrl, streamRun } from "../services/api/designRunApi";
import type { DesignSnapshot, RunRequest } from "../services/api/designRunApi";
import PartsList from "./PartsList";

const compatibilityLabels = { checked: "Compatibility checked", issues_found: "Compatibility issues found", incomplete: "Compatibility review incomplete" };

export default function DesignInterface({ initialQuery = "", runId = null }: { initialQuery?: string; runId?: string | null }) {
  const navigate = useNavigate();
  const [snapshot, setSnapshot] = useState<DesignSnapshot | null>(null);
  const [query, setQuery] = useState(initialQuery);
  const [modification, setModification] = useState("");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState("");
  const [error, setError] = useState<string | null>(null);
  const controller = useRef<AbortController | null>(null);
  const generation = useRef(0);
  const activeRunId = useRef<string | null>(null);

  const run = useCallback(async (request: RunRequest) => {
    controller.current?.abort();
    const current = new AbortController();
    controller.current = current;
    const ticket = ++generation.current;
    activeRunId.current = null;
    let sequence = 0;
    setBusy(true);
    setError(null);
    setAnswers({});
    setProgress("Starting design analysis…");
    if ("query" in request) setSnapshot(null);
    try {
      await streamRun(request, event => {
        if (generation.current !== ticket) return;
        if (activeRunId.current && activeRunId.current !== event.run_id) return;
        if (event.sequence <= sequence) return;
        if (!activeRunId.current) {
          activeRunId.current = event.run_id;
          void navigate(`/design?run=${encodeURIComponent(event.run_id)}`, { replace: true, state: null });
        }
        sequence = event.sequence;
        if (event.snapshot) setSnapshot(event.snapshot);
        if (event.message || event.stage) setProgress(event.message || event.stage!.replaceAll("_", " "));
        if (event.type === "error") setError(event.message || event.snapshot?.terminal_reason || "Analysis could not finish.");
      }, current.signal);
      if (generation.current === ticket) setModification("");
    } catch (failure) {
      if (generation.current === ticket) setError(failure instanceof Error ? failure.message : "Analysis could not finish.");
    } finally {
      if (generation.current === ticket) {
        setBusy(false);
        controller.current = null;
      }
    }
  }, [navigate]);

  const loadSaved = useCallback(async (id: string) => {
    controller.current?.abort();
    const current = new AbortController();
    controller.current = current;
    const ticket = ++generation.current;
    activeRunId.current = id;
    setBusy(true);
    setError(null);
    setProgress("Loading saved result…");
    try {
      const saved = await getSavedRun(id, current.signal);
      if (generation.current !== ticket) return;
      setSnapshot(saved);
      setError(null);
      setProgress(saved.lifecycle === "running" ? "The backend is finishing its current operation. Reload again shortly." : saved.terminal_reason);
    } catch (failure) {
      if (generation.current === ticket) setError(failure instanceof Error ? failure.message : "Could not retrieve the saved run.");
    } finally {
      if (generation.current === ticket) {
        setBusy(false);
        controller.current = null;
      }
    }
  }, []);

  useEffect(() => {
    // Publishing the current stream's ID must not abort it or reload its snapshot.
    if (runId && runId === activeRunId.current) return;
    controller.current?.abort();
    generation.current += 1;
    activeRunId.current = null;
    setSnapshot(null);
    setAnswers({});
    setModification("");
    setError(null);
    setBusy(false);
    setProgress("");
    setQuery(initialQuery);
    let cancelled = false;
    // Defer starts so a development remount can cancel before making a request.
    queueMicrotask(() => {
      if (cancelled) return;
      if (runId) void loadSaved(runId);
      else if (initialQuery.trim()) void run({ query: initialQuery });
    });
    return () => { cancelled = true; };
  }, [initialQuery, runId, run, loadSaved]);

  useEffect(() => () => {
    controller.current?.abort();
    generation.current += 1;
  }, []);

  const reload = () => {
    const id = activeRunId.current ?? runId;
    if (id) void loadSaved(id);
  };

  const canRefine = snapshot && snapshot.lifecycle !== "running" && !busy;
  const findings = snapshot?.findings.filter(item => item.revision === snapshot.revision) ?? [];
  const outstanding = findings.filter(item => item.kind === "check" && ["fail", "unknown"].includes(item.status));
  const lifecycle = snapshot?.lifecycle.replaceAll("_", " ");

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <header className="border-b border-zinc-800 bg-zinc-900/50 px-6 py-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate("/")} className="text-zinc-400"><ArrowLeft className="w-4 h-4" /> Back</Button>
          <h1 className="text-xl">Jigsaw <span className="text-zinc-500 text-sm ml-2">Pre-layout BOM</span></h1>
        </div>
        {snapshot && <span className="text-xs text-zinc-500">Revision {snapshot.revision} · {lifecycle}</span>}
      </header>

      <p className="px-6 py-3 bg-amber-950/50 text-amber-300 text-sm">Experimental: compatibility checks apply to the recorded parts and assumptions, not a tested PCB. Review the evidence and open issues before ordering parts.</p>

      {API_CONFIG.useMock && <div className="px-6 py-3 bg-amber-950/50 text-amber-300 text-sm">Demo mode is enabled. Live analysis is disabled.</div>}

      <main className="max-w-[1500px] mx-auto grid lg:grid-cols-[minmax(0,1fr)_420px]">
        <div className="p-6 space-y-6 min-w-0">
          <Card className="bg-zinc-900/50 border-zinc-800 p-5">
            <h2 className="text-lg mb-3">{snapshot ? "Device request" : "Describe your device"}</h2>
            {snapshot ? <p className="text-zinc-300 whitespace-pre-wrap">{snapshot.original_request}</p> : <form onSubmit={event => { event.preventDefault(); void run({ query: query.trim() }); }}>
              <Textarea aria-label="Device requirements" value={query} onChange={event => setQuery(event.target.value)} maxLength={10000} placeholder="A temperature and humidity sensor with WiFi and Bluetooth, powered by USB-C…" className="bg-zinc-950 border-zinc-700 min-h-28" disabled={busy} />
              <Button type="submit" disabled={busy || !query.trim() || API_CONFIG.useMock} className="mt-3 bg-emerald-600 hover:bg-emerald-500">Generate BOM</Button>
            </form>}
            {snapshot?.summary && <p className="text-sm text-zinc-400 mt-4">{snapshot.summary}</p>}
          </Card>

          <div aria-live="polite" className="space-y-3">
            {busy && <div className="flex items-center justify-between gap-4 text-sm text-emerald-400"><span className="flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin shrink-0" />{progress || "Analysis in progress…"}</span><Button variant="outline" size="sm" onClick={() => controller.current?.abort()} className="border-zinc-700 text-zinc-300"><Square className="w-3 h-3" /> Stop</Button></div>}
            {error && <p role="alert" className="border border-red-900 bg-red-950/30 text-red-300 p-4 rounded-lg text-sm">{error}</p>}
            {!busy && !snapshot && runId && <Button variant="ghost" size="sm" onClick={reload} className="text-zinc-400"><RefreshCw className="w-3 h-3" /> Retry saved result</Button>}
            {!busy && snapshot && <div className="flex flex-wrap items-center gap-3">
              <span className={`text-sm ${snapshot.compatibility === "checked" && !error ? "text-emerald-400" : "text-amber-400"}`}>{error ? "Request did not finish successfully — see error above" : compatibilityLabels[snapshot.compatibility]}</span>
              <Button variant="ghost" size="sm" onClick={() => void reload()} className="text-zinc-400"><RefreshCw className="w-3 h-3" /> Reload saved result</Button>
            </div>}
            {!busy && snapshot?.terminal_reason && <p className="text-sm text-zinc-400">{snapshot.terminal_reason}</p>}
            {!busy && progress && snapshot?.lifecycle === "running" && <p className="text-sm text-zinc-400">{progress}</p>}
          </div>

          {snapshot?.lifecycle === "needs_input" && <Card className="bg-zinc-900/50 border-amber-900 p-5">
            <h2 className="text-lg mb-4">A little more detail is needed</h2>
            <form onSubmit={event => { event.preventDefault(); void run({ base_run_id: snapshot.id, answers }); }} className="space-y-4">
              {snapshot.pending_questions.map(question => <label key={question.id} className="block text-sm text-zinc-300">
                {question.question}{question.guidance && <span className="block text-xs text-zinc-500 mt-1">{question.guidance}</span>}
                <Textarea value={answers[question.id] ?? ""} onChange={event => setAnswers(previous => ({ ...previous, [question.id]: event.target.value }))} className="mt-2 bg-zinc-950 border-zinc-700" required disabled={busy} maxLength={10000} />
              </label>)}
              <Button type="submit" disabled={busy || !snapshot.pending_questions.every(question => answers[question.id]?.trim())} className="bg-emerald-600 hover:bg-emerald-500">Continue design</Button>
            </form>
          </Card>}

          {snapshot && <>
            {snapshot.assumptions.length > 0 && <Card className="bg-zinc-900/50 border-zinc-800 p-5">
              <h2 className="text-lg mb-3">Design assumptions</h2>
              <ul className="list-disc pl-5 space-y-2 text-sm text-zinc-400">{snapshot.assumptions.map(item => <li key={item.id}>{item.description}</li>)}</ul>
            </Card>}

            {snapshot.components.some(item => !item.product) && <Card className="bg-zinc-900/50 border-amber-900 p-5">
              <h2 className="text-lg mb-3">Unresolved selections</h2>
              {snapshot.components.filter(item => !item.product).map(item => <p key={item.id} className="text-sm text-amber-300 mt-2">{item.id} · {item.name}: {item.selection_error || "Selection pending"}</p>)}
            </Card>}

            <Card className="bg-zinc-900/50 border-zinc-800 p-5">
              <h2 className="text-lg mb-2">Compatibility review</h2>
              <p className="text-xs text-zinc-500 mb-4">Source-assisted model review and explicit code checks. {outstanding.length} unresolved check(s). This is a pre-layout review, not a finished schematic or tested PCB.</p>
              {!findings.length && <p className="text-sm text-zinc-500">No review results yet.</p>}
              <div className="space-y-3">{findings.map(finding => <details key={finding.id} open={finding.kind === "check" && ["fail", "unknown"].includes(finding.status)} className="border border-zinc-800 rounded-md p-3">
                <summary className="cursor-pointer text-sm"><span className={finding.status === "pass" ? "text-emerald-400" : finding.status === "fail" ? "text-red-300" : "text-amber-300"}>{finding.status.replaceAll("_", " ")}</span><span className="text-zinc-300 ml-2">{finding.area} · {finding.kind === "guidance" ? "guidance" : finding.method === "code" ? "code check" : "model review"}</span></summary>
                <p className="text-sm text-zinc-400 mt-3">{finding.explanation}</p>
                {finding.remedy && <p className="text-sm text-zinc-300 mt-2">{finding.remedy}</p>}
                <div className="flex flex-wrap gap-3 text-xs text-emerald-400 mt-3">{finding.evidence_ids.map(id => {
                  const evidence = snapshot.evidence.find(item => item.id === id);
                  const document = snapshot.documents.find(item => item.document_id === evidence?.document_id);
                  const url = safeUrl(document?.url);
                  return url && evidence ? <a key={id} href={`${url.split("#")[0]}#page=${evidence.page}`} target="_blank" rel="noopener noreferrer" title={evidence.fact}>{document?.title || id} · p. {evidence.page}</a> : <span key={id} className="text-zinc-500">{id}</span>;
                })}</div>
              </details>)}</div>
            </Card>

            {snapshot.configuration_notes.length > 0 && <details className="border border-zinc-800 bg-zinc-900/30 rounded-xl p-5">
              <summary className="cursor-pointer">Configuration and layout notes</summary>
              <ul className="list-disc pl-5 space-y-2 text-sm text-zinc-400 mt-4">{snapshot.configuration_notes.map((note, index) => <li key={index}>{note}</li>)}</ul>
            </details>}

            {snapshot.lifecycle !== "needs_input" && <Card className="bg-zinc-900/50 border-zinc-800 p-5">
              <h2 className="text-lg mb-3">Refine this design</h2>
              <form onSubmit={event => { event.preventDefault(); void run({ base_run_id: snapshot.id, modification: modification.trim() }); }}>
                <Textarea aria-label="Design modification" value={modification} onChange={event => setModification(event.target.value)} disabled={!canRefine} maxLength={10000} placeholder="Add a second sensor, change the supply, or adjust a requirement…" className="bg-zinc-950 border-zinc-700" />
                <Button type="submit" disabled={!canRefine || !modification.trim()} className="mt-3 bg-emerald-600 hover:bg-emerald-500">Update and recheck</Button>
              </form>
            </Card>}
          </>}
        </div>
        <aside className="border-l border-zinc-800 bg-zinc-900/30 min-w-0"><PartsList snapshot={snapshot} /></aside>
      </main>
    </div>
  );
}
