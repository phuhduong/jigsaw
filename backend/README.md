# Jigsaw backend

An explicit Flask/Python workflow turns a device request into selected components,
manufacturer evidence, a feasible operating configuration, supporting parts, review findings,
and a purchasable pre-layout BOM. LangChain supplies the model interface; Python
owns stage order, state, checks, budgets, and completion.

This local/private development version now has a fresh unattended positive baseline:
run `149dc53304e146f584d6159366e663ee` used the original sensor query, Flash-Lite,
no manual component/source guidance, and finished `checked / partial` in 131.60
seconds. Its 15 placements / 13 MPNs pass [independent source review](evaluations/prompt18-sensor-audit.md)
under the recorded operating assumptions and ordinary pre-layout placement choices.
One bypass capacitor has no supplier price/stock offer; the known $9.34 subtotal
excludes it, and its purchase link remains available. All 59 backend tests pass;
saved state, stream, retrieval and JSON/CSV exports agree. One positive case does
not establish reliability across arbitrary devices. Earlier failed/guided attempts
remain in the [verification progress](evaluations/results.md).

## Setup and run

Use Python 3.11+ and start the [DigiKey MCP server](../mcp-server/README.md) first.
From this directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.template .env
```

Edit `.env`: supply `GEMINI_API_KEY`, confirm `MODEL` is available to your account,
and set `LANGCHAIN_TRACING_V2=false` unless you deliberately configure LangSmith.
The template contains placeholders, not working credentials. On Windows, activate
the environment with `.venv\Scripts\activate`.

```bash
python app.py
```

The server binds to `127.0.0.1:3001`, with request threads, debug/reloader disabled,
and one admitted design run per process. Another start returns HTTP 409; health,
retrieval, and export requests remain available. Do not launch multiple workers or
expose it publicly: authentication, shared admission, and background jobs are not
implemented. Keep the MCP service local too; its production setting exposes a
network listener without application authentication.

Runs execute in their streaming request, not a durable worker. A disconnected
browser can leave the current external call finishing before cancellation is
noticed. No further work is intended after disconnect detection. Restarting the
backend marks unfinished saved runs interrupted; it does not resume provider calls.

## Configuration and budgets

The backend reads `.env` alongside `app.py`. Existing process environment variables
take precedence. DigiKey credentials belong in the MCP server, never the frontend.

| Setting | Default / purpose |
|---|---|
| `GEMINI_API_KEY` | Required for the default Google integration |
| `MODEL` | `gemini-3.5-flash-lite` |
| `MODEL_PROVIDER` | `google_genai`; passed to LangChain's model factory |
| `MODEL_THINKING_LEVEL` | Unset/provider default for the current task; optional Google-model override |
| `MODEL_PDF_INPUT` | `true`; capability declaration, not automatic model verification |
| `MODEL_RPM` / `MODEL_TPM` | `15` / `250000`; local request/input-token scheduling limits |
| `MODEL_CONTEXT_TOKENS` | `1048576`; per-call input estimate plus output allowance |
| `MCP_SERVER_URL` | `http://localhost:8080` |
| `PORT` / `FRONTEND_ORIGIN` | `3001` / `http://localhost:5173` |
| `DATA_DIR` | `backend/data`; contains `runs/` and `documents/` |
| LangSmith settings | Optional tracing; may send prompts and source material externally |

Set quota limits to your actual project allowance; these defaults do not establish
free-tier availability. Other LangChain providers may need an additional integration
package, their own credentials, and verified structured-output/PDF support. Changing
the provider name alone does not prove equivalent capability. There is no automatic
provider switch or paid fallback. New full runs save provider/thinking settings in
`model_configuration`, alongside `model` and `prompt_version`, so comparisons can
identify configuration changes. An explicit thinking level is not evidence of
better design accuracy.

`models.py` defines the default per-run limits: 8 minutes, 30 model requests,
300,000 input tokens, 64,000 output tokens, 60 supplier calls, 20 documents,
120 PDF page inputs including repeated reads, 8 primary functional blocks,
40 component placements, and 2 correction rounds. `documents.py` limits each
download to 15 MiB. These are starting resource limits, not promised completion
times. They are not currently request-level configuration options.

These budgets remain unchanged for the narrowed BOM task, with 4,000 requested
output per source extraction and Flash-Lite/provider-default thinking. Scheduling
remains 15 RPM/250,000 TPM, subject to actual account quotas. Historical budget/model
experiments are in the [progress record](evaluations/results.md); they do not
establish success for this scope. There is no automatic paid fallback or further
budget increase in this task.

Model attempts normally have at most 45 seconds; supplier/document operations
normally have at most 20 seconds, reduced to remaining run time. Supplier MCP
initialization, OAuth, and lookup share one logical deadline. There are no hidden
supplier retries; model schema/transient retries are bounded and counted. A model
quota error stops the run instead of repeatedly retrying. Requests reserve estimated
input and maximum output, then reconcile reported usage. DNS, local PDF parsing,
or an in-flight blocking call can overrun a nominal deadline; this is not a hard
real-time execution sandbox. Local rate-limit waits emit progress and sleep in
chunks of at most 50 seconds; they stop if the required wait exceeds remaining
run time, not merely because it exceeds one chunk. The browser has a separate
10-minute stream timeout.

## What the result means

The product selects a BOM, not a schematic or wiring design. “Compatibility checked”
requires an evidence-backed feasible common operating configuration for the chosen
parts: compatible operating ranges, a credible current budget, suitable logic levels,
and sufficient available interfaces/resources. Necessary supporting components must
have selected parts, values/ratings, quantities, and clear purposes. Numbered pin
assignments, nets, and a complete programming/reset pad plan are not required.
Programming feasibility and any external-tool assumption matter when they affect
the parts needed, not as a wiring deliverable.

The workflow plans requirements and assumptions, selects up to three real catalog
candidates per query, confirms the selected manufacturer/MPN with product details,
and reads relevant source pages. The selected MPN replaces the planning name;
preselection document hints are cleared so another part's guide is not inherited.
Additional guides can then be discovered for the actual selected part.
An explicit nominal capacitance in a search query is checked against the labeled
catalog capacitance before selection and again against confirmed product details.
Equivalent SI values are normalized; proven mismatches are rejected. MPN-only
hints, ranges and missing catalog values remain subject to the ordinary source
review, not an invented deterministic approval.
For commodity passives/connectors, labeled exact-part supplier fields can establish
type, value, and ratings when the current evidence reviewer explicitly names the
component, relevant fields, and product URL. This does not replace manufacturer
evidence for active devices/modules or necessary support-purpose evidence; missing
material ratings remain unresolved. A manufacturer PDF is not mandatory per BOM row.
Each document gets a focused extraction call with manufacturer/MPN/package context;
its packet must establish applicability for each referenced selected component.
Python validates source/page references and text quotations into an observation
ledger. A separate BOM/support-proposal call references that ledger without rewriting
its observations, and proposes necessary parts and an operating configuration. Named code checks
and whole-BOM model review follow; the reviewer still receives the original
relevant PDF pages, not just the ledger. Corrections remain in the same bounded
Python workflow, with renewed source interpretation where needed.
Review runs before correction even when code checks have numeric gaps, so the
bounded repair receives both calculation and source-interpretation findings.
Corrections can explicitly reread an affected component's source even when the
needed fact was omitted from an already-interpreted page. Unaffected source packets
remain available to the complete review. A mapping-only correction skips BOM
regeneration, not the current review. A repair using unchanged selected parts and
existing evidence can return the complete corrected compatibility record directly,
removing the extra instruction-to-assembly model call. That mode cannot add parts
or request source rereads, cannot rewrite source evidence, and still needs fresh
whole-BOM review. Two-part I2C records cover both driving
directions; no per-wire or numbered-pin plan is required.
An off-board programming tool can be a disclosed assumption; do not generate a
mandatory pad/connector wiring plan. An onboard USB bridge needs an explicit request
or a concrete necessity for the selected device; USB-C power alone does not request it.
When suitable, it prefers a documented board-mountable controller assembly with
requested power functions already integrated. The result must disclose a
carrier-board BOM around that purchased assembly and check available exposed interfaces,
form-factor suitability, supply inputs, and rail capacity after onboard loads. Internal parts
are not purchased again; this is not a fixed module whitelist or finished-kit lookup.
Requirements use `req:` IDs, separate from physical component references.
Bounded correction can repair an existing requirement's component-ID mapping without
rewriting its clause or description. It validates the IDs and invalidates the old
review; a mapping repair is not permission to weaken a requirement.
Source-owned support obligations are also retained separately: the BOM proposal
must resolve applicable necessary parts rather than silently drop them. Their roles
distinguish, for example, regulator input versus output capacitors without specifying
a complete wiring plan. A configuration-only repair
can reuse unchanged-part observations when no source gap or unread requested page
requires extraction; it still reruns whole-BOM review. The reading planner now
receives the latest refinement instruction, existing observations, source obligations,
and issues to target missing context. Focused extraction also receives request/
modification and operating assumptions. Retained source pages remain available to review; rereading a shared
source preserves its earlier evidence pages. The first prompt-5 live trial still
ended incomplete with material source-interpretation errors; it did not select
the integrated-assembly route. See the [progress record](evaluations/results.md).
The source-packet handoff supplies same-document, current-owner prior observations/support
to a reread, requesting a complete replacement that preserves correct concrete
facts and corrects mistakes against original pages. A local handoff test does not
establish engineering quality; prior interpretations can anchor old errors. It adds
no merge system or separate state. Historical trials are not proof of the narrowed scope.
Supplier failures never become synthetic components.

PDF extraction sends selected original pages as PDF input, including diagrams,
alongside extracted text and physical-page labels. Whole-BOM review retains the
same original PDF pages and labels but omits duplicate extracted PDF text. HTML
reading and review currently provide text and
links, not embedded figure pixels. Missing sources or unreadable figures block only
when they prevent a material BOM judgment, such as a required support value or
operating limit. Discarded observations and facts for unused modes remain visible
guidance; they must not be used as evidence for a passing claim. A bad citation used
by an active requirement, support need, or numeric operand remains blocking.

Power capacity uses peak/design rail loads. Linear-regulator thermal screening
uses those loads conservatively unless a separate `average_output_current` has
applicable source evidence or a justified workload assumption. It cannot exceed
the peak-load sum or reduce the capacity check. The reviewer must assess the
workload/burst assumptions and the package/ambient basis of the thermal allowance;
this is not measured board thermal performance.
Code computes that allowance from `ambient_max`, `junction_target`, and cited
package `theta_ja`, rather than trusting a model-supplied watt result. A documented
typical thermal resistance remains an estimate tied to its board/copper conditions.
Missing inputs cannot pass. Historical `dissipation_limit` claims remain readable
but are not requested from new model responses or used as a fallback calculation.

Documents are content-hashed and cached locally; valid source
references and matching text quotations establish traceability, not that every model
interpretation is correct. Navigation summaries are capped at approximately 10,000
characters per document and 30,000 across current documents. Omitted pages remain
requestable; these summaries are navigation, not evidence that a page was read.
Open-drain static-high checks use the proposed pull-up supply domain when supplied;
pull-up values and feasible rate/loading assumptions matter to compatibility, not
a chosen numbered-pin mapping or a completed routed-bus analysis.

The report keeps three independent statuses:

- **Lifecycle:** `running`, `needs_input`, `finished`, `interrupted`, or `error`.
  `finished` can include unresolved issues or exhausted work budgets.
- **Compatibility:** `issues_found` for current failed checks; otherwise `incomplete`
  for material BOM unknowns or unfinished coverage; `checked` only after the current required
  checks and model review complete without unresolved check findings.
- **Sourcing:** `available`, `partial`, or `unknown`, based on matched locale offers,
  purchase URLs, known prices, stock, and required order quantities. Compatibility
  alone does not mean parts are available.

Findings distinguish `code` from `model_review`, and blocking `check` findings from
ordinary `guidance`. Assumptions, remaining issues, and configuration/layout notes
stay visible. Missing wiring details alone cannot create blocking findings. This is a
pre-layout BOM assessment, not a schematic, routed PCB, compliance
certification, or guarantee that a built device will work.

Every physical placement has an ID. The BOM groups matching parts and derives
installed/build/order quantities, including known MOQ and order multiples. Unknown
price or stock stays unknown. Missing order multiples require checkout confirmation;
shipping and tax are excluded. Available ordinary packaging is preferred over
explicitly labeled Digi-Reel service, then ranked by the existing order-quantity
price. Ordinary Tape & Reel is not custom reeling. A custom-only selected offer
includes an ordering note that component prices exclude any custom-reeling/setup
fee; no fee is invented. Before planning an inherited design, offers are
refreshed if their retrieval age plus the remaining run budget would exceed
15 minutes. Price constraints therefore see refreshed offers before review;
finalization does not silently change them after that review. Failed refreshes
leave offers unknown. Exports are snapshots, not a promise of current stock, and
the system never places orders.

## API

Start a run with `POST /api/component-analysis`:

```json
{
  "query": "A temperature and humidity sensor with WiFi and Bluetooth powered by USB-C",
  "options": {"board_quantity": 1, "region": "US", "currency": "USD"}
}
```

`options` is optional and defaults to the values shown. A successful start returns
`text/event-stream`. Every `data:` JSON event has `type`, `run_id`, and increasing
`sequence`; it may include `stage`, `message`, and `snapshot`:

```json
{"type":"progress","run_id":"<saved-run-id>","sequence":2,"stage":"select","message":"Searching for a sensor"}
```

Event types are `started`, `progress`, `snapshot`, and terminal `complete` or `error`.
The initial, stage, and terminal snapshots are full saved `DesignRun` records plus
a derived `bom` array. Replace client design state with each snapshot; ignore old
run IDs/sequences. `complete` is a transport outcome, not a compatibility badge.
Clarification ends with `complete` and lifecycle `needs_input`. EOF without a terminal
event is an interruption, not success.

Use `POST /api/refine` with exactly one of these bodies:

```json
{"base_run_id":"<saved-run-id>","modification":"Add a second temperature sensor"}
```

```json
{"base_run_id":"<saved-run-id>","answers":{"<pending-question-id>":"Indoor use"}}
```

Answers must match all pending question IDs. Refinement loads the full saved design,
inherits purchasing options, and creates a new run with `parent_run_id` and a newer
revision. Send a saved ID, not a flattened client BOM. A still-running base returns
409; an unknown base returns 404.

| Endpoint | Result |
|---|---|
| `GET /api/runs/<id>` | Latest saved snapshot, including derived BOM |
| `GET /api/runs/<id>/export?format=csv` | Grouped BOM with source/purchase links and review status |
| `GET /api/runs/<id>/export?format=json` | Full saved design, evidence, findings, assumptions, and usage |
| `GET /health` | Local status and admission `busy`; does not test provider credentials |
| `POST /api/query`, `POST /api/continue` | Retired; HTTP 410 |

Invalid request bodies return 400; unknown saved IDs return 404. Initial failures
are HTTP errors; errors after streaming begins are terminal events when the transport
is still usable. Keep the run ID and retrieve its snapshot after a connection failure;
it may briefly remain `running` while an in-flight call finishes. There is no stream
replay or automatic restart. Run JSON files are atomically replaced in `DATA_DIR/runs`;
local runtime data and credentials should not be committed.

## Verification

Run the deterministic suite from `backend/`:

```bash
.venv/bin/python -m unittest discover -s tests
.venv/bin/python ../mcp-server/tests/test_supplier.py
```

These tests use local fake models, supplier responses, and document downloads; no
live credentials or external network are required. The [MCP tests](../mcp-server/README.md#verification)
cover catalog normalization separately. The frontend's `yarn typecheck` and `yarn build`
verify the coordinated client contract compiles.

The current milestone requires relevant local tests, an actual run of the user's
sensor example with Flash-Lite within the existing budgets, and an independent
source-grounded BOM audit. Inspect exact identities, requested functions, support
parts/values/quantities, feasible operating/current/logic/resource compatibility,
material evidence, purchase links, and matching exports. Do not score absent wiring,
numbered pin assignments, or a complete programming-pad plan as BOM defects.
Record the model/configuration, date, outcome, request/token usage, and actual failures.
The scope changes have 59 passing backend tests. Fresh original-query run
`149dc533` completed current compatibility review within the unchanged budget and
passed the [independent audit](evaluations/prompt18-sensor-audit.md). Its saved
state and all export paths agree. This satisfies the automatic compatibility-BOM
milestone, while preserving the separate partial-sourcing outcome for C4.
Earlier guided results and failed trials are not relabeled as successes.

See the [design's evaluation criteria](../docs/architecture/practical-bom-workflow.md#6-implementation-and-evaluation).
The [manual source oracle](evaluations/sensor_acceptance_oracle.md) and its earlier
three-frozen-trial plan remain historical engineering references, not the current
completion gate. Use applicable source facts without importing the former wiring
deliverables. Diagnostic outcomes remain unchanged in the
[live progress record](evaluations/results.md). One audited run is a concrete
demonstration, not a claim of broad reliability.

With the MCP server and backend running, start one manual live smoke trial from
`backend/`:

```bash
.venv/bin/python evaluations/run_live.py
```

The default is the public USB-C temperature/humidity sensor example. Optional
`--query` and `--url` override the request and backend address. To refine a saved run,
provide both nonblank options below; this uses `/api/refine` instead of a fresh query:

```bash
.venv/bin/python evaluations/run_live.py --base-run-id "<saved-run-id>" --modification "Keep the selected parts and repair the cited compatibility findings."
```

Replace the placeholder with the actual saved ID. A guided refinement must be
reported as such, not as a fresh unattended success. The command prints the run ID,
progress, terminal outcomes, usage, and current failed/unknown checks; it does not
dump credentials or the full design payload. A missing terminal snapshot or an
outcome other than `checked` exits nonzero. No automatic retries or independent
engineering-acceptance claim are implied by this smoke command.
