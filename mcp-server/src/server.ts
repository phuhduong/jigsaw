import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { DigiKeyClient, SupplierError } from './client.js';

const lookupFields = {
  region: z.string().regex(/^[A-Z]{2}$/).default('US'),
  currency: z.string().regex(/^[A-Z]{3}$/).default('USD'),
  deadline_ms: z.number().finite().positive().optional().describe('Absolute Unix-millisecond operation deadline'),
};

async function resultOf(operation: () => Promise<unknown>) {
  try {
    return { content: [{ type: 'text' as const, text: JSON.stringify(await operation()) }] };
  } catch (error) {
    const known = error instanceof SupplierError;
    return {
      isError: true,
      content: [{ type: 'text' as const, text: JSON.stringify({ error: {
        message: known ? error.message : 'Supplier lookup failed',
        status_code: known ? error.statusCode ?? null : null,
        retry_after: known ? error.retryAfter ?? null : null,
      } }) }],
    };
  }
}

export function createDigiKeyServer(clientId: string, clientSecret: string): McpServer {
  const server = new McpServer({ name: 'digikey-mcp', version: '0.1.0' });
  const client = new DigiKeyClient(clientId, clientSecret);
  server.registerTool('search_components', {
    description: 'Search DigiKey products and packaging offers.',
    inputSchema: {
      query: z.string().min(1).max(500),
      limit: z.number().int().min(1).max(10).default(3),
      ...lookupFields,
    },
  }, async ({ query, limit, region, currency, deadline_ms }) => resultOf(() => client.searchComponents(
    query, limit, { region, currency, deadlineMs: deadline_ms },
  )));
  server.registerTool('get_product', {
    description: 'Get product details using a DigiKey SKU or an unambiguous manufacturer MPN.',
    inputSchema: {
      mpn: z.string().min(1).max(200),
      ...lookupFields,
    },
  }, async ({ mpn, region, currency, deadline_ms }) => resultOf(() => client.getProduct(
    mpn, { region, currency, deadlineMs: deadline_ms },
  )));
  return server;
}
