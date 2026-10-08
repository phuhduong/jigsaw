# Development

Follow the [local setup instructions](../README.md#run-locally) to install dependencies
and start the services.

## Checks

Run `make check` from the repository root for tests, type checking, and production builds.
Individual targets are `check-backend`, `check-mcp`, and `check-frontend`. Tests use local
fixtures and fakes. To exercise model and supplier integration, use the running application.

The backend suite uses Python's `unittest`. The frontend uses Node's test runner, TypeScript,
and the React Router production build. The MCP suite compiles TypeScript and tests catalog
normalization, CLI behavior, and loopback HTTP sessions.

## Configuration

Copy the `.env.template` beside each service to its local `.env` file. Process environment
values take precedence. The backend loads its adjacent `.env`; the MCP CLI loads `.env` from
its working directory. Frontend settings are resolved by Vite at startup/build time.

| Setting | Purpose |
|---|---|
| `GEMINI_API_KEY` | Backend model credential |
| `MODEL`, `MODEL_PROVIDER`, `MODEL_THINKING_LEVEL` | Model, provider, and optional reasoning level |
| `MODEL_PDF_INPUT` | Whether the configured model accepts original PDF pages |
| `MODEL_RPM`, `MODEL_TPM`, `MODEL_CONTEXT_TOKENS` | Local request, token, and context limits |
| `DATA_DIR` | Backend runtime directory, containing `runs/` and `documents/` |
| `MCP_SERVER_URL` | Backend's DigiKey service address |
| `FRONTEND_ORIGIN` | Browser origin permitted by the backend |
| `DIGIKEY_CLIENT_ID`, `DIGIKEY_CLIENT_SECRET` | DigiKey service credentials |
| `PORT` | Backend port (default 3001) or DigiKey service port (default 8080) |
| `VITE_BACKEND_URL` | Frontend's backend address |
| `VITE_DISABLE_GENERATION` | Disable generation while allowing saved-design retrieval |

Set model rate limits to the provider account's allowance. The workflow uses structured
model output and original PDF pages.
Credentials, runtime data, and build output are kept outside version control.

The default runtime directory is `$XDG_DATA_HOME/jigsaw`, or `~/.local/share/jigsaw` when
`XDG_DATA_HOME` is unset. `DATA_DIR` overrides it and accepts `~`. Back up this directory to
preserve saved URLs and source documents. Starting the backend marks unfinished runs interrupted.

For a built frontend preview, run `yarn build` then `yarn start` from `frontend/`. Set
`FRONTEND_ORIGIN=http://127.0.0.1:4173` in the backend environment for that preview.

## Backend API

Start with `POST /api/component-analysis`:

```json
{
  "query": "A USB-C-powered temperature and humidity sensor with Wi-Fi and Bluetooth",
  "options": {"board_quantity": 1, "region": "US", "currency": "USD"}
}
```

`options` is optional. Refine with `POST /api/refine`, sending a saved ID and either a change
or all pending clarification answers:

```json
{"base_run_id": "<id>", "modification": "Add another sensor"}
```

```json
{"base_run_id": "<id>", "answers": {"<question-id>": "Indoor use"}}
```

Both POST endpoints return server-sent events (SSE). Each event's `data` is JSON with `type`,
`run_id`, and an increasing `sequence`. A stream begins with `started`, sends `progress` and
`snapshot` updates, and ends with `complete` or `error`. Snapshots contain the saved record
plus derived `bom`.

`complete` marks the end of the request; the snapshot's `compatibility` is `checked`,
`issues_found`, or `null`. A request for clarification ends with `complete` and a lifecycle of
`needs_input`. If the stream ends before a terminal event, retrieve the saved run to check
its state. Streams cannot be replayed or resumed.

| Endpoint | Result |
|---|---|
| `GET /api/runs/<id>` | Latest saved snapshot and BOM |
| `GET /api/runs/<id>/export?format=csv` | Grouped purchasing rows |
| `GET /api/runs/<id>/export?format=json` | Complete record and diagnostics |
| `GET /health` | Server health and whether a run is active |

Request validation errors return 400, missing runs return 404, and concurrent starts or a
running refinement base return 409. Request bodies larger than 64 KiB return 413. Once
streaming starts, failures arrive as terminal events when possible.

Per-run limits are defined in [`Limits`](../backend/models.py). Supplier and document calls
normally have at most 20 seconds, model calls 45 seconds, and the browser stream 10 minutes.
In-flight calls, DNS, and PDF parsing can overrun nominal deadlines. Refinements inherit saved
purchasing options and limits. Retrieval and export return saved results without refreshing
prices or repeating review.

## DigiKey service

After building, `npm start` serves Streamable HTTP at `/mcp`, with `GET /health` for status.
For STDIO, run `node dist/index.js --stdio` directly so stdout contains only MCP protocol
messages. `--port` overrides `PORT`, and `--help` works without credentials.

HTTP accepts native loopback clients with a matching Host header and rejects any Origin header.
At most 32 sessions can exist; idle sessions expire after 15 minutes without an active request.
Clients release sessions with `DELETE /mcp` and their `mcp-session-id`. Expired sessions return
404 and require initialization again.

`search_components` accepts `{query, limit?, region?, currency?, deadline_ms?}`. The limit is
1–10, default 3. `get_product` accepts `{mpn, region?, currency?, deadline_ms?}`. Prefer a
DigiKey SKU from search results; manufacturer part numbers must resolve to a single product.
Locale defaults are US/USD. Both return exact catalog identity,
labeled parameters, offers, source URLs, and retrieval time. Missing numbers stay unknown.

`deadline_ms` is an absolute Unix-millisecond deadline shared by OAuth and catalog lookup.
Without one, the operation has 20 seconds. Tool errors are MCP `isError` results; the caller
controls retries. The Python client also includes MCP initialization in its operation deadline.
