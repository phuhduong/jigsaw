# Jigsaw backend

One explicit Python workflow turns a device request into real catalog parts, source
evidence, necessary support components, compatibility findings, and a pre-layout BOM.
LangChain is the model interface, not the orchestrator. Python owns state, stage order,
checks, resource limits, and completion.

The working scope is common low-voltage embedded devices, not PCB or schematic design.
A fresh unattended Flash-Lite sensor baseline passed an
[independent source audit](evaluations/prompt18-sensor-audit.md); its sourcing was partial.
See [verification results](evaluations/results.md) for actual runs, failures, and limits.
One successful example is not a reliability claim for arbitrary requests.

The [cleanup pass](evaluations/cleanup-review.md) passes local tests and preserves saved-run
results. Its fresh trials did not yield another independently accepted BOM; final live
verification remains open. After a quota reset, one fresh run was labeled checked but failed
independent source review for capacitor double allocation and unestablished regulator support.
The applicable code checks match the baseline; model review is still fallible.

## Setup and run

Use Python 3.11+ and start the [DigiKey MCP service](../mcp-server/README.md) first.
From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.template .env
# Supply GEMINI_API_KEY in .env.
python app.py
```

On Windows activate with `.venv\Scripts\activate`. The template contains placeholders.
DigiKey credentials belong in the MCP service, never the frontend.

The backend binds to `127.0.0.1:3001`, with threads and no debug/reloader. It admits
one run per process; another start returns 409 while health, retrieval, and exports
remain available. Keep both services local/private: authentication, multiple workers,
shared admission, and durable background jobs are not implemented.

Runs execute inside their streaming request. After a detected disconnect no new work
starts, but an in-flight external call may finish first. Restart marks unfinished saved
runs interrupted; it does not resume them. Importing `app` does not create the application
or touch saved runs. Alternate local launchers should use `create_app()`.

## Code map

| Module | Responsibility |
|---|---|
| `app.py` | Request validation, single-run admission, SSE, retrieval and exports |
| `pipeline.py` | Stage order, applying proposals, source ownership and bounded repair |
| `stages.py` | Plan/select/review model calls and the observed capacitor-value mismatch guard |
| `prompts.py` | Stage instructions and shared BOM/configuration rules |
| `models.py` | Saved records and structured model-response schemas |
| `checks.py` | Named evidence, requirement, support, power, interface and regulator checks; outcomes |
| `documents.py` | Bounded source download/cache, original-page input and quotation matching |
| `tools.py` | Narrow supplier calls through the existing MCP service |
| `llm.py` | LangChain model construction, usage accounting, quota scheduling and bounded retry |
| `run_store.py` | Atomic snapshots, model-facing projections, purchasing quantities and JSON/CSV |

The flow is plan → select → read sources/add support → check/review → bounded
correction → saved result. New active support receives its own source reading.
There is no agent framework, task queue, rule engine, database, or separate purchasing state.

`DesignRun` is the working record. `Requirement.component_ids` is the one active
requirement mapping. Source extraction alone writes verified observations and source-owned
support needs. Assembly/correction references those observations; it cannot replace them.
A source reread replaces that document's packet, retaining applicable earlier facts/pages.
Part replacement invalidates the replaced owner's evidence, including shared-document variants.
Changes invalidate the old review; code findings and badges are recomputed consistently.

## Configuration and limits

`create_app()` reads the adjacent `.env`; process environment values take precedence.

| Setting | Default / purpose |
|---|---|
| `GEMINI_API_KEY` | Required for the Google integration |
| `MODEL` / `MODEL_PROVIDER` | `gemini-3.5-flash-lite` / `google_genai` |
| `MODEL_THINKING_LEVEL` | Unset; provider default |
| `MODEL_PDF_INPUT` | `true`; a capability declaration, not automatic verification |
| `MODEL_RPM` / `MODEL_TPM` | `15` / `250000`; local request/input-token scheduling |
| `MODEL_CONTEXT_TOKENS` | `1048576`; per-call input estimate plus output allowance |
| `MCP_SERVER_URL` | `http://localhost:8080` |
| `PORT` / `FRONTEND_ORIGIN` | `3001` / `http://localhost:5173` |
| `DATA_DIR` | `backend/data`, containing `runs/` and `documents/` |
| LangSmith settings | Optional tracing; keep disabled unless deliberately configured |

Set quotas to the actual account allowance. Other providers may require another integration
package, credentials, and verified structured-output/PDF support. There is no automatic paid
fallback. Runs record model, provider/thinking settings and prompt version.

Default per-run limits in `models.py`: 8 minutes, 30 model requests, 300,000 input tokens,
64,000 output tokens, 60 supplier calls, 20 downloads, 120 PDF page inputs including repeats,
8 primary functional blocks, 40 physical placements, and 2 corrections. Downloads are
limited to 15 MiB each. These are resource ceilings, not completion guarantees.

Model attempts have at most 45 seconds; supplier/document operations normally have at most
20 seconds, reduced by remaining run time. MCP initialization/authentication/lookup share one
deadline. The gateway counts at most one schema/transient retry, disables SDK retries, and
stops on provider quota exhaustion. It reserves estimated input and maximum output, then
reconciles reported usage. Local quota waits emit progress in chunks of at most 50 seconds;
a wait exceeding remaining run time ends the run. The browser has a separate 10-minute
stream timeout. DNS, local PDF parsing, or an in-flight blocking call can overrun nominal
deadlines; this is not a hard real-time execution sandbox.

## What is checked

“Compatibility checked” means the selected parts have a feasible common operating
configuration backed by the available evidence, with no unresolved material issue after
the implemented code checks and source-assisted model review. This covers requested
functions, supply ranges and current capacity, logic levels, available interfaces/resources,
exact variants, and necessary support values/ratings/counts.

It does not require numbered pins, nets, wiring procedures, a complete programming-pad
plan, or schematic/layout generation. Programming feasibility and external-tool assumptions
matter only when they affect required parts. USB-C power alone does not request a USB bridge.
Purchased assemblies may integrate functions, but their actual module boundaries, exposed
interfaces, supply inputs and remaining rail capacity must be checked.

Selection uses real search results, at most three candidates per query and one broader
retry. Product details must confirm the selected manufacturer/MPN. Proven nominal-capacitance
mismatches are rejected; missing/ranged catalog values remain for review. Exact-part labeled
catalog fields can establish commodity passive/connector values and ratings when the current
review explicitly names the parts, fields and product URL. Active devices/modules still need
manufacturer evidence; suppliers never become synthetic parts.

PDF extraction receives original selected pages, including diagrams, plus text/physical-page
labels. Review sees those original pages again, without duplicate extracted PDF text.
HTML currently supplies text and links, not embedded figure pixels. Content hashes, source
ownership, page checks and matching quotations establish traceability—not infallible
interpretation. Navigation summaries are not evidence that a page was read.

Source-observed support needs cannot disappear during assembly. Required/recommended parts
must be resolved with selected placements, actual internal inclusion, or a justified omission.
The reviewer independently looks for omitted support and wrong values. Peak loads determine
supply capacity. Linear-regulator thermal screening uses those loads unless a separately
justified average is declared; code calculates allowance from ambient, junction target and
source-owned package thermal resistance. This remains a conditioned estimate for later layout,
not measured board performance. Interface checks cover applicable bidirectional logic and
pull-up domains without a per-wire pin plan.

The complete review runs even when code operands are missing, so correction sees both
numeric and source-interpretation problems. Mapping-only repairs skip regeneration, not
review. Unchanged parts with sufficient evidence can receive a complete corrected configuration
directly. Part/source changes use the normal selection/reading path. Every accepted repair
requires fresh whole-BOM review; it cannot override a code failure or rewrite a user requirement.

Only facts used or needed for a material BOM claim block the result. Discarded unused facts
and ordinary later implementation advice remain guidance and cannot support a passing claim.
This is a pre-layout assessment, not a tested PCB, compliance certification, or guarantee.

## Outcomes and purchasing

The report separates three statuses:

- Lifecycle: `running`, `needs_input`, `finished`, `interrupted`, or `error`.
  Normal completion can still contain unresolved issues or exhausted budgets.
- Compatibility: `issues_found` for current failed checks, otherwise `incomplete`
  for material unknowns/unfinished review, otherwise `checked`.
- Sourcing: `available`, `partial`, or `unknown`, independently of compatibility.

Findings identify code versus model review and blocking checks versus guidance. Historical
wiring fields, the inverse component requirement map, and the old thermal watt scalar remain
readable but are omitted from new schemas/reports.

BOM rows group exact matching parts and derive installed, build and order quantities,
including MOQ/order multiples. Candidate selection also sees actual order quantities and
extended costs. Available ordinary packaging is preferred over explicit Digi-Reel custom
reeling, then ranked by order cost. Custom-only offers disclose unquoted setup fees.
Unknown price/stock is never zero or presumed available; missing order multiples require
checkout confirmation. Shipping/tax are excluded.

Inherited offers refresh before planning if their age plus the remaining budget would exceed
15 minutes. Failed refreshes leave offers unknown; finalization does not silently change
prices after review. Exports are historical snapshots, not promises of current stock.
The system never places orders.

## API

Start with `POST /api/component-analysis`:

```json
{"query":"A temperature and humidity sensor with WiFi and Bluetooth powered by USB-C",
 "options":{"board_quantity":1,"region":"US","currency":"USD"}}
```

Options are optional, with the defaults shown. The response is `text/event-stream`.
Every JSON `data:` event has `type`, `run_id`, and increasing `sequence`.
Types are `started`, `progress`, `snapshot`, and terminal `complete`/`error`.
Snapshots contain the complete saved record plus derived `bom`. Replace client state
with each snapshot; ignore older runs/sequences. `complete` is not a compatibility badge.
Clarification completes with lifecycle `needs_input`; EOF without a terminal event is
an interruption.

Refine with exactly one instruction:

```json
{"base_run_id":"<saved-id>","modification":"Add another sensor"}
```

```json
{"base_run_id":"<saved-id>","answers":{"<pending-question-id>":"Indoor use"}}
```

`POST /api/refine` loads the full saved record, inherits purchasing options, and creates
a new run/revision. Answers must match all pending question IDs. Do not send a flattened BOM.
A running base returns 409; unknown IDs return 404; invalid requests return 400.

| Endpoint | Result |
|---|---|
| `GET /api/runs/<id>` | Latest saved snapshot with BOM |
| `GET /api/runs/<id>/export?format=csv` | Grouped BOM; formula-leading cells escaped |
| `GET /api/runs/<id>/export?format=json` | Full report, evidence, assumptions and usage |
| `GET /health` | Server/admission status, not a credential test |
| `POST /api/query`, `POST /api/continue` | Retired; 410 for legacy clients |

Initial failures are HTTP errors; failures after streaming starts are terminal events when
possible. Retrieve the saved ID after transport loss. No stream replay or automatic restart
is implemented. Snapshots are atomically replaced under `DATA_DIR/runs`; runtime data and
credentials must not be committed.

## Verification

From `backend/`:

```bash
.venv/bin/python -m unittest discover -s tests
```

Tests use short deterministic core/error paths and local model, supplier and document fakes.
The suite includes the Python MCP boundary. Run `npm test` in `mcp-server/`, and
`yarn typecheck` plus `yarn build` in `frontend/` for the connected code.
No unit test uses live models or networks.

An opt-in live run consumes provider quota; start both backend services first:

```bash
.venv/bin/python evaluations/run_live.py --record data/evaluations/my-run.jsonl
```

The helper sends the original sensor query without component/page guidance, records all SSE
events without overwriting an existing file, and fails unless compatibility is checked.
It also accepts `--query`, `--url`, or a refinement pair `--base-run-id`/`--modification`.
A passing badge still needs source-based inspection of the actual parts, support, operating
bounds, current/thermal assumptions and purchase quantities. Keep live audits separate from
unit tests; record failures as well as successes in [results.md](evaluations/results.md).

The [current architecture](../docs/architecture/practical-bom-workflow.md) explains the
decisions. The earlier design-compiler document is historical, not an implementation plan.
