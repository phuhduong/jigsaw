import { once } from 'node:events';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { HELP, loadConfig, parseArgs } from './config.js';
import { createDigiKeyServer } from './server.js';
import { createHttpServer } from './http.js';

async function main() {
  const options = parseArgs();
  if (options.help) {
    console.log(HELP);
    return;
  }
  const config = loadConfig(options.port);
  if (options.stdio) {
    await createDigiKeyServer(config.clientId, config.clientSecret).connect(new StdioServerTransport());
  } else {
    const server = createHttpServer(config);
    server.listen(config.port, '127.0.0.1');
    await once(server, 'listening');
    console.log(`DigiKey MCP server listening on http://127.0.0.1:${config.port}/mcp`);
    const shutdown = () => {
      server.close();
      server.closeAllConnections();
    };
    process.once('SIGINT', shutdown);
    process.once('SIGTERM', shutdown);
  }
}

main().catch(error => {
  console.error(error instanceof Error ? error.message : 'Could not start DigiKey MCP server');
  process.exitCode = 1;
});
