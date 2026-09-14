/**
 * Server instance creation
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { DigiKeyClient } from './client.js';
import { registerDigiKeyTools } from './tools/index.js';

export class DigiKeyServer {
  private server: McpServer;
  private digikeyClient: DigiKeyClient;

  constructor(clientId: string, clientSecret: string) {
    this.digikeyClient = new DigiKeyClient(clientId, clientSecret);
    this.server = new McpServer(
      {
        name: 'digikey-mcp',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Register tools
    registerDigiKeyTools(this.server, this.digikeyClient);
    console.error('DigiKey MCP Server initialized with tools registered');
  }

  getServer(): McpServer {
    return this.server;
  }
}
