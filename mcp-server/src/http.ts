import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { randomUUID } from 'node:crypto';
import type { AddressInfo } from 'node:net';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import type { Config } from './config.js';
import { createDigiKeyServer } from './server.js';

const MAX_SESSIONS = 32;
const IDLE_TIMEOUT_MS = 15 * 60 * 1000;

interface Session {
  id: string;
  transport: StreamableHTTPServerTransport;
  activeRequests: number;
  idleTimer?: ReturnType<typeof setTimeout>;
}

export function createHttpServer(config: Config) {
  const sessions = new Map<string, Session>();

  function endSession(session: Session) {
    clearTimeout(session.idleTimer);
    sessions.delete(session.id);
    void session.transport.close().catch(error => console.error('Could not close MCP session:', error));
  }

  async function handleSession(session: Session, req: IncomingMessage, res: ServerResponse) {
    clearTimeout(session.idleTimer);
    session.activeRequests++;
    try {
      await session.transport.handleRequest(req, res);
    } finally {
      session.activeRequests--;
      const id = session.transport.sessionId;
      if (!id) {
        endSession(session);
      } else if (sessions.has(id) && session.activeRequests === 0) {
        session.idleTimer = setTimeout(() => endSession(session), IDLE_TIMEOUT_MS);
        session.idleTimer.unref();
      }
    }
  }

  async function handleRequest(req: IncomingMessage, res: ServerResponse) {
    const port = (httpServer.address() as AddressInfo).port;
    const hosts = ['localhost', '127.0.0.1'];
    const allowedHosts = hosts.map(host => `${host}:${port}`);
    if (port === 80) allowedHosts.push(...hosts);
    if (!allowedHosts.includes(req.headers.host ?? '') || req.headers.origin !== undefined) {
      res.writeHead(403);
      res.end('Only native loopback clients are supported');
      return;
    }

    const path = (req.url ?? '/').split('?')[0];
    if (path === '/health' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'healthy' }));
      return;
    }
    if (path !== '/mcp') {
      res.writeHead(404);
      res.end('Not Found');
      return;
    }

    const sessionId = req.headers['mcp-session-id'];
    if (typeof sessionId === 'string') {
      const session = sessions.get(sessionId);
      if (!session) {
        res.writeHead(404);
        res.end('Session not found');
        return;
      }
      await handleSession(session, req, res);
      return;
    }
    if (req.method !== 'POST') {
      res.writeHead(400);
      res.end('Initialize an MCP session first');
      return;
    }
    if (sessions.size >= MAX_SESSIONS) {
      res.writeHead(503);
      res.end('MCP session limit reached');
      return;
    }

    const server = createDigiKeyServer(config.clientId, config.clientSecret);
    const id = randomUUID();
    const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: () => id });
    const session: Session = { id, transport, activeRequests: 0 };
    // Reserve capacity before awaiting initialization.
    sessions.set(id, session);
    transport.onclose = () => {
      clearTimeout(session.idleTimer);
      sessions.delete(id);
    };
    try {
      await server.connect(transport);
      await handleSession(session, req, res);
    } catch (error) {
      endSession(session);
      throw error;
    }
  }

  const httpServer = createServer((req, res) => {
    void handleRequest(req, res).catch(error => {
      console.error('MCP request failed:', error);
      if (res.headersSent) {
        res.destroy();
      } else {
        res.writeHead(500);
        res.end('Internal server error');
      }
    });
  });
  httpServer.on('close', () => {
    for (const session of sessions.values()) endSession(session);
  });
  return httpServer;
}
