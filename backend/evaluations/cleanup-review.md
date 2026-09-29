# Backend cleanup review

Verified 2026-09-14; subsequently committed as `58876b4`.

Scope: the cleanup following commit `da37c00`, under `AGENTS.md`. This preserves the
BOM-only workflow, Gemini 3.5 Flash-Lite, LangChain model integration, API routes and
existing resource limits. It is not a new architecture or a reliability qualification.

## What changed and why

- Replaced the three thin `agents` modules with ordinary functions in `stages.py`.
  Kept explicit workflow order; no agent runtime or new dependency was introduced.
- Moved instructions to `prompts.py`. Broad prompt shortening was tried, then backed
  out after unsuccessful live trials; final instructions retain the baseline's detailed
  engineering wording. Assembly instructions remain shared with correction. Small
  additions clarify the single requirement map and protected-source repair path.
- Made `Requirement.component_ids` the sole active requirement mapping. The redundant
  inverse field remains loadable for historical snapshots but is no longer generated
  or exported. Historical wiring fields and the obsolete thermal watt scalar likewise
  remain read-compatible, not active model obligations.
- Removed `DesignProposal`, the intermediate evidence/configuration copy. Source
  extraction owns validated observations; configuration updates only reference them.
  This removes the second verification plus diagnostic save/overwrite/restore sequence.
- Centralized review invalidation and recomputation of code findings/outcomes. Split
  the monolithic checker into six named domain functions without changing its findings,
  ordering or arithmetic. Extracted plan application and correction routing from the
  main workflow, and consolidated original-page merging.
- Put model-facing contexts, purchasing rows and response/export snapshots in
  `run_store.py`. Removed the model/projection circular import. Replaced positional
  purchasing tuples and nested status expressions with named values and plain branches.
- Fixed candidate pricing to include supplier order multiples and actual extended cost,
  consistent with the final BOM. Packaging remains visible, including custom-reel caveats.
- Removed app-construction side effects from module import; the factory loads configuration
  before constructing runtime dependencies. Kept request admission, disconnect handling,
  atomic persistence and legacy-route error responses. Removed the redundant post-terminal
  error save that changed the stored timestamp after the terminal SSE snapshot was emitted.
- Kept document safeguards and supplier deadlines, while simplifying repeated text/error
  handling. Fixed MCP stdio startup diagnostics to use stderr instead of corrupting stdout.
- Fixed one demonstrated false quotation rejection: numeric `10uF` and `10µF` are equivalent;
  other values, units, wording and numeric column boundaries remain checked.
- Improved the existing bounded source-page preview to recognize functional-description
  and input/output-capacitor text. A real regulator page previously showed only the tail
  of its application prose, not the explicit support requirement. Original page numbers,
  character/page budgets and model-selected reading remain unchanged; this does not
  interpret the requirement or create a deterministic electrical rule.
- Replaced the existing ambiguous USB forum source lead with a short manufacturer guide
  covering device/sink termination values/counts and default versus advertised current.
  It uses the same document request/extraction path; exact connector ratings still come
  from the selected product. No fixed parts, new source allowance or rule engine was added.
- Removed model transcription of known document IDs in single-source extraction. The
  caller supplies the ID; hidden literal/default validation rejects conflicting observation
  IDs while preserving them in saved evidence. Source-support IDs were already caller-assigned
  and are no longer requested from the model either. Existing quote/page/owner checks remain.
- Put existing quotation/table-classification instructions beside the actual evidence fields,
  removing duplicate prompt wording. Clarified that regulator reading includes capacitor
  selection/stability prose as well as tables and the reference circuit. These are existing
  material support obligations, not new schematic requirements or automatic page reads.
- Kept the existing single schema retry, but supplied concise redacted validation feedback.
  Invalid parsed dictionaries follow the same retry path; raw responses/input values are
  not echoed. Review-area completeness now belongs to the existing code checks rather
  than a duplicate schema validator that discarded usable partial findings. Missing or
  empty review coverage still cannot produce `checked`.
- Excluded direct configuration from the correction response schema while any part is
  unselected. Missing selections must use the existing part-repair path; the runtime
  guard remains. This moves a demonstrated invalid response into the existing bounded
  schema-recovery path without adding retries or correction rounds.
- Consolidated deterministic test records/fakes, removed stage-string dispatch from long
  workflow tests, and moved the Python supplier tests into backend discovery. Added only
  focused pricing/schema-recovery coverage. Applied consistent import ordering, formatting,
  assertion/check/action names, and readable control flow throughout the Python backend.
- Replaced the repetitive backend guide with a code map and current operating contract.
  Marked the unimplemented design-compiler proposal superseded and corrected stale test
  commands and contradictory milestone statements.

## Complexity deliberately retained

The source ledger and support-fulfillment records have different owners: merging them
would let a proposed design erase a source requirement. Numeric records are needed to
check supply/current/logic/thermal compatibility, not to generate wiring. Source URL,
content-hash and original-page protections handle actual untrusted provider content.
Budgets, partial outcomes, saved revisions, admission and disconnect cleanup protect the
existing local request workflow. The capacitor-value guard and TI redirect handling address
observed failures; neither is a generic electronics parser. No extra framework, database,
worker, model provider, retry allowance, manual acceptance fixture or fixed part catalog
was added.

Production Python modules decreased from 12 to 10. Physical line count increased because
dense expressions, schemas and calls were formatted across readable lines; it is not being
presented as a line-count reduction. The reductions are in duplicated state, intermediate
records, responsibilities and misleading module structure.

## Verification

- 69 deterministic backend tests pass, including the relocated supplier-boundary tests.
- Three MCP catalog tests and the TypeScript build pass. A local stdio initialization
  returned JSON-only protocol output with diagnostics isolated on stderr.
- Frontend typecheck and production build pass; build reports only the existing stale
  Browserslist database warning. No frontend dependency update was needed for this task.
- Ruff import/basic checks, 120-column formatter check, and `git diff --check` pass.
- Final read-only comparison across all 43 terminal saved runs produced identical code
  findings, purchasing rows, CSV and recomputed outcomes versus `da37c00`. The accepted `149dc533` baseline
  still recomputes `checked / partial` with 15 placements / 13 MPNs. No snapshots were edited.
- Separate agents reviewed prompt/stage constraints, workflow/state transitions, historical
  loading and pricing, numeric-check parity, source/supplier boundaries, tests, and the
  narrow quote/schema-feedback fixes. Concrete findings were fixed and tested; scope and
  arithmetic checks were not relaxed to make a live run pass.
- Both prompt-23 runs have exact terminal-SSE/saved/GET/JSON equality and matching CSV
  purchasing quantities. Their code findings are identical under baseline `da37c00` and
  the cleanup. This includes the false-positive model review described below: it was not
  introduced by a changed deterministic check.
- The final prompt-27 schema was accepted by the live provider. Its 66-event terminal stream,
  saved snapshot, GET and JSON export agree exactly; source identities persist and HTTP CSV
  is byte-identical to the saved-record export. A separate final implementation review found
  no actionable regression in these contracts or the source/schema changes.

Live verification is recorded separately in [the source audit](cleanup-source-audit.md)
and [results](results.md). Failed trials remain failures even when the chosen parts could
work after a configuration repair. A manually repaired BOM is not an unattended success.

**Fresh acceptance:** prompt 27 (`29c85ccd86234aedb40010b7ce754d16`) completed
`checked / available` in 104.95 seconds using 14 calls and one correction. It used only
the original sensor request, Gemini 3.5 Flash-Lite and the existing budgets, with no
manual parts, pages or repair hints. Independent original-source review accepts its
15 placements / 12 MPNs under the saved operating assumptions; all have offers, totaling
$9.76 at the snapshot. Necessary support parts are separately accounted for. Exact
regulator package, ceramic-capacitor suitability and thermal ratings were verified.
The saved 150mA sustained load and 50°C ambient give approximately 89°C junction,
below its 115°C target. This is conditional pre-layout compatibility, not unrestricted
continuous radio operation or measured PCB cooling.

The source audit explicitly retains nonblocking model-record errors: an incorrect peak
current number, incomplete output-envelope arithmetic, a duplicate misinterpreted reference
resistor, and a reviewer thermal explanation that contradicts its stated target. Correct
source values still leave the actual selected parts compatible under the saved mode; no
part, operating assumption or run snapshot was manually repaired to obtain acceptance.

**Remaining limitation:** the ten preceding cleanup trials did not pass independent
acceptance. One was falsely labeled `checked` despite a capacitor allocated to different
supply domains and unresolved exact-regulator capacitor suitability. That failure also
occurs under the baseline code checks; the cleanup did not introduce or conceal it.
This success does not establish repeatability or make model review authoritative proof.
All failures remain in the linked results and source audit. One earlier quota failure
was followed by a confirmed reset; quota was no longer blocking the 2026-09-14 verification.

The scoped cleanup and its verification are complete. General model reliability remains
unqualified and requires separate measured evaluation, not more cleanup infrastructure.
No stronger model, new framework, increased budget, weakened material check or manual
acceptance fixture was introduced.
