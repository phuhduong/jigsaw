# DigiKey MCP Server

MCP tools for DigiKey keyword search and exact product details. The server returns
catalog evidence and purchasing offers; it does not approve electrical compatibility.

## Setup

1. **Install dependencies**:

```bash
npm install
```

2. **Create local configuration**:

```bash
cp .env.template .env
# Edit .env: set DIGIKEY_CLIENT_ID and DIGIKEY_CLIENT_SECRET.
# PORT defaults to 8080.
```

3. **Build & run**:

```bash
npm run build
npm start            # HTTP transport on port 8080
npm run dev:stdio    # STDIO transport (for local MCP client testing)
```

Run commands from `mcp-server/`. HTTP binds to `localhost` normally; setting
`NODE_ENV=production` binds to all interfaces (`0.0.0.0`). Neither transport adds
application authentication. Keep this service local/private; production binding alone
does not make it safe for public access.

## Tool: search_components

- **Input**: `{ query, limit?, region?, currency?, deadline_ms? }`.
  `limit` is an integer from 1 to 10, default 3; locale defaults are `US` / `USD`.
- **Output**: Array of normalized products with exact manufacturer/MPN, package,
  labeled parameters, provider-supplied product/datasheet URLs, offers, and retrieval time.

## Tool: get_product

- **Input**: `{ mpn, region?, currency?, deadline_ms? }`; locale defaults are `US` / `USD`.
- **Output**: One product in the same format, backed by ProductDetails. Prefer a
  selected DigiKey SKU as `mpn` when a manufacturer part number could be ambiguous.

Each packaging offer retains its SKU, packaging name, stock, MOQ, price breaks,
and returned locale. Missing numbers stay unknown; absent prices produce no priced
breaks. Manufacturer standard pack size is kept separately from order multiple.
URLs come from DigiKey fields and are never constructed from part numbers.

`deadline_ms` is an absolute Unix-millisecond deadline, shared by authentication
and lookup. Without one, the operation has 20 seconds. Errors are MCP `isError`
results; the caller controls any retry. The Python `SupplierClient` also includes
MCP initialization in the same deadline and raises `SupplierError` on failure.

## Verification

`npm test` builds and runs three deterministic catalog tests with local fakes.
From `backend/`, run `.venv/bin/python -m unittest discover -s tests` for the backend
suite, including the Python MCP-boundary tests. Neither suite calls a live provider.

## Architecture

```
src/
├── index.ts              # Entry point, HTTP transport startup
├── server.ts             # MCP server instance
├── client.ts             # DigiKey OAuth2 client
├── config.ts             # Environment config
├── tools/digikey.ts      # search_components and get_product tools
├── transport/http.ts     # Streamable HTTP transport
├── transport/stdio.ts    # STDIO transport (dev)
└── types.ts              # Shared types
```
