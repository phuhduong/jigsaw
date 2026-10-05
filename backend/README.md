# Jigsaw backend

One explicit Python workflow turns a device request into real functional components,
source evidence, operating/support notes, compatibility findings, and a pre-layout BOM.
LangChain is the model interface, not the orchestrator. Python owns state, stage order,
checks, resource limits, and completion.

The scope is common low-voltage embedded devices, not schematic design or a complete PCB
parts inventory. Missing functional blocks such as regulators, level translators, and
drivers remain in scope. Routine capacitor, pull-up, feedback, and reset/boot details are
source-grounded notes for schematic work, not mandatory procurement or a completeness gate.
Explicitly requested passives and any parts actually selected still require suitable values
and ratings. Completed reviews report **Checks passed** or **Checks failed** based on identified functional or
electrical compatibility errors. Unknowns and evidence gaps remain inspectable without
blocking acceptance; a run without review has no passing verdict.

See [verification results](evaluations/results.md) for dated live runs and independent audits.
Earlier evaluations used a stricter acceptance gate and broader support-inventory scope.
Historical incomplete runs are not promoted to passes, and changing the verdict does not
establish improved engineering accuracy.

The [prompt-41 cleanup verification](evaluations/results.md#functional-component-cleanup-2026-09-30-prompt-41)
passed 106 local backend tests and one fresh sensor run with four available functional parts,
matching saved reports and exports, eight model calls and no correction rounds. Independent
source inspection found plausible choices but inaccurate or unsupported report claims,
especially for the regulator. That audit is separate from the binary passing badge; one
successful run does not establish general reliability.

The subsequent [reporting handoff audit](evaluations/results.md#reporting-handoff-audit-2026-09-30-unchanged-prompt-41)
found no justified additional backend rewrite. It documented the frontend presentation work
pending at that time and another fresh smoke test of identical runtime code, including its
remaining model scope/reporting limitations. The current frontend implements the reporting
contract below; its verification is recorded in the [project guide](../README.md#verification).

The [October 4 fixed preset batch](evaluations/preset-generalization-2026-10-04.md)
subsequently tested eight requests on unchanged prompt-41 code. Independent audits found
three plausible results, two correct failed verdicts, and three false acceptances involving
power capability or stale configuration after replacement. This includes a failure of the
familiar wireless control; broader reliability remains unestablished. All attempts, sources,
usage, and matching saved/export records are documented without repairing the outputs.

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
| `checks.py` | Named evidence, requirement, power, interface and regulator checks; outcomes |
| `numeric.py` | Shared unit conversion, source-owned operand binding, and existing power/logic arithmetic |
| `documents.py` | Bounded source download/cache, original-page input and quotation matching |
| `tools.py` | Narrow supplier calls through the existing MCP service |
| `llm.py` | LangChain model construction, usage accounting, quota scheduling and bounded retry |
| `run_store.py` | Atomic snapshots, model-facing projections, purchasing quantities and JSON/CSV |

The flow is plan → select → read sources/establish configuration → check/review → bounded
correction → saved result. Missing functional blocks can be added and receive their own
source reading; ordinary passive-support procurement is not a stage requirement.
There is no agent framework, task queue, rule engine, database, or separate purchasing state.

`DesignRun` is the working record. `Requirement.component_ids` is the one active
requirement mapping. Source extraction alone writes verified observations, including relevant
support dependencies. Configuration/correction references those observations; it cannot replace them.
A source reread receives applicable earlier observations and pages as context, then replaces
that document's packet with the newly validated response; retention is not guaranteed by a merge.
Part replacement invalidates the replaced owner's evidence, including shared-document variants.
Extraction explicitly records whether each source applies to each selected variant. A negative
explanation cannot authorize facts for that component. A labeled USB-C connector
also receives the existing manufacturer Type-C hardware guide through normal source processing;
the code does not insert resistor values or assume a port role.
Changes invalidate the old review; code findings and badges are recomputed consistently.
Support guidance stays in evidence observations, configuration notes, and review guidance.
Historical `source_support_needs` and `support_needs` remain readable in saved reports, but
new runs do not create or enforce those fulfillment records. They are omitted from model
context and new response schemas; empty arrays preserve the existing frontend contract.

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
fallback. Runs record model, provider/thinking settings and prompt version, currently `41`.

Default per-run limits in `models.py`: 8 minutes, 30 model requests, 400,000 input tokens,
64,000 output tokens, 60 supplier calls, 20 downloads, 120 PDF page inputs including repeats,
8 primary functional blocks, 40 physical placements, and 2 corrections. Downloads are
limited to 15 MiB each. These are resource ceilings, not completion guarantees.

The input allowance is intended to accommodate two corrections and final source-assisted
review, including its optional source-follow-up pass, but does not guarantee that they fit.
One frozen reliability attempt exhausted it before final review. The 2026-09-30
[budget evaluation](evaluations/results.md#input-budget-evaluation-2026-09-30) records the
measurements behind the increase from 300,000. Other resource limits are unchanged.
Configuration searches only newly added functional parts; an existing failed selection waits for
an explicit correction rather than repeating the same searches during configuration.
Existing saved runs retain their recorded limits; refinements currently inherit those limits.

Model attempts have at most 45 seconds; supplier/document operations normally have at most
20 seconds, reduced by remaining run time. MCP initialization/authentication/lookup share one
deadline. The gateway counts at most one schema/transient retry, disables SDK retries, and
stops on provider quota exhaustion. Read timeouts use that same single retry allowance,
not a separate retry loop. It reserves estimated input and maximum output, then
reconciles reported usage. Local quota waits emit progress in chunks of at most 50 seconds;
a wait exceeding remaining run time ends the run. The browser has a separate 10-minute
stream timeout. DNS, local PDF parsing, or an in-flight blocking call can overrun nominal
deadlines; this is not a hard real-time execution sandbox.

## What is checked

“Checks passed” means a completed review identified no explicit functional or electrical
compatibility error. “Checks failed” means it identified at least one. Review still covers
requested functions, supply ranges and current capacity, logic levels, available
interfaces/resources, exact variants, and necessary functional blocks.
The verdict is not a claim that every compatibility question has been resolved. Unknowns,
coverage gaps, and evidence/reporting defects remain nonblocking review details.

It does not require numbered pins, nets, wiring procedures, a complete programming-pad
plan, or schematic/layout generation. Programming feasibility and external-tool assumptions
matter only when they affect required parts. USB-C power alone does not request a USB bridge.
Purchased assemblies may integrate functions, but their actual module boundaries, exposed
interfaces, supply inputs and remaining rail capacity must be checked.

Interfaces use numerical driver/receiver limits. A shared protocol or nominal voltage alone
is insufficient. Numerical checks and address conflicts still block when they fail.
Single-part radio capability records need their own source-backed current review, not an
invented second component; a one-ended I2C bus remains unresolved. Prefer capability evidence
and ordinary off-board programming assumptions in requirements/notes, without extra interfaces.

The existing `passive` category includes bare current-limited indicator LEDs and dry-contact
switches, not smart LEDs or driver ICs. Their ratings, current limiting and contact/input
behavior require source/catalog review; invented supply ranges or active-driver thresholds do
not. A passive rail entry may omit both IC-style operating bounds when a current power review
names its rail and component and checks the actual ratings/arrangement. Its current remains in
the rail total. A passive signal receiver without digital thresholds needs a current driver/load
review with driver evidence and load evidence or reviewed catalog ratings. Any supplied numerical
limits remain checked; active devices do not receive these exceptions. Missing requirement
mapping details remain distinct from an identified failure to provide the requested function.

Selection uses real search results, at most three candidates per query and one broader
retry. Product details must confirm the selected manufacturer/MPN. Proven nominal-capacitance
mismatches are rejected; missing/ranged catalog values remain for review. A missing datasheet
URL alone does not reject a catalog part. Source discovery follows selection using available
datasheet, supplemental-guide, or product-page leads; unsuccessful discovery remains an evidence
gap. Exact-part labeled catalog fields and product URLs are supplied for model review of selected passive/connector
values and ratings. Code requires catalog parameters, a product URL and a current passing
evidence finding naming the part; field interpretation remains model judgment. Active
device/module ratings seek manufacturer evidence without making missing evidence a failed
verdict. Suppliers never become synthetic parts.

PDF extraction receives original selected pages, including diagrams, plus text/physical-page
labels. Review sees those original pages again, without duplicate extracted PDF text.
HTML currently supplies text and links, not embedded figure pixels. Content hashes, source
ownership, page checks and matching quotations establish traceability—not infallible
interpretation. Navigation summaries are not evidence that a page was read.

New workflows use numeric binding version 1. Extraction records typed source numbers inside
the evidence observations. Configuration references those numbers; code materializes the existing
public quantity values, units and citations. Ownership and parameter roles prevent an input
supply requirement from becoming output capacity or a source's 379 mA demand becoming 250 mA.
Source conditions travel with the resolved operands. Binding and checks share
`numeric.convert_value` for supported units and dimensions. The resolver covers direct ratings,
output tolerance, supply-scaled logic thresholds, regulator input headroom and linear input
current. It is not a general expression engine. Source interpretation and applicability remain
fallible and require the original-page review. Executing/refining a run enables the current
binding contract. An unbound device rating remains an unknown calculation, not a proven
rating or an automatic failed verdict.
An explicit, justified design margin may widen the source-derived delivered output interval.
It remains labeled an estimate, retains source conditions, and cannot narrow that interval or
alter a device rating. This supports conservative compatibility screening without building a
general datasheet-coefficient calculator.

A single mistyped voltage-limit ID or an Evidence ID can resolve to an existing number when
owner, parameter, min/max bound and unit identify exactly one match. Ambiguous, missing-data
and known wrong-owner/role references remain unresolved; there is no guessed numerical value.
Equivalent microamp spellings are accepted. A non-converter sensor's documented active current
may be called quiescent current; its source conditions remain visible and require review.
Converter own current cannot stand in for the load it powers.

Support awareness remains important. A bare 3.3 V module does not acquire a 5 V regulator
merely because routine support procurement is deferred. Likewise, an adjustable converter's
output assumption must be consistent with its documented configuration. Record the necessary
external network as guidance without requiring every passive SKU, count, or fulfillment link.
A separate review call using the same model looks for missing functional blocks and wrong
selected parts. Independent source audits are development verification, not an additional
automatic production stage. Peak loads determine supply capacity.
Linear-regulator thermal screening uses those loads unless a separately justified average
is declared; code calculates allowance from ambient, junction target and
source-owned package thermal resistance, and includes input voltage times regulator own current
in the dissipation estimate. Linear input demand reuses the downstream peak sum plus own current.
This remains a conditioned estimate for later layout, not measured board performance.
Interface checks cover applicable bidirectional logic and
pull-up domains without a per-wire pin plan.

The complete review runs even when code operands are missing. Only identified functional
or electrical failures trigger correction; unknowns and evidence gaps alone do not consume
correction rounds. Mapping-only repairs skip regeneration, not review. Unchanged parts with
sufficient evidence can receive a complete corrected configuration directly. Part changes use
the normal selection/reading path; explicit `reread_component_ids` target source rereading.
Instruction-only repairs reuse existing sources unless configuration introduces a new nonpassive
functional part needing source review. An unrelated evidence gap no longer triggers a blanket
source reread. Every accepted repair requires fresh whole-BOM review; it cannot override a
code failure or rewrite a user requirement.

Numerical and source checks are retained. A current failed check in requirements, power,
signals, or support blocks the verdict, including missing selected parts and necessary
functional blocks, not omitted routine passive procurement. Unknown checks and evidence/report
integrity failures do not. They stay inspectable without issue banners and are never converted
into individual passing findings.
Discarded unused facts and ordinary later implementation advice remain guidance.
This is a pre-layout assessment, not a tested PCB, compliance certification, or guarantee.

## Outcomes and purchasing

The report separates three statuses:

- Lifecycle: `running`, `needs_input`, `finished`, `interrupted`, or `error`.
  Normal completion can still contain unresolved issues or exhausted budgets.
- Compatibility: an identified current functional/electrical failure yields `issues_found`
  (Checks failed), even if execution later stops. Otherwise a completed current model review
  with check findings, components, and requirements yields `checked` (Checks passed). Without that
  review, or when interrupted, errored, or awaiting input, the field is `null`. This is
  absence of a verdict, not a third review result. Legacy `incomplete` values read as
  `null`, never as an automatic pass.
- Sourcing: `available`, `partial`, or `unknown`, independently of compatibility.

Findings identify code versus model review, check versus guidance, and the individual
pass/fail/unknown/not-applicable result. Aggregate acceptance considers only current failed
checks in requirements, power, signals, and support. Historical
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

## Frontend reporting contract

The normal report focuses on the functional BOM and purchase links, component
roles, important operating assumptions, schematic-stage notes, and actual functional or
electrical failures. Successful technical review prose, raw numerical records, and
source-binding errors belong in diagnostics, not compatibility-proof summaries. Unknown
or unbound quantities must not be displayed as verified figures; declared operating
assumptions must remain labeled as assumptions.

Keep the complete saved JSON available as a diagnostic export and preserve the existing
parts CSV. Historical support inventories may be shown when present in legacy records;
new runs should not show empty support-inventory sections. The frontend implements this
contract through Map and Parts views, component details, Build notes, and CSV/JSON exports.
Backend evidence, checks, saved records, and exports remain intact.

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

The frontend publishes `/design?run=<id>` when a run starts and updates it for a
refinement. Opening or refreshing that URL uses GET to restore the saved snapshot;
it never automatically resubmits or resumes a run. The active client contract is
[`designRunApi.ts`](../frontend/app/services/api/designRunApi.ts), not the retired chat API.

## Verification

From `backend/`:

```bash
.venv/bin/python -m unittest discover -s tests
```

Tests use short deterministic core/error paths and local model, supplier and document fakes.
The suite includes the Python MCP boundary. Run `npm test` in `mcp-server/`, and
`yarn test`, `yarn typecheck`, and `yarn build` in `frontend/` for the connected code.
Frontend tests use Node's test runner with local fetch fakes and a small saved-run fixture.
No unit test uses live models or networks.

An opt-in live run consumes provider quota; start both backend services first:

```bash
.venv/bin/python evaluations/run_live.py --record data/evaluations/my-run.jsonl
```

The helper sends the original sensor query without component/page guidance, records all SSE
events without overwriting an existing file, and fails unless compatibility is checked.
It also accepts `--query`, `--url`, or a refinement pair `--base-run-id`/`--modification`.
When evaluating engineering accuracy, inspect the actual parts, support assumptions, operating bounds,
current/thermal assumptions and purchase quantities separately from the binary badge.
Keep live audits separate from unit tests; record failures as well as successes in
[results.md](evaluations/results.md).

The [current architecture](../docs/architecture/practical-bom-workflow.md) explains the
decisions. The earlier design-compiler document is historical, not an implementation plan.
