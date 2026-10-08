export interface Config {
  clientId: string;
  clientSecret: string;
  port: number;
}

export interface CliOptions {
  port?: number;
  stdio?: boolean;
  help?: boolean;
}

function parsePort(value: string): number {
  const port = Number(value);
  if (!/^\d+$/.test(value) || !Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error('Port must be an integer from 1 to 65535');
  }
  return port;
}

export function loadConfig(portOverride?: number): Config {
  try {
    process.loadEnvFile();
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
  }
  const clientId = process.env.DIGIKEY_CLIENT_ID;
  const clientSecret = process.env.DIGIKEY_CLIENT_SECRET;

  if (!clientId) {
    throw new Error('DIGIKEY_CLIENT_ID environment variable is required');
  }

  if (!clientSecret) {
    throw new Error('DIGIKEY_CLIENT_SECRET environment variable is required');
  }

  const port = portOverride ?? parsePort(process.env.PORT ?? '8080');
  return { clientId, clientSecret, port };
}

export function parseArgs(args = process.argv.slice(2)): CliOptions {
  const options: CliOptions = {};
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--port':
        if (args[i + 1] === undefined) throw new Error('--port requires a value');
        options.port = parsePort(args[++i]);
        break;
      case '--stdio':
        options.stdio = true;
        break;
      case '--help':
        options.help = true;
        break;
      default:
        throw new Error(`Unknown argument: ${args[i]}`);
    }
  }
  return options;
}

export const HELP = `Usage: node dist/index.js [--port PORT] [--stdio] [--help]

--port PORT overrides PORT (default 8080); use an integer from 1 to 65535.
--stdio uses STDIO instead of loopback HTTP. --help requires no credentials.
Set DIGIKEY_CLIENT_ID and DIGIKEY_CLIENT_SECRET in the environment or .env.
HTTP binds to 127.0.0.1 and accepts native clients without browser Origin headers.
`;
