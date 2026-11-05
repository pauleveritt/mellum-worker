/** Restricted inference over docker-exec pipes. No host port or filesystem grant. */
import http from 'node:http';
import {spawn} from 'node:child_process';
import {appendFileSync} from 'node:fs';
import {once} from 'node:events';
import {randomUUID} from 'node:crypto';
import {pathToFileURL} from 'node:url';

const MAX_BODY = 16 * 1024 * 1024, MAX_ACTIVE = 4, MAX_QUEUE = 8 * 1024 * 1024;
export const allowedRoute = (method, path) =>
  (method === 'POST' && path === '/v1/chat/completions') ||
  (method === 'GET' && ['/v1/models', '/health'].includes(path));

export async function* readFrames(input, limit = 2 * 1024 * 1024) {
  let buffer = '';
  for await (const chunk of input) {
    buffer += chunk.toString('utf8');
    let at;
    while ((at = buffer.indexOf('\n')) >= 0) {
      if (at > limit) throw new Error('frame limit exceeded');
      yield JSON.parse(buffer.slice(0, at));
      buffer = buffer.slice(at + 1);
    }
    if (buffer.length > limit) throw new Error('frame limit exceeded');
  }
  if (buffer) throw new Error('truncated relay frame');
}

function writer(output) {
  let tail = Promise.resolve(), queued = 0;
  return frame => {
    const bytes = JSON.stringify(frame) + '\n';
    queued += Buffer.byteLength(bytes);
    if (queued > MAX_QUEUE) throw new Error('relay queue limit exceeded');
    const written = tail.then(async () => {
      if (!output.write(bytes)) await once(output, 'drain');
      queued -= Buffer.byteLength(bytes);
    });
    tail = written;
    return written;
  };
}

function body(frame) {
  if (typeof frame.data !== 'string' || frame.data.length > 90000 ||
      !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(frame.data))
    throw new Error('invalid relay chunk');
  return Buffer.from(frame.data, 'base64');
}

function safeCode(error) {
  return /^(?:E[A-Z0-9_]+|ERR_[A-Z0-9_]+)$/.test(error?.code ?? '') ? error.code : 'RELAY_FAILURE';
}

export async function hostRelay(input, output, target, log = () => {}) {
  const url = new URL(target);
  if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1' || url.username || url.password || url.search || url.pathname !== '/')
    throw new Error('relay target must be an explicit loopback HTTP endpoint');
  const send = writer(output), active = new Map(), used = new Map();
  function record(boundary, id, fields = {}) {
    log({boundary, id, timestamp:new Date().toISOString(), ...fields});
  }
  try {
    for await (const frame of readFrames(input)) {
      if (frame.type === 'ready') { record('ready', null); continue; }
      if (typeof frame.id !== 'string' || !/^[a-f0-9-]{36}$/.test(frame.id)) throw new Error('invalid relay ID');
      if (frame.type === 'open') {
        if (used.has(frame.id) || active.size >= MAX_ACTIVE || used.size > 4096 || !allowedRoute(frame.method, frame.path))
          throw new Error('relay route, identity or concurrency violation');
        used.set(frame.id, {bytes:0});
        const id = frame.id, started = performance.now();
        const req = http.request(new URL(frame.path, url), {method:frame.method,
          headers:{'content-type':'application/json', accept:'text/event-stream, application/json'}}, async res => {
          record('headers', id, {status:res.statusCode, elapsedMs:performance.now()-started});
          const headers = {'x-mellum-transport-id':id};
          for (const key of ['content-type', 'content-encoding', 'content-length'])
            if (res.headers[key] !== undefined) headers[key] = res.headers[key];
          try {
            await send({type:'headers',id,status:res.statusCode,headers});
            let bytes = 0;
            for await (const chunk of res) {
              bytes += chunk.length;
              for (let offset=0; offset<chunk.length; offset+=65536)
                await send({type:'data',id,data:chunk.subarray(offset,offset+65536).toString('base64')});
            }
            record('complete', id, {bytes, elapsedMs:performance.now()-started});
            await send({type:'end',id});
          } catch (error) {
            record('stream_error', id, {code:safeCode(error), elapsedMs:performance.now()-started});
            await send({type:'failure',id,code:safeCode(error)}).catch(() => {});
          } finally { clearTimeout(active.get(id)?.timer); active.delete(id); }
        });
        const timer = setTimeout(() => req.destroy(Object.assign(new Error(), {code:'ETIMEDOUT'})), 600000);
        active.set(id, {req, timer, bytes:0});
        req.on('error', error => {
          record('request_error', id, {code:safeCode(error), elapsedMs:performance.now()-started});
          send({type:'failure',id,code:safeCode(error)}).catch(() => {});
          clearTimeout(timer); active.delete(id);
        });
        record('created', id, {method:frame.method, path:frame.path});
      } else {
        const entry = active.get(frame.id);
        const tombstone = used.get(frame.id);
        if (!tombstone) throw new Error('unknown relay request');
        if (frame.type === 'data') {
          const chunk = body(frame);
          tombstone.bytes += chunk.length;
          if (tombstone.bytes > MAX_BODY) throw new Error('relay request body limit exceeded');
          if (entry && !entry.req.write(chunk)) await once(entry.req, 'drain');
        } else if (frame.type === 'end') entry?.req.end();
        else if (frame.type === 'cancel') { if (entry) { entry.req.destroy(); clearTimeout(entry.timer); active.delete(frame.id); } }
        else throw new Error('invalid relay frame type');
      }
    }
  } finally {
    for (const {req,timer} of active.values()) { clearTimeout(timer); req.destroy(); }
  }
}

function loopbackTarget(target) {
  const url = new URL(target);
  if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1' || url.username || url.password || url.search || url.pathname !== '/')
    throw new Error('relay target must be an explicit loopback HTTP endpoint');
  return url;
}

/** Add the one routing field the proxy needs; everything the model reads is unchanged. */
export function rewriteRequest(body) {
  const value = JSON.parse(body.toString('utf8'));
  if (value === null || typeof value !== 'object' || Array.isArray(value)) throw new Error('request body must be a JSON object');
  if (value.stream === true) value.stream_options = {...(value.stream_options ?? {}), include_usage: true};
  return Buffer.from(JSON.stringify(value));
}

/** Native sessions (LC.39): a loopback HTTP proxy in front of llama-server, one per session. */
export async function proxyRelay({listen, target, log = () => {}}) {
  const url = loopbackTarget(target);
  const record = (boundary, id, fields = {}) => log({boundary, id, timestamp:new Date().toISOString(), ...fields});
  const server = http.createServer(async (req, res) => {
    if (!allowedRoute(req.method, req.url)) { res.writeHead(403).end(); return; }
    const id = randomUUID(), started = performance.now();
    record('created', id, {method:req.method, path:req.url});
    let body = Buffer.alloc(0);
    try {
      const chunks = []; let size = 0;
      for await (const chunk of req) {
        size += chunk.length;
        if (size > MAX_BODY) throw new Error('relay request body limit exceeded');
        chunks.push(chunk);
      }
      body = Buffer.concat(chunks);
      if (req.method === 'POST') { body = rewriteRequest(body); record('rewritten', id, {added:['stream_options.include_usage']}); }
    } catch (error) {
      record('request_error', id, {code:safeCode(error), elapsedMs:performance.now()-started});
      res.writeHead(400).end(); return;
    }
    const upstream = http.request(new URL(req.url, url), {method:req.method,
      headers:{'content-type':'application/json', accept:'text/event-stream, application/json',
               ...(req.method === 'POST' ? {'content-length':body.length} : {})}}, async up => {
      record('headers', id, {status:up.statusCode, elapsedMs:performance.now()-started});
      const headers = {'x-mellum-transport-id':id};
      for (const key of ['content-type', 'content-encoding', 'content-length'])
        if (up.headers[key] !== undefined) headers[key] = up.headers[key];
      res.writeHead(up.statusCode, headers);
      let bytes = 0;
      try {
        for await (const chunk of up) { bytes += chunk.length; if (!res.write(chunk)) await once(res, 'drain'); }
        record('complete', id, {bytes, elapsedMs:performance.now()-started});
        res.end();
      } catch (error) {
        record('stream_error', id, {code:safeCode(error), elapsedMs:performance.now()-started});
        res.destroy();
      }
    });
    upstream.setTimeout(600000, () => upstream.destroy(Object.assign(new Error(), {code:'ETIMEDOUT'})));
    upstream.on('error', error => {
      record('request_error', id, {code:safeCode(error), elapsedMs:performance.now()-started});
      if (res.headersSent) res.destroy(); else res.writeHead(502, {'x-mellum-transport-id':id}).end();
    });
    res.on('close', () => { if (!res.writableFinished) upstream.destroy(); });
    upstream.end(req.method === 'POST' ? body : undefined);
  });
  server.listen(listen, '127.0.0.1');
  await once(server, 'listening');
  record('ready', null, {port:server.address().port});
  return {port:server.address().port, server,
          close:() => new Promise(resolve => { server.closeAllConnections?.(); server.close(() => resolve()); })};
}

function flag(argv, name, fallback) {
  const at = argv.indexOf(name);
  return at >= 0 ? argv[at + 1] : fallback;
}

async function containerRelay() {
  const send = writer(process.stdout), active = new Map();
  const server = http.createServer(async (req,res) => {
    if (!allowedRoute(req.method, req.url) || active.size >= MAX_ACTIVE) { res.writeHead(403).end(); return; }
    const id = randomUUID();
    active.set(id,res);
    res.on('close', () => { if (active.delete(id)) send({type:'cancel',id}).catch(() => {}); });
    try {
      await send({type:'open',id,method:req.method,path:req.url});
      let bytes = 0;
      for await (const chunk of req) {
        bytes += chunk.length;
        if (bytes > MAX_BODY) throw new Error('body limit');
        for (let offset=0; offset<chunk.length; offset+=65536)
          await send({type:'data',id,data:chunk.subarray(offset,offset+65536).toString('base64')});
      }
      await send({type:'end',id});
    } catch { send({type:'cancel',id}).catch(() => {}); res.destroy(); }
  });
  server.listen(8002,'127.0.0.1');
  await once(server,'listening');
  await send({type:'ready'});
  try {
    for await (const frame of readFrames(process.stdin)) {
      const res = active.get(frame.id);
      if (!res) continue; // Cancellation can race with a response already in flight.
      if (frame.type === 'headers') res.writeHead(frame.status, frame.headers);
      else if (frame.type === 'data') { if (!res.write(body(frame))) await once(res,'drain'); }
      else if (frame.type === 'end') { active.delete(frame.id); res.end(); }
      else if (frame.type === 'failure') {
        active.delete(frame.id);
        if (res.headersSent) res.destroy();
        else res.writeHead(502, {'x-mellum-transport-id':frame.id}).end();
      } else throw new Error('invalid host frame');
    }
  } finally { for (const res of active.values()) res.destroy(); server.close(); }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (process.argv[2] === 'container') await containerRelay();
  else if (process.argv[2] === 'proxy') {
    const argv = process.argv.slice(3), file = flag(argv, '--log');
    const log = row => appendFileSync(file, JSON.stringify(row)+'\n');
    const proxy = await proxyRelay({listen:Number(flag(argv, '--listen', '0')), target:flag(argv, '--target'), log});
    for (const signal of ['SIGTERM','SIGINT']) process.on(signal, () => proxy.close().then(() => process.exit(0)));
  } else {
    const [cid,target,file] = process.argv.slice(3);
    const child = spawn('docker',['exec','-i','--user','1000:1000',cid,'node','/opt/relay.mjs','container'],
      {stdio:['pipe','pipe','inherit']});
    const log = row => appendFileSync(file, JSON.stringify(row)+'\n');
    for (const signal of ['SIGTERM','SIGINT']) process.on(signal, () => child.stdout.destroy());
    try { await hostRelay(child.stdout, child.stdin, target, log); }
    catch (error) { log({boundary:'relay_error',code:safeCode(error)}); process.exitCode = 1; }
    finally { child.stdin.destroy(); child.kill(); }
  }
}
