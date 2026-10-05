![Jigsaw Logo](assets/logo_w_text.png)

**From a device description to an evidence-backed, pre-layout bill of materials.**

[Devpost](https://devpost.com/software/jigsaw-make-your-pcb-board-click) • [Pitch Deck](https://www.figma.com/slides/94eWyD99wBcK8kr5nobDi2/Jigsaw?node-id=1-510&t=PplOcCx70slVACQC-1) • [Installation](#installation)

---

Jigsaw is a small side project for common low-voltage embedded devices. Describe what
you want to build; the workflow selects actual DigiKey parts, reads manufacturer
documents, checks component compatibility, and attempts bounded corrections. The result
is a pre-layout BOM of functional components with purchase links, source evidence,
operating assumptions, and support/configuration notes for later schematic work.

Completed reviews report **Checks passed** or **Checks failed**. A pass means the
performed checks identified no explicit functional or electrical compatibility error.
Review covers requested functions, operating ranges, current budgets, logic levels,
available interfaces/resources, and necessary functional blocks such as regulators and
level translators. Routine decoupling, pull-ups, and reset/boot or feedback networks are
not an exhaustive purchasing inventory. Explicitly requested passives and any parts
actually selected are still checked. Unknowns and evidence or reporting gaps remain
inspectable details without blocking the verdict. Without a
completed review or an identified error, a run has no verdict. The workflow does not
design wiring, assign numbered pins, produce a netlist, or require a complete programming-pad plan.

This is a source-assisted assessment, not a complete PCB parts inventory, schematic,
tested board, or guarantee of electrical correctness.
All generated results remain visible and exportable. Current status is a functioning
local/private prototype. The [current cleanup verification](backend/evaluations/results.md#functional-component-cleanup-2026-09-30-prompt-41)
passed local tests and a fresh end-to-end sensor run with four available functional parts,
including matching saved reports and exports. Independent inspection found plausible component
choices but inaccurate or unsupported electrical-report claims, especially for the regulator.
This is working generation, not established general reliability. Earlier results retain their
original support-inventory scope and outcomes in the verification record.

The [October 4 preset evaluation](backend/evaluations/preset-generalization-2026-10-04.md)
ran eight fresh requests on unchanged backend code. Independent source audits found three
plausible component sets, two correctly reported failures, and three passing results with
material errors, including the wireless control. Battery and display presets remain removed;
the remaining wireless example is not a reliability guarantee.

The UI follows the [frontend reporting contract](backend/README.md#frontend-reporting-contract):
useful BOM information, operating assumptions, schematic-stage notes, and actual failures
appear in the normal report. Detailed review prose and numerical records are kept in
diagnostics; unbound quantities are not presented as operating figures.

---

## Installation

You'll need three things running: the MCP server (DigiKey), the backend (Flask + Gemini), and the frontend.

### Prerequisites

- Python 3.11+
- Node.js 22.12+ and Yarn 4 for the frontend (the version is declared in `frontend/package.json`; use Corepack to activate it)
- A [Gemini API key](https://aistudio.google.com/apikey) with access to the configured model
- [DigiKey API credentials](https://developer.digikey.com/) with Product Information API access

Provider access and free-tier quotas depend on your accounts. There is no automatic
paid-model fallback. Start each service below in a separate terminal from the
repository root. Keep this first version local/private: there is no application
authentication or multi-worker job system.

### 1. MCP Server

```bash
cd mcp-server
cp .env.template .env
# Fill in DIGIKEY_CLIENT_ID and DIGIKEY_CLIENT_SECRET in .env
npm install
npm run build
npm start
```

The MCP server runs on `http://localhost:8080`. It obtains a DigiKey token using
client credentials; the design flow does not require a browser OAuth login.

### 2. Backend

```bash
cd backend
cp .env.template .env
# Fill in GEMINI_API_KEY; set LANGCHAIN_TRACING_V2=false unless using LangSmith
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The backend runs on `http://localhost:3001`, with one analysis at a time. See the
[backend guide](backend/README.md) for model settings, budgets, API, saved results,
and failure handling.

### 3. Frontend

```bash
cd frontend
corepack enable
yarn install --immutable
yarn dev
```

Open `http://localhost:5173`.

The frontend uses the local backend by default. Set `VITE_BACKEND_URL` if needed;
the legacy `VITE_USE_MOCK=true` flag disables generation and displays a preview notice.
It does not provide mock data; saved designs remain available. Start with a device
description; purchasing uses the backend defaults of one board,
US sourcing, and USD. The request screen keeps one illustrated wireless-sensor example; the battery logger
and display monitor presets remain removed after independent evaluation. Other device
descriptions can still be entered freely. The workspace has two views:

- **Map:** recorded power and data relationships, with restrained technical illustrations.
  Hover or focus a part to trace its connections; select it for the reason it was chosen,
  its price, supplier link, and datasheet. The diagram keeps a fixed arrangement when
  details open or the screen narrows; scroll the canvas or use its zoom and fit controls.
- **Parts:** illustrated rows with grouped quantities, prices, and purchase links. Narrow screens stack
  each row. Missing selections remain visible, and stock shortages or extra order quantities
  appear only when relevant. Component details keep selection reasoning under “Why this part.”

Build notes beneath the workspace contain operating assumptions, schematic-stage notes,
and actual compatibility failures. Complete backend diagnostics remain available through
Export → Full JSON; the same menu also offers the parts CSV. There are no technical-record
or run-metadata drawers in the normal interface.

The map represents recorded BOM relationships, not physical packages, a PCB layout, or a
wiring plan. Generation shows one plain-language stage from backend events. The review
outcome is separate from sourcing and run lifecycle; unknown prices and unreviewed results
stay visible, and nonblocking unknowns and evidence gaps do not become issue banners.

The page records the current result as `/design?run=<id>`. Refreshing or opening that
URL retrieves the saved snapshot with GET; it does not resubmit the original request
or resume interrupted work. Changes and clarification answers create a new run and update
the URL; browser Back returns to the parent result. Keep the tab open during analysis.
Stop closes the connection and keeps the last received result. Change opens the revision
form and preserves its draft when closed. Failed reviews offer “Try to fix issues”; unfinished
results offer “Try again.” These start explicit new revisions rather than retrying indefinitely.
Operational failures use plain-language messages; provider names, raw exceptions, and
source-selection instructions stay out of the normal interface. Full JSON retains diagnostics.

For a local production-build preview, run `yarn build` then `yarn start`. This serves
the static SPA from `build/client`, not an SSR server or production hosting service.
The preview defaults to `http://127.0.0.1:4173`; set the backend's `FRONTEND_ORIGIN`
to that origin when using it.

## Architecture and API

React consumes a Flask progress stream. One explicit Python workflow owns the
design record, evidence, checks, and bounded repair; LangChain remains the model
integration layer. Focused per-document extraction produces source-checked
observations; a separate operating-configuration proposal references them, and whole-BOM review
still sees the original relevant PDF pages. DigiKey search/details stay in the
existing MCP process. Runs and source documents are stored locally under
`backend/data/` by default.

Refinement instructions reach source-page selection; bounded correction can repair
existing requirement-to-component mappings without rewriting the requirements.
Purchasing prefers available ordinary packaging over custom Digi-Reel service with
an unquoted setup fee. Custom-only offers retain a checkout-fee warning.

- `POST /api/component-analysis` starts a device request.
- `POST /api/refine` starts a revision using a saved run ID and a modification or clarification answers.
- `GET /api/runs/<id>` retrieves the latest saved snapshot.
- `GET /api/runs/<id>/export?format=csv|json` downloads the BOM or full report.
- `GET /health` reports local server status and whether a run is active.

The old `/api/query` and `/api/continue` routes are retired and return HTTP 410.
See [API details](backend/README.md#api) and the
[architecture rationale](docs/architecture/practical-bom-workflow.md). The earlier
design-compiler proposal is historical, not an implementation requirement.

## Verification

From the repository root, after installing dependencies:

```bash
cd backend
.venv/bin/python -m unittest discover -s tests
cd ../mcp-server
npm test
cd ../frontend
yarn test
yarn typecheck
yarn build
```

These checks use local fakes or compile the application; they do not call live
models or suppliers. Live model/PDF capability checks and source-grounded design
evaluation are separate, quota-consuming work described in the backend guide.
Frontend tests cover stream/restoration contracts, recorded system relationships,
report handling of current findings, shared support, and unknown prices; and diagram
geometry that keeps recorded connections clear of component interiors. The
reusable saved-run fixture is `frontend/tests/fixtures/designRun.ts`.

The October 5 UI refinement passed 33 local tests, typecheck, and production build. Browser
verification covered desktop and mobile layouts, saved success/failure/error states, clarification,
one-click repair, rejected-update retry, Stop and reload, parent-history navigation, keyboard
focus, and CSV/JSON downloads. Controlled error/recovery scenarios used a separate local fixture
service; no production snapshots were altered. A fresh request submitted through the live UI
produced run `30d40d3873864ab3a4f23a0138f489bc`: Checks passed, six placements grouped into five
purchasing rows, USD 8.17, 68.64 seconds, and 11 model calls. Downloaded JSON matched the saved
record and CSV contained the same five purchasing rows. This verifies frontend integration;
the backend verdict is not a new independent engineering evaluation. Local screenshots are
in `output/verification/ui-ux-*.jpg`; `output/` is ignored and is not published with the repository.

The final typography and spacing pass uses locally hosted Space Grotesk and IBM Plex
fonts (licenses and sources in `frontend/public/fonts`). The map canvas follows diagram
size within a viewport limit, with tighter surrounding controls and supporting-part rows.
Browser checks at phone, tablet, and desktop widths covered saved sensor and motor designs,
parts, selection, and zoom-out/Fit recovery. All 33 tests, typecheck, and production build
passed. This visual pass used saved results and did not submit a new model run.
Local screenshots are in `output/verification/polish-*.jpg`.

The frontend cleanup preserved behavior across all 57 saved runs: diagram geometry and
1,976 report/illustration renders matched the pre-cleanup implementation exactly. Browser
checks covered generation, revisions, clarification, retry, Stop/reload, history, export links,
and keyboard focus using local fixtures. Desktop map and mobile request/parts layouts also
matched the baseline. Typecheck now rejects unused locals and parameters; the existing
33 tests, immutable install, and production build pass. No backend code or visual assets
changed. The local verification record is `output/verification/frontend-cleanup.json`.

On 2026-09-30, a fresh wireless-sensor request submitted through the UI produced saved run
`6658e55b1a9a4b4892737b0a1fd30f48`: four available functional parts, USD 7.50,
Checks passed, 55.73 seconds, nine model calls, and 71,796 input tokens with no budget stop.
Saved-page reload and downloaded CSV/JSON were verified. This verifies the live UI workflow;
the pass reflects the performed checks, with source and numerical gaps retained as diagnostics.
The diagram revision was also checked in the browser with the saved result and local
synthetic records covering branched supplies, long regulator chains, external power/data,
unfinished selections, long labels, and empty results. Desktop and narrow-screen checks
covered selection visibility, stable zoom, keyboard access, the fit overview, and page
overflow. This visual revision did not submit another model run.
Local verification passes, but the historical [BOM-only reliability gate](backend/evaluations/reliability-plan.md)
failed. Its stricter acceptance criteria, broader support-inventory scope, and earlier accepted
examples remain historical records, not evidence of reliability under the current binary verdict.
The [backend verification guide](backend/README.md#verification) includes fresh-run
and saved-run refinement commands.

---

## Team

**Charles Muehlberger** • **Luke Sanborn** • **Phu Duong**

Built at **HackPrinceton Spring 2025** — Winner, Best Business + Enterprise Hack
