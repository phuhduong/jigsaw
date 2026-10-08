import assert from 'node:assert/strict';
import http from 'node:http';
import test from 'node:test';
import { createHttpServer } from '../dist/http.js';

async function localServer(t) {
  const server = createHttpServer({ clientId: 'fake', clientSecret: 'fake', port: 0 });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise(resolve => {
    server.close(resolve);
    server.closeAllConnections();
  }));
  const port = server.address().port;
  return (path, { method = 'GET', body, headers = {} } = {}) => new Promise((resolve, reject) => {
    const req = http.request({ hostname: '127.0.0.1', port, path, method, headers: {
      Accept: 'application/json, text/event-stream', 'Content-Type': 'application/json', ...headers,
    } }, res => {
      let text = '';
      res.on('data', data => { text += data; });
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, text }));
    });
    req.on('error', reject);
    req.end(body === undefined ? undefined : JSON.stringify(body));
  });
}

const initialize = {
  jsonrpc: '2.0', id: 1, method: 'initialize',
  params: { protocolVersion: '2025-03-26', capabilities: {}, clientInfo: { name: 'local-test', version: '1' } },
};

test('HTTP rejects hostile headers and browser origins, and returns 404 for unknown paths', async t => {
  const request = await localServer(t);
  for (const headers of [{ Host: '[' }, { Host: 'attacker.example' }, { Origin: 'https://attacker.example' }]) {
    const rejected = await request('/mcp', { method: 'POST', body: initialize, headers });
    assert.equal(rejected.status, 403);
    assert.equal(rejected.headers['access-control-allow-origin'], undefined);
  }
  assert.equal((await request('/missing')).status, 404);
  const health = await request('/health');
  assert.equal(health.status, 200);
  assert.equal(JSON.parse(health.text).status, 'healthy');
});

test('MCP initializes, lists tools, reports expired deadlines and terminates sessions', async t => {
  const request = await localServer(t);
  const initialized = await request('/mcp', { method: 'POST', body: initialize });
  assert.equal(initialized.status, 200);
  const headers = { 'mcp-session-id': initialized.headers['mcp-session-id'] };
  assert.ok(headers['mcp-session-id']);
  const post = body => request('/mcp', { method: 'POST', headers, body });
  assert.equal((await post({ jsonrpc: '2.0', method: 'notifications/initialized' })).status, 202);
  const tools = await post({ jsonrpc: '2.0', id: 2, method: 'tools/list' });
  assert.equal(tools.status, 200);
  assert.match(tools.text, /search_components/);
  assert.match(tools.text, /get_product/);
  const expired = await post({ jsonrpc: '2.0', id: 3, method: 'tools/call', params: {
    name: 'get_product', arguments: { mpn: 'FAKE', deadline_ms: 1 },
  } });
  assert.match(expired.text, /"isError":true/);
  assert.match(expired.text, /Supplier operation deadline exceeded/);
  assert.equal((await request('/mcp', { method: 'DELETE', headers })).status, 200);
  assert.equal((await post({ jsonrpc: '2.0', id: 4, method: 'tools/list' })).status, 404);
});

test('rejected initialization frees capacity, concurrent sessions are bounded and deletion releases them', async t => {
  const request = await localServer(t);
  const rejected = await request('/mcp', { method: 'POST', body: { ...initialize, params: {} } });
  assert.equal(rejected.status, 400);
  assert.match(rejected.text, /"error"/);
  assert.equal(rejected.headers['mcp-session-id'], undefined);
  const attempts = await Promise.all(Array.from({ length: 33 }, () =>
    request('/mcp', { method: 'POST', body: initialize })));
  assert.equal(attempts.filter(result => result.status === 200).length, 32);
  assert.equal(attempts.filter(result => result.status === 503).length, 1);
  const headers = { 'mcp-session-id': attempts.find(result => result.status === 200).headers['mcp-session-id'] };
  const existing = await request('/mcp', {
    method: 'POST', headers, body: { jsonrpc: '2.0', id: 2, method: 'tools/list' },
  });
  assert.equal(existing.status, 200);
  assert.equal((await request('/mcp', { method: 'DELETE', headers })).status, 200);
  assert.equal((await request('/mcp', { method: 'POST', body: initialize })).status, 200);
});
