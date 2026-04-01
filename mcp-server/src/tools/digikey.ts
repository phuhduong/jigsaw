/**
 * DigiKey tool definitions and handlers
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { DigiKeyClient } from '../client.js';

/**
 * Create and register DigiKey tools
 */
export function registerDigiKeyTools(server: McpServer, digikeyClient: DigiKeyClient): void {
  console.log('Registering DigiKey MCP tools...');

  // @ts-expect-error — MCP SDK Zod type recursion exceeds TS depth limit
  server.tool(
    'search_components',
    'Search for electronic components using the DigiKey API. Returns a list of compatible components with specifications, pricing, and datasheets.',
    {
      query: z.string().describe(
        'Search query describing the component needed (e.g., "ESP32 microcontroller with WiFi", "3.3V LDO regulator 600mA")'
      ),
      limit: z.number().optional().default(5).describe('Maximum number of results to return (default: 5)'),
    },
    async ({ query, limit = 5 }) => {
      // Use the query as-is — the caller (Agent 1) crafts descriptive search queries.
      // Prepending raw category strings like "mcu" degrades DigiKey keyword results.
      const components = await digikeyClient.searchComponents(query, limit);
      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(components, null, 2),
          },
        ],
      };
    }
  );

  console.log('Tools registered: search_components');
}
