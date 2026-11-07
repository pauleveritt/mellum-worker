// The per-session budget proxy (F.5, ported from lc40's relay.mjs loopback mode, LC.39).
import assert from 'node:assert/strict';
import test from 'node:test';
import {createServer} from 'node:http';
import {once} from 'node:events';
import {spawn} from 'node:child_process';
import {mkdtempSync, readFileSync, existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {allowedRoute, rewriteRequest, usageFrom, proxyRelay} from '../learn/code/budget-proxy.mjs';

const PROXY = resolve(dirname(fileURLToPath(import.meta.url)), '../learn/code/budget-proxy.mjs');

async function upstream(handler) {
  const server = createServer(handler);
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  return {server, url: `http://127.0.0.1:${server.address().port}/`};
}

async function post(port, path, body) {
  const response = await fetch(`http://127.0.0.1:${port}${path}`, {method: 'POST',
    headers: {'content-type': 'application/json'}, body: JSON.stringify(body)});
  return {status: response.status, bytes: Buffer.from(await response.arrayBuffer())};
}

const sse = tokens => Buffer.from(`data: {"choices":[{"delta":{"content":"a"}}]}\n\n` +
  `data: {"choices":[],"usage":{"prompt_tokens":5,"completion_tokens":${tokens}}}\n\ndata: [DONE]\n\n`);
const budget = (requests, outputTokens) => ({requests, outputTokens, unknownCharge: 16384});

test('the proxy permits only inference routes, never admin, CONNECT or absolute URLs', () => {
  assert.ok(allowedRoute('POST', '/v1/chat/completions'));
  assert.ok(allowedRoute('GET', '/v1/models'));
  for (const [m, p] of [['CONNECT', 'localhost:8765'], ['POST', '/slots/0?action=save'],
    ['GET', 'http://localhost:8765'], ['POST', '/v1/chat/completions?x=1'], ['GET', '/etc/passwd']])
    assert.equal(allowedRoute(m, p), false);
});

test('rewriteRequest adds only include_usage to a streamed request', () => {
  const body = {messages: [{role: 'user', content: 'hi'}], max_tokens: 16384, stream: true, temperature: 1};
  const out = JSON.parse(rewriteRequest(Buffer.from(JSON.stringify(body))).toString());
  assert.deepEqual(out, {...body, stream_options: {include_usage: true}});
  const plain = {messages: [], stream: false};
  assert.deepEqual(JSON.parse(rewriteRequest(Buffer.from(JSON.stringify(plain))).toString()), plain);
  assert.throws(() => rewriteRequest(Buffer.from('[]')), /object/);
});

test('usageFrom reads the final SSE usage chunk and a JSON body', () => {
  assert.equal(usageFrom(sse(42), 'text/event-stream'), 42);
  assert.equal(usageFrom(Buffer.from('{"usage":{"completion_tokens":7}}'), 'application/json'), 7);
  assert.equal(usageFrom(Buffer.from('data: {"choices":[]}\n\n'), 'text/event-stream'), null);
  assert.equal(usageFrom(Buffer.from('garbage'), 'application/json'), null);
});

test('the proxy forwards the rewritten body and the response bytes unchanged', async () => {
  let received;
  const reply = Buffer.from('data: {"choices":[]}\n\ndata: [DONE]\n\n');
  const {server, url} = await upstream(async (q, s) => {
    let raw = ''; for await (const c of q) raw += c; received = JSON.parse(raw);
    s.writeHead(200, {'content-type': 'text/event-stream'}); s.end(reply);
  });
  const rows = [];
  const proxy = await proxyRelay({listen: 0, target: url, log: row => rows.push(row)});
  try {
    const {status, bytes} = await post(proxy.port, '/v1/chat/completions', {messages: [], stream: true});
    assert.equal(status, 200);
    assert.ok(bytes.equals(reply));
    assert.deepEqual(received.stream_options, {include_usage: true});
    assert.deepEqual(rows.map(r => r.boundary), ['ready', 'created', 'rewritten', 'headers', 'complete', 'usage']);
  } finally { await proxy.close(); server.close(); }
});

test('the proxy refuses other routes without contacting the server, and a non-loopback target', async () => {
  let hits = 0;
  const {server, url} = await upstream((q, s) => { hits++; s.end('x'); });
  const proxy = await proxyRelay({listen: 0, target: url, log: () => {}});
  try {
    assert.equal((await post(proxy.port, '/slots/0?action=save', {})).status, 403);
    assert.equal(hits, 0);
  } finally { await proxy.close(); server.close(); }
  await assert.rejects(proxyRelay({listen: 0, target: 'http://example.com/', log: () => {}}), /loopback/);
});

test('the budget refuses the request after the limit, never the one in flight', async () => {
  let serverHits = 0;
  const {server, url} = await upstream((q, s) => { serverHits++; s.writeHead(200, {'content-type': 'text/event-stream'}); s.end(sse(10)); });
  const rows = [];
  const proxy = await proxyRelay({listen: 0, target: url, log: row => rows.push(row), budget: budget(2, 1000)});
  try {
    assert.equal((await post(proxy.port, '/v1/chat/completions', {stream: true})).status, 200);
    assert.equal((await post(proxy.port, '/v1/chat/completions', {stream: true})).status, 200);
    const refused = await post(proxy.port, '/v1/chat/completions', {stream: true});
    assert.equal(refused.status, 429);
    assert.deepEqual(JSON.parse(refused.bytes.toString()), {error: 'session budget exhausted'});
    await post(proxy.port, '/v1/chat/completions', {stream: true});
    assert.equal(serverHits, 2);
    assert.equal(rows.filter(r => r.boundary === 'budget_exhausted').length, 1);
    assert.deepEqual(rows.filter(r => r.boundary === 'usage').map(r => r.charged), [10, 10]);
  } finally { await proxy.close(); server.close(); }
});

test('the budget counts output tokens across requests', async () => {
  const {server, url} = await upstream((q, s) => { s.writeHead(200, {'content-type': 'text/event-stream'}); s.end(sse(60)); });
  const rows = [];
  const proxy = await proxyRelay({listen: 0, target: url, log: row => rows.push(row), budget: budget(120, 100)});
  try {
    assert.equal((await post(proxy.port, '/v1/chat/completions', {stream: true})).status, 200);
    assert.equal((await post(proxy.port, '/v1/chat/completions', {stream: true})).status, 200);
    assert.equal((await post(proxy.port, '/v1/chat/completions', {stream: true})).status, 429);
    const exhausted = rows.find(r => r.boundary === 'budget_exhausted');
    assert.equal(exhausted.requests, 2); assert.equal(exhausted.outputTokens, 120);
  } finally { await proxy.close(); server.close(); }
});

test('the budget charges unknown usage when the stream resets, never zero', async () => {
  const {server, url} = await upstream((q, s) => {
    s.writeHead(200, {'content-type': 'text/event-stream'});
    s.write('data: {"choices":[]}\n\n'); setTimeout(() => s.socket.destroy(), 10);
  });
  const rows = [];
  const proxy = await proxyRelay({listen: 0, target: url, log: row => rows.push(row), budget: budget(10, 100000)});
  try {
    await post(proxy.port, '/v1/chat/completions', {stream: true}).catch(() => {});
    await new Promise(r => setTimeout(r, 50));
    const usage = rows.filter(r => r.boundary === 'usage');
    assert.equal(usage.length, 1);
    assert.equal(usage[0].outputTokens, null); assert.equal(usage[0].charged, 16384);
  } finally { await proxy.close(); server.close(); }
});

test('the CLI logs a ready row with its port and enforces the flags it is given', async () => {
  const {server, url} = await upstream((q, s) => { s.writeHead(200, {'content-type': 'text/event-stream'}); s.end(sse(5)); });
  const log = join(mkdtempSync(join(tmpdir(), 'budget-proxy-')), 'proxy.jsonl');
  const child = spawn(process.execPath, [PROXY, '--target', url, '--log', log, '--max-requests', '1',
    '--max-output', '1000', '--unknown-charge', '16384', '--listen', '0'], {stdio: 'ignore'});
  try {
    let ready;
    for (let i = 0; i < 100 && !ready; i++) {
      await new Promise(r => setTimeout(r, 50));
      if (existsSync(log)) ready = readFileSync(log, 'utf8').split('\n').filter(Boolean).map(JSON.parse).find(r => r.boundary === 'ready');
    }
    assert.ok(ready?.port > 0);
    assert.equal((await post(ready.port, '/v1/chat/completions', {stream: true})).status, 200);
    assert.equal((await post(ready.port, '/v1/chat/completions', {stream: true})).status, 429);
    assert.ok(readFileSync(log, 'utf8').includes('"boundary":"budget_exhausted"'));
  } finally { child.kill(); server.close(); }
});

test('a finished error response is counted as a request but charged no tokens', async () => {
  // A llama-server 400 (context exceeded) is a host fault, not spent budget (final review).
  const {server, url} = await upstream((q, s) => { s.writeHead(400, {'content-type': 'application/json'}); s.end('{"error":"context"}'); });
  const rows = [];
  const proxy = await proxyRelay({listen: 0, target: url, log: row => rows.push(row), budget: budget(10, 32000)});
  try {
    for (let i = 0; i < 3; i++) assert.equal((await post(proxy.port, '/v1/chat/completions', {stream: true})).status, 400);
    const usage = rows.filter(r => r.boundary === 'usage');
    assert.deepEqual(usage.map(r => [r.charged, r.status]), [[0, 400], [0, 400], [0, 400]]);
    assert.equal(rows.filter(r => r.boundary === 'budget_exhausted').length, 0);
  } finally { await proxy.close(); server.close(); }
});

test('a server that cannot be reached is charged no tokens', async () => {
  const {server, url} = await upstream((q, s) => s.end());
  server.close(); await once(server, 'close');
  const rows = [];
  const proxy = await proxyRelay({listen: 0, target: url, log: row => rows.push(row), budget: budget(10, 32000)});
  try {
    for (let i = 0; i < 3; i++) assert.equal((await post(proxy.port, '/v1/chat/completions', {stream: true})).status, 502);
    assert.deepEqual(rows.filter(r => r.boundary === 'usage').map(r => r.charged), [0, 0, 0]);
  } finally { await proxy.close(); }
});
