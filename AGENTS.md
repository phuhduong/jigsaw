# Project guidance

## Project

Jigsaw is a small, free side project whose goal is to turn high-level, natural-language
embedded-device requirements into an evidence-backed, compatibility-checked pre-layout
BOM of functional components with purchase links and source-grounded configuration/support notes.

Scope is functional-component compatibility, not schematic design or a complete PCB parts
inventory. Establish a feasible common operating configuration and check material supply,
current, logic-level, and interface/resource compatibility. Select missing functional blocks
such as regulators, level translators, or drivers. Record ordinary decoupling, pull-ups,
feedback networks, and reset/boot implementation as source-grounded notes for schematic work,
not mandatory procurement or exhaustive value/count proof. Explicitly requested passives and
the suitability of any actually selected part remain in scope. Do not require pin assignments,
a netlist, or a complete programming-pad plan.
Review is binary once completed. Fail only for identified functional or electrical
compatibility errors, including missing selected parts or necessary functional blocks.
Unknowns, coverage gaps, and evidence/reporting defects remain inspectable details, not
blocking verdicts or warning banners. A pass means no explicit error was identified by
the performed checks, not complete proof of compatibility. Without a completed review or
an identified error, a run has no verdict.

Normal frontend reporting should focus on the functional BOM, purchase links, component
roles, important operating assumptions, schematic-stage notes, and actual functional or
electrical failures. Successful review prose, raw numeric records, and source-binding errors
are diagnostics, not proof of compatibility. Do not display unknown or unbound quantities
as verified figures. Retain the complete saved JSON as a diagnostic export and the parts CSV.
Show historical support inventories only when a legacy record contains them, not as empty
sections on new runs.

## Engineering approach

- Apply YAGNI aggressively. Implement only current, demonstrated requirements with the smallest
  clear solution.
- Avoid overengineering, speculative abstractions, premature extensibility, and overly defensive
  code. Prefer simple control flow, few dependencies, and deletion of unnecessary machinery.
- Add complexity only when a concrete failure or requirement justifies it.

## Tests and verification

- Unit tests must be short, deterministic core and error paths using local fakes; do not add live models, external networks, exhaustive edge-cases, timing-injections, or implementation-detail tests.

## Repository map

- [README.md](README.md): current status, setup, and verification commands. The frontend uses
  Node.js 22.12+ and Yarn 4; the MCP service uses npm.
- [backend/README.md](backend/README.md): runtime, configuration, API, and backend module map.
- [Current architecture](docs/architecture/practical-bom-workflow.md): implemented design and
  rationale; earlier proposals and dated evaluations are historical context, not new requirements.
- Frontend entry points: `frontend/app/routes/design.tsx`, `frontend/app/design/index.tsx`, and
  `frontend/app/services/api/designRunApi.ts`. Backend contracts live in `backend/app.py`,
  `backend/models.py`, and `backend/run_store.py`; use saved run IDs, not flattened BOMs.
- Frontend local contract tests: `frontend/tests/designRunApi.test.ts`; reusable saved-run
  fixture: `frontend/tests/fixtures/designRun.ts`. Run with `yarn test` from `frontend/`.
