import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { parseArgs } from '../dist/config.js';

test('help works without credentials or an environment file', () => {
  const entry = fileURLToPath(new URL('../dist/index.js', import.meta.url));
  const result = spawnSync(process.execPath, [entry, '--help'], { cwd: tmpdir(), env: {}, encoding: 'utf8' });
  assert.equal(result.status, 0);
  assert.match(result.stdout, /Usage: node dist\/index.js/);
  assert.equal(result.stderr, '');
});

test('CLI accepts explicit options and rejects invalid ports and unknown arguments', () => {
  assert.deepEqual(parseArgs(['--port', '9000', '--stdio']), { port: 9000, stdio: true });
  assert.deepEqual(parseArgs([]), {});
  for (const port of ['junk', '8080junk', '0', '65536']) {
    assert.throws(() => parseArgs(['--port', port]), /Port must be an integer/);
  }
  assert.throws(() => parseArgs(['--port']), /requires a value/);
  assert.throws(() => parseArgs(['--unknown']), /Unknown argument/);
});
