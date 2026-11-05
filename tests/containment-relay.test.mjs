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
