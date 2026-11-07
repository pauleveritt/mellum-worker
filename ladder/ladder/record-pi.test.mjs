import assert from 'node:assert/strict';
import test from 'node:test';
import * as recorder from '../../extensions/mellum-recorder.ts';

function capture(options = {}) {
  assert.equal(typeof recorder.installRecorder, 'function', 'observational recorder is missing');
  const handlers = {}, rows = [], diagnostics = [];
  recorder.installRecorder({on: (name, fn) => { handlers[name] = fn; }}, {
    write: row => rows.push(structuredClone(row)), diagnose: text => diagnostics.push(text),
    runId: 'run', pid: 10, runtime: {piVersion:'1.1.0', entryPath:'/runtime/pi', execPath:'/node', cwd:'/fixture'},
    ...options,
  });
  return {handlers, rows, diagnostics};
}
const request = {payload:{model:'mellum', messages:[{role:'user', content:'fix it'}]}};
const assistant = {message:{role:'assistant', content:[{type:'toolCall', id:'call', name:'bash', arguments:{command:'pytest'}}]}};

test('metadata and request association preserve original payload and chunk', () => {
  const {handlers:h, rows} = capture();
  const payload = structuredClone(request), before = structuredClone(payload);
  assert.equal(h.before_provider_request(payload), undefined);
  const chunk = {provider:'omlx', api:'openai-completions', model:'mellum', data:{choices:[{delta:{content:'yes'}}]}};
  assert.equal(h.provider_stream_event(chunk), undefined);
  h.message_end(assistant);
  h.tool_call({toolCallId:'call', toolName:'bash', input:{command:'pytest'}});
  assert.deepEqual(payload, before);
  assert.equal(rows[0].type, 'instance_start');
  assert.deepEqual(rows.map(r => r.seq), [1,2,3,4,5]);
  assert.equal(rows[1].request, 1);
  assert.equal(rows[2].requestId, rows[1].requestId);
  assert.equal(rows[4].requestId, rows[1].requestId);
  assert.deepEqual(rows[2].data, chunk.data);
  for(const row of rows) { assert.equal(row.traceSchema, 1); assert.equal(row.runId,'run'); assert.ok(row.instanceId); assert.ok(Number.isFinite(row.elapsedMs)); assert.ok(!Number.isNaN(Date.parse(row.timestamp))); }
});

test('two instances sharing a PID have distinct identities', () => {
  const a=capture(), b=capture();
  assert.notEqual(a.rows[0].instanceId, b.rows[0].instanceId);
  assert.equal(a.rows[0].pid,b.rows[0].pid);
});

test('unassociated chunks after completion or settlement remain unknown', () => {
  const {handlers:h, rows} = capture();
  h.provider_stream_event({data:{orphan:true}});
  h.before_provider_request(request); h.message_end({message:{role:'assistant', content:[]}});
  h.provider_stream_event({data:{orphan:true}});
  h.before_provider_request(request); h.agent_settled({aborted:false}); h.provider_stream_event({data:{orphan:true}});
  for(const row of rows.filter(r => r.type==='provider_stream_event')) { assert.equal(row.requestId,null); assert.ok(row.associationIssue); }
});

test('blocked and unfinished tool attempts keep missing execution evidence', () => {
  const {handlers:h, rows} = capture();
  h.tool_call({toolCallId:'blocked', toolName:'bash', input:{command:'x'}});
  h.tool_result({toolCallId:'blocked', toolName:'bash', isError:true, content:[{type:'text',text:'blocked'}]});
  h.tool_execution_end({toolCallId:'blocked',toolName:'bash',isError:true,result:{content:[]}});
  h.tool_execution_start({toolCallId:'running',toolName:'bash',args:{command:'server'},parentToolCallId:'outer'});
  const end = rows.find(r=>r.type==='tool_execution_end');
  assert.equal(Object.hasOwn(end,'durationMs'),false);
  assert.equal(rows.at(-1).parentToolCallId,'outer');
  assert.equal(rows.filter(r=>r.type==='tool_call').length,1);
  assert.equal(rows.filter(r=>r.type==='tool_result').length,1);
});

test('optional native duration and abort stay optional and preserve zero', () => {
  const {handlers:h, rows} = capture();
  h.tool_execution_end({toolCallId:'call',toolName:'bash',result:{},isError:false,durationMs:0});
  h.message_end({message:{role:'assistant',content:[],durationMs:12}});
  h.agent_settled({aborted:true}); h.agent_settled({});
  assert.equal(rows[1].durationMs,0);
  assert.equal(rows[2].message.durationMs,12);
  assert.equal(rows[3].aborted,true);
  assert.equal(Object.hasOwn(rows[4],'aborted'),false);
});

test('sink failure is diagnostic only and every observer returns undefined', () => {
  const {handlers:h, diagnostics} = capture({write:()=>{throw Error('disk full');}});
  assert.equal(h.before_provider_request(request),undefined);
  assert.equal(h.agent_settled({aborted:false}),undefined);
  assert.ok(diagnostics.some(d=>d.startsWith('mellum-trace:')));
});

test('observer leaves frozen inputs unchanged and does not invent guard decisions', () => {
  const {handlers:h} = capture();
  const event = Object.freeze({payload:Object.freeze({messages:Object.freeze([])})});
  assert.equal(h.before_provider_request(event),undefined);
  assert.equal(h.tool_call(Object.freeze({toolCallId:'x',toolName:'read',input:Object.freeze({path:'x'})})),undefined);
  assert.equal(h.tool_result(Object.freeze({toolCallId:'x',toolName:'read',isError:false,content:Object.freeze([])})),undefined);
  assert.equal(h.agent_start({}),undefined); assert.equal(h.agent_end({}),undefined);
});

test('recorded Pi 1.1 final response replays chunks and actual normalized reply', async () => {
  const {readFileSync}=await import('node:fs');
  const source=JSON.parse(readFileSync(new URL('../../tests/fixtures/telemetry/pi110.events.json',import.meta.url),'utf8'));
  const {handlers:h,rows}=capture();
  for(const event of source) {
    const hook=event.type==='provider_request' ? 'before_provider_request' : event.type;
    h[hook](structuredClone(event));
  }
  const chunks=rows.filter(row=>row.type==='provider_stream_event');
  assert.equal(chunks.length,22);
  const final=rows.find(row=>row.type==='message_end').message;
  assert.equal(final.durationMs,2276);
  assert.equal(final.stopReason,'stop');
  const visible=chunks.flatMap(row=>row.data.choices??[]).map(c=>c.delta?.content??'').join('');
  assert.equal(visible,final.content.find(b=>b.type==='text').text);
  assert.equal(rows[0].runtime.piVersion,'1.1.0');
  assert.equal(rows.at(-1).aborted,false);
  assert.ok(chunks.every(c=>c.requestId===rows[1].requestId));
});

test('shipped guard hook decisions and payloads are identical with telemetry', async () => {
  const {default:installGuards}=await import('../../extensions/mellum-guards.ts');
  async function run(withTelemetry) {
    const listeners={}, rows=[], saved=process.env.MELLUM_WORKER_RUNS;
    process.env.MELLUM_WORKER_RUNS='0';
    const pi={on:(name,fn)=>{(listeners[name]??=[]).push(fn);}};
    try { installGuards(pi,{fetch:()=>Promise.reject(Error('no server'))}); }
    finally { if(saved===undefined) delete process.env.MELLUM_WORKER_RUNS; else process.env.MELLUM_WORKER_RUNS=saved; }
    if(withTelemetry) recorder.installRecorder(pi,{write:r=>rows.push(r),runtime:{piVersion:'1.1.0'},runId:'run'});
    const decisions=[], payload=structuredClone(request);
    const events=[['before_provider_request',payload],...Array.from({length:8},()=>['tool_call',{toolCallId:'read',toolName:'read',input:{path:'x'}}]),
      ['turn_end',{message:{role:'assistant',content:[],stopReason:'stop'},toolResults:[]}],['agent_before_settle',{}]];
    for(const [name,event] of events) {
      const results=[];
      for(const handler of listeners[name]??[]) { const result=await handler(event); if(result!==undefined) results.push(result); }
      decisions.push(results);
    }
    return {decisions,payload};
  }
  const plain=await run(false), observed=await run(true);
  assert.ok(plain.decisions.flat().some(d=>d.block));
  assert.ok(plain.decisions.flat().some(d=>d.continue));
  assert.deepEqual(observed,plain);
});
