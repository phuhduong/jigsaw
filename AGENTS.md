# Project guidence

## Project

Jigsaw is a small, free side project whose goal is to turn high-level, natural-language
embedded-device requirements into an evidence-backed, compatibility-checked pre-layout
bill of materials (BOM), including required supporting components and purchase links.

Scope is BOM compatibility, not schematic or wiring design. Establish an evidence-backed
feasible common operating configuration, necessary support parts with values and quantities,
and material operating-range, current, logic-level, and interface/resource compatibility.
Do not require numbered pin assignments, a netlist, or a complete programming-pad plan.
Only evidence needed for a material BOM claim blocks the result; discarded unused facts
remain visible guidance, not new proof obligations.

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
