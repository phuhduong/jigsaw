# DigiKey MCP Server

MCP server that provides a `search_components` tool for querying the DigiKey API.

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

- **Input**: `{ query: string, limit?: number }`
- **Output**: Array of components from DigiKey (mpn, manufacturer, description, price, etc.)

## Architecture

```
src/
├── index.ts              # Entry point, HTTP transport startup
├── server.ts             # MCP server instance
├── client.ts             # DigiKey OAuth2 client
├── config.ts             # Environment config
├── tools/digikey.ts      # search_components tool implementation
├── transport/http.ts     # Streamable HTTP transport
├── transport/stdio.ts    # STDIO transport (dev)
└── types.ts              # Shared types
```
