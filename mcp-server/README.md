# DigiKey MCP Server

MCP tools for DigiKey keyword search and exact product details. The server returns
catalog evidence and purchasing offers; it does not approve electrical compatibility.

## Setup

1. **Install dependencies**:
```bash
npm install
```

2. **Set environment variables** (see `.env.template`):
```bash
DIGIKEY_CLIENT_ID=your_client_id
DIGIKEY_CLIENT_SECRET=your_client_secret
PORT=8080
```

3. **Build & run**:
```bash
npm run build
npm start            # HTTP transport on port 8080
npm run dev:stdio    # STDIO transport (for local MCP client testing)
```

## Tool: search_components

- **Input**: `{ query, limit?: 3, region?: "US", currency?: "USD", deadline_ms? }`
- **Output**: Array of normalized products with exact manufacturer/MPN, package,
  labeled parameters, provider-supplied product/datasheet URLs, offers, and retrieval time.

## Tool: get_product

- **Input**: `{ mpn, region?: "US", currency?: "USD", deadline_ms? }`
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
From the repository root, run `backend/.venv/bin/python mcp-server/tests/test_supplier.py`
for the Python MCP-boundary tests. Neither test suite calls a live provider.

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
