# Project guidance

## Project

Jigsaw is a small, free side project that turns natural-language embedded-device
requirements into a compatibility-checked BOM of functional components with purchase
links and notes for schematic design.

Read [architecture](docs/architecture.md) for product scope and review semantics,
[development](docs/development.md) for API and verification details, and
[README](README.md) for setup. Update these documents when behavior changes rather
than duplicating their contracts here.

Keep documentation focused on the current system. Remove stale prose and comments;
keep task journals, handoff notes, and refactoring histories out of the repository.

## Engineering approach

- Apply YAGNI aggressively. Implement only demonstrated requirements with the smallest
  clear solution. Add complexity only when a concrete failure or requirement justifies it.
- Prefer simple control flow, few dependencies, and deletion of obsolete machinery.
  Avoid speculative abstractions, premature extensibility, and unnecessary defensive code.
- Preserve the documented product scope and acceptance criteria unless the user requests
  a change. Do not expand requirements or weaken checks merely to make a run pass.
- Distinguish implementation defects, external-service failures, and model-output errors
  before changing code or prompts. Fix the demonstrated cause at the narrowest responsible
  layer rather than accumulating special cases.
- Preserve saved designs and export behavior during refactors. Confine compatibility for
  older records to the storage boundary; keep current models free of obsolete fields.
- Keep missing or malformed supplier values and unresolved evidence explicit. Do not
  guess numbers or source references to make a result appear complete.
- Keep UI copy and controls focused on understanding or acting on the BOM. Keep implementation
  diagnostics in exports; avoid promotional copy and redundant explanations.
- Preserve a mature technical aesthetic: geometric typography, restrained color accents,
  precise component diagrams, and deliberate spacing. Aim for clear hierarchy and useful
  density without making the interface feel crowded.

## Tests and verification

- Keep unit tests short and deterministic, covering core and error paths with local fakes.
  Do not add live models, external networks, exhaustive edge cases, timing injections,
  or implementation-detail tests.
- For code changes, run `make check` from the repository root. Report any checks that
  could not run.
- For frontend changes, inspect affected flows in a browser at desktop and narrow widths,
  including keyboard use and diagram clarity. Compare before and after for refactors.
  Use saved runs or local fixtures for routine QA; report live generation separately.
- For live reliability evaluations, define acceptance criteria and an attempt budget
  before running. Use fresh representative requests, inspect BOMs against requirements
  and sources, and report every attempt separately from local test results. If criteria
  are missed, stop for a decision rather than automatically beginning another tuning cycle.
