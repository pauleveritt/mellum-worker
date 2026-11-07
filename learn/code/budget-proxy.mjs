/**
 * A loopback proxy in front of llama-server, one per session, that enforces the session budget
 * (F.5; the loopback mode of lc40's scripts/containment/relay.mjs, LC.39).
 *
 * It counts inference requests and the output tokens each response reports. Once either limit
 * is spent, every later inference request gets 429 and the log gains one `budget_exhausted`
 * row, which the harness watches to end the session as `budget`. A successful response whose
 * stream breaks without usage is charged `unknownCharge`, never zero; a failed one (a 400, an
 * unreachable server) is charged nothing, so a host fault never reads as spent budget.
 * Node built-ins only.
 *
 *   node budget-proxy.mjs --target http://127.0.0.1:8001/ --log proxy.jsonl \
 *     --max-requests 64 --max-output 32000 --unknown-charge 16384 [--listen 0]
 */
import http from 'node:http';
import {appendFileSync} from 'node:fs';
import {once} from 'node:events';
import {randomUUID} from 'node:crypto';
import {pathToFileURL} from 'node:url';

const MAX_BODY = 16 * 1024 * 1024;
const KEEP_RESPONSE = 2 * 1024 * 1024;

export const allowedRoute = (method, path) =>
  (method === 'POST' && path === '/v1/chat/completions') ||
  (method === 'GET' && ['/v1/models', '/health'].includes(path));

function safeCode(error) {
  return typeof error?.code === 'string' && /^[A-Z0-9_]{1,64}$/.test(error.code) ? error.code : 'RELAY_ERROR';
}

function loopbackTarget(target) {
  const url = new URL(target);
  if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1' || url.username || url.password || url.search || url.pathname !== '/')
    throw new Error('proxy target must be an explicit loopback HTTP endpoint at its root');
  return url;
}

/** Add the one field the budget needs (usage on a stream); everything the model reads is unchanged. */
export function rewriteRequest(body) {
  const value = JSON.parse(body.toString('utf8'));
  if (value === null || typeof value !== 'object' || Array.isArray(value)) throw new Error('request body must be a JSON object');
  if (value.stream === true) value.stream_options = {...(value.stream_options ?? {}), include_usage: true};
  return Buffer.from(JSON.stringify(value));
}

/** Output tokens a response reports: the last SSE usage chunk, or a JSON body's usage; null if none. */
export function usageFrom(bytes, contentType = '') {
  const read = value => (typeof value?.usage?.completion_tokens === 'number' ? value.usage.completion_tokens : null);
  const text = bytes.toString('utf8');
  if (contentType.includes('text/event-stream')) {
    let found = null;
    for (const line of text.split('\n')) {
      if (!line.startsWith('data:')) continue;
      const data = line.slice(5).trim();
      if (!data || data === '[DONE]') continue;
      try { const tokens = read(JSON.parse(data)); if (tokens !== null) found = tokens; } catch { /* partial frame */ }
    }
    return found;
  }
  try { return read(JSON.parse(text)); } catch { return null; }
}

export async function proxyRelay({listen, target, log = () => {}, budget = null}) {
  const url = loopbackTarget(target);
  const spent = {requests: 0, outputTokens: 0};
  let exhausted = false;
  const record = (boundary, id, fields = {}) => log({boundary, id, timestamp: new Date().toISOString(), ...fields});
  // A 2xx response is charged what it reports, or unknownCharge when its stream broke without
  // usage. A failed response (a 400, the server unreachable) is a host fault: counted as a
  // request, charged no tokens, and logged with its status.
  const charge = (id, outputTokens, status) => {
    const ok = status >= 200 && status < 300;
    const charged = ok ? (outputTokens ?? budget?.unknownCharge ?? 0) : 0;
    spent.outputTokens += charged;
    record('usage', id, {outputTokens, charged, status});
  };
  const server = http.createServer(async (req, res) => {
    if (!allowedRoute(req.method, req.url)) { res.writeHead(403).end(); return; }
    const id = randomUUID(), started = performance.now();
    const inference = req.method === 'POST';
    if (inference && budget && (spent.requests >= budget.requests || spent.outputTokens >= budget.outputTokens)) {
      if (!exhausted) { exhausted = true; record('budget_exhausted', null, {...spent}); }
      for await (const chunk of req) void chunk;
      res.writeHead(429, {'content-type': 'application/json'}).end(JSON.stringify({error: 'session budget exhausted'}));
      return;
    }
    if (inference) spent.requests += 1;
    record('created', id, {method: req.method, path: req.url});
    let body = Buffer.alloc(0);
    try {
      const chunks = []; let size = 0;
      for await (const chunk of req) {
        size += chunk.length;
        if (size > MAX_BODY) throw new Error('proxy request body limit exceeded');
        chunks.push(chunk);
      }
      body = Buffer.concat(chunks);
      if (inference) {
        body = rewriteRequest(body);
        const sent = JSON.parse(body.toString('utf8')).max_tokens;
        record('rewritten', id, {added: ['stream_options.include_usage'], max_tokens: typeof sent === 'number' ? sent : null});
      }
    } catch (error) {
      record('request_error', id, {code: safeCode(error), elapsedMs: performance.now() - started});
      res.writeHead(400).end(); return;
    }
    const upstream = http.request(new URL(req.url, url), {method: req.method,
      headers: {'content-type': 'application/json', accept: 'text/event-stream, application/json',
                ...(inference ? {'content-length': body.length} : {})}}, async up => {
      record('headers', id, {status: up.statusCode, elapsedMs: performance.now() - started});
      const headers = {};
      for (const key of ['content-type', 'content-encoding', 'content-length'])
        if (up.headers[key] !== undefined) headers[key] = up.headers[key];
      res.writeHead(up.statusCode, headers);
      let bytes = 0; const kept = [];
      try {
        for await (const chunk of up) {
          bytes += chunk.length;
          if (inference && bytes <= KEEP_RESPONSE) kept.push(chunk);
          if (!res.write(chunk)) await once(res, 'drain');
        }
        record('complete', id, {bytes, elapsedMs: performance.now() - started});
        if (inference) charge(id, bytes <= KEEP_RESPONSE ? usageFrom(Buffer.concat(kept), up.headers['content-type'] ?? '') : null, up.statusCode);
        res.end();
      } catch (error) {
        record('stream_error', id, {code: safeCode(error), elapsedMs: performance.now() - started});
        if (inference) charge(id, null, up.statusCode);
        res.destroy();
      }
    });
    upstream.setTimeout(600000, () => upstream.destroy(Object.assign(new Error(), {code: 'ETIMEDOUT'})));
    upstream.on('error', error => {
      record('request_error', id, {code: safeCode(error), elapsedMs: performance.now() - started});
      if (inference && !res.headersSent) charge(id, null, 502);
      if (res.headersSent) res.destroy(); else res.writeHead(502).end();
    });
    res.on('close', () => { if (!res.writableFinished) upstream.destroy(); });
    upstream.end(inference ? body : undefined);
  });
  server.listen(listen, '127.0.0.1');
  await once(server, 'listening');
  record('ready', null, {port: server.address().port});
  return {port: server.address().port, server,
          close: () => new Promise(resolve => { server.closeAllConnections?.(); server.close(() => resolve()); })};
}

function flag(argv, name) {
  const at = argv.indexOf(name);
  return at >= 0 ? argv[at + 1] : undefined;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const argv = process.argv.slice(2), file = flag(argv, '--log');
  const log = row => appendFileSync(file, JSON.stringify(row) + '\n');
  const number = name => (flag(argv, name) === undefined ? null : Number(flag(argv, name)));
  const budget = number('--max-requests') === null ? null
    : {requests: number('--max-requests'), outputTokens: number('--max-output'), unknownCharge: number('--unknown-charge')};
  const proxy = await proxyRelay({listen: Number(flag(argv, '--listen') ?? 0), target: flag(argv, '--target'), log, budget});
  for (const signal of ['SIGTERM', 'SIGINT']) process.on(signal, () => proxy.close().then(() => process.exit(0)));
}
