![Jigsaw Logo](assets/logo_w_text.png)

**From a device description to an evidence-backed, pre-layout bill of materials.**

[Devpost](https://devpost.com/software/jigsaw-make-your-pcb-board-click) • [Pitch Deck](https://www.figma.com/slides/94eWyD99wBcK8kr5nobDi2/Jigsaw?node-id=1-510&t=PplOcCx70slVACQC-1) • [Installation](#installation)

---

Jigsaw is a small side project for common low-voltage embedded devices. Describe what
you want to build; the workflow selects actual DigiKey parts, reads manufacturer
documents, adds supporting components, checks BOM compatibility, and attempts
bounded corrections. The result includes a BOM with purchase links, source evidence,
assumptions, and unresolved issues.

“Compatibility checked” means the selected parts have an evidence-backed feasible
common operating configuration, including necessary support parts, values and
quantities. Review covers operating ranges, current budgets, logic levels, and
available interfaces/resources. It does not design wiring, assign numbered pins,
produce a netlist, or require a complete programming-pad plan. Only missing or
conflicting evidence material to a BOM claim blocks the result; discarded unused
observations remain visible guidance.

This is a source-assisted assessment—not a schematic, tested PCB, or guarantee of
electrical correctness.
Incomplete results remain visible and exportable. Live end-to-end reliability is
still being evaluated; passing local tests does not establish engineering accuracy.

Current status: **a working local/private baseline, not a qualified PCB-design product**.
The [backend cleanup](backend/evaluations/cleanup-review.md), committed as `58876b4`, passed
local tests, saved-run regression checks and fresh original-query Flash-Lite run `29c85ccd`.
Independent source review accepts its 15 placements / 12 MPNs under the saved operating
assumptions, without manual parts/page guidance or run repairs. All have supplier offers
totaling $9.76 at the 2026-09-14 snapshot; it completed in 105 seconds using 14 model calls.
Saved, streamed and exported results agree. Its explanatory record still contains nonblocking
model errors. Earlier trials include a falsely checked BOM with a material support-part
problem, so repeatability and model-review reliability remain unqualified. The applicable
code checks were not weakened. The [evaluation record](backend/evaluations/results.md)
preserves both successes and failures, including the earlier partial-sourcing baseline `149dc533`.

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
`VITE_USE_MOCK=true` explicitly disables live generation and displays a demo-mode
notice. The active design screen shows saved snapshots, findings, and BOM exports;
it does not generate or display a speculative PCB layout.

The page records the current result as `/design?run=<id>`. Refreshing or opening that
URL retrieves the saved snapshot with GET; it does not resubmit the original request
or resume interrupted work. Refinement creates a new run and updates the URL.

For a local production-build preview, run `yarn build` then `yarn start`. This serves
the static SPA from `build/client`, not an SSR server or production hosting service.
The preview defaults to `http://127.0.0.1:4173`; set the backend's `FRONTEND_ORIGIN`
to that origin when using it.

## Architecture and API

React consumes a Flask progress stream. One explicit Python workflow owns the
design record, evidence, checks, and bounded repair; LangChain remains the model
integration layer. Focused per-document extraction produces source-checked
observations; a separate BOM/support proposal references them, and whole-BOM review
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
Local verification and an independently audited unattended sensor run have passed.
The earlier evaluation plan remains historical, not a gate for this BOM-only workflow.
Successful examples are not proof of reliability across arbitrary requests.
The [backend verification guide](backend/README.md#verification) includes fresh-run
and saved-run refinement commands.

---

## Team

**Charles Muehlberger** • **Luke Sanborn** • **Phu Duong**

Built at **HackPrinceton Spring 2025** — Winner, Best Business + Enterprise Hack
