import assert from 'node:assert/strict';
import test from 'node:test';
import {PassThrough} from 'node:stream';
import {createServer} from 'node:http';
import {once} from 'node:events';
import {readFrames, allowedRoute, hostRelay} from '../scripts/containment/relay.mjs';

test('relay permits only inference routes, never admin, CONNECT or absolute URLs', () => {
  assert.ok(allowedRoute('POST','/v1/chat/completions'));
  assert.ok(allowedRoute('GET','/v1/models'));
  for (const [m,p] of [['CONNECT','localhost:8765'],['POST','/slots/0?action=save'],
    ['GET','http://localhost:8765'],['POST','/v1/chat/completions?x=1'],['GET','/etc/passwd']])
    assert.equal(allowedRoute(m,p), false);
});

test('relay bounds malformed and oversized frames before unbounded buffering', async () => {
  const input = new PassThrough();
  const reading = (async () => { for await (const frame of readFrames(input, 16)) void frame; })();
  input.end('x'.repeat(17));
  await assert.rejects(reading, /frame limit/);
  const bad = new PassThrough();
  const parsing = (async () => { for await (const frame of readFrames(bad)) void frame; })();
  bad.end('bad json\n');
  await assert.rejects(parsing);
});

test('late frames after upstream refusal do not break a subsequent valid request', async () => {
  const server = createServer((q,s) => s.end('stream bytes'));
  server.listen(0,'127.0.0.1'); await once(server,'listening');
  const port=server.address().port;
  await new Promise(resolve=>server.close(resolve));
  const input=new PassThrough(), output=new PassThrough(), frames=[];
  output.on('data', chunk=>frames.push(...chunk.toString().trim().split('\n').map(JSON.parse)));
  const failed=Promise.withResolvers(), complete=Promise.withResolvers();
  const created=[];
  const running=hostRelay(input,output,`http://127.0.0.1:${port}`, row=>{
    if(row.boundary==='created') created.push(row);
    if(row.boundary==='request_error') failed.resolve();
    if(row.boundary==='complete') complete.resolve();
  });
  running.catch(()=>{});
  const send=frame=>input.write(JSON.stringify(frame)+'\n');
  const first='00000000-0000-0000-0000-000000000001', next='00000000-0000-0000-0000-000000000002';
  try {
    send({type:'open',id:first,method:'GET',path:'/health'});
    await failed.promise;
    send({type:'end',id:first}); send({type:'cancel',id:first});
    server.listen(port,'127.0.0.1'); await once(server,'listening');
    send({type:'open',id:next,method:'GET',path:'/health'}); send({type:'end',id:next});
    await Promise.race([complete.promise, running.then(()=>{throw new Error('relay ended early');})]);
    input.end(); await running;
    assert.equal(Buffer.concat(frames.filter(f=>f.id===next&&f.type==='data').map(f=>Buffer.from(f.data,'base64'))).toString(),'stream bytes');
    assert.ok(created.length === 2 && created.every(r=>r.method==='GET' && r.path==='/health'));
  } finally { input.destroy(); output.destroy(); server.closeAllConnections(); server.close(); }
});

// --- Proxy mode (LC.39): a loopback proxy in front of llama-server, no containers. ---
import {rewriteRequest, proxyRelay} from '../scripts/containment/relay.mjs';

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

test('rewriteRequest adds only include_usage to a streamed request', () => {
  const body = {messages: [{role: 'user', content: 'hi'}], max_tokens: 16384, stream: true, temperature: 1};
  const out = JSON.parse(rewriteRequest(Buffer.from(JSON.stringify(body))).toString());
  assert.deepEqual(out, {...body, stream_options: {include_usage: true}});
  const plain = {messages: [], stream: false};
  assert.deepEqual(JSON.parse(rewriteRequest(Buffer.from(JSON.stringify(plain))).toString()), plain);
});

test('rewriteRequest refuses JSON that is not an object', () => {
  assert.throws(() => rewriteRequest(Buffer.from('[]')), /object/);
  assert.throws(() => rewriteRequest(Buffer.from('not json')));
});

test('proxy forwards the rewritten body and response bytes unchanged', async () => {
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
    assert.equal(rows[1].method, 'POST'); assert.equal(rows[1].path, '/v1/chat/completions');
    assert.ok(rows[1].timestamp);
  } finally { await proxy.close(); server.close(); }
});

test('proxy refuses non-inference routes without contacting the server', async () => {
  let hits = 0;
  const {server, url} = await upstream((q, s) => { hits++; s.end('x'); });
  const proxy = await proxyRelay({listen: 0, target: url, log: () => {}});
  try {
    assert.equal((await post(proxy.port, '/slots/0?action=save', {})).status, 403);
    assert.equal(hits, 0);
  } finally { await proxy.close(); server.close(); }
});

test('proxy refuses a non-loopback target', async () => {
  await assert.rejects(proxyRelay({listen: 0, target: 'http://example.com/', log: () => {}}), /loopback/);
});

// --- Proxy session budget (LC.39). ---
import {usageFrom} from '../scripts/containment/relay.mjs';

const sse = tokens => Buffer.from(`data: {"choices":[{"delta":{"content":"a"}}]}\n\n` +
  `data: {"choices":[],"usage":{"prompt_tokens":5,"completion_tokens":${tokens}}}\n\ndata: [DONE]\n\n`);
const budget = (requests, outputTokens) => ({requests, outputTokens, unknownCharge: 16384});

test('usageFrom reads the final SSE usage chunk and a JSON body', () => {
  assert.equal(usageFrom(sse(42), 'text/event-stream'), 42);
  assert.equal(usageFrom(Buffer.from('{"usage":{"completion_tokens":7}}'), 'application/json'), 7);
  assert.equal(usageFrom(Buffer.from('data: {"choices":[]}\n\n'), 'text/event-stream'), null);
  assert.equal(usageFrom(Buffer.from('garbage'), 'application/json'), null);
});

test('budget refuses the request after the limit, never the one in flight', async () => {
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
    assert.equal(rows.filter(r => r.boundary === 'created').length, 2);
    assert.deepEqual(rows.filter(r => r.boundary === 'usage').map(r => r.charged), [10, 10]);
  } finally { await proxy.close(); server.close(); }
});

test('budget charges unknown usage when the stream resets', async () => {
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

test('budget counts output across requests', async () => {
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
