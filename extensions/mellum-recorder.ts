/**
 * The recorder: the one instrument that records a Pi run's effort — turns,
 * tokens, tool calls, timing, compaction — as a JSONL trace. Load it on a
 * run with `-e extensions/mellum-recorder.ts` and `MELLUM_TRACE_FILE` set; the
 * harness and the ladder both do. Without `MELLUM_TRACE_FILE` it records
 * nothing. The summarisers (`learn/code/harness.py`, `ladder/ladder/score.py`)
 * read the trace by event `type`.
 *
 * This is the single recorder: it unifies the lesson recorder (which added the
 * compaction row) and the ladder recorder (the fuller instrument — timing,
 * tool↔request association, streaming and version stamps). Nothing is lost.
 */
import { appendFileSync, readFileSync, realpathSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import { dirname, join } from 'node:path';
import { performance } from 'node:perf_hooks';

function runtimeIdentity() {
  let entryPath = process.argv[1] ?? null;
  let piVersion = null;
  try {
    entryPath = realpathSync(entryPath);
    for (let dir = dirname(entryPath); ; dir = dirname(dir)) {
      try {
        const pkg = JSON.parse(readFileSync(join(dir, 'package.json'), 'utf8'));
        if (pkg.name?.endsWith('/pi-coding-agent')) { piVersion = pkg.version; break; }
      } catch { /* Not every ancestor is a package. */ }
      if (dirname(dir) === dir) break;
    }
  } catch { /* A compiled runtime may expose only execPath. */ }
  return { piVersion, entryPath, execPath: process.execPath, cwd: process.cwd() };
}

export function installRecorder(pi, options = {}) {
  const {
    write = row => appendFileSync(process.env.MELLUM_TRACE_FILE, JSON.stringify(row) + '\n'),
    diagnose = text => process.stderr.write(text + '\n'),
    wallClock = () => Date.now(), monotonicClock = () => performance.now(),
    runtime = runtimeIdentity(), runId = process.env.MELLUM_TRACE_RUN_ID ?? randomUUID(),
    pid = process.pid,
  } = options;
  const instanceId = randomUUID(), started = monotonicClock(), toolRequests = new Map();
  let seq = 0, requests = 0, activeRequest = null;
  function record(fields, requestId = activeRequest) {
    const row = {traceSchema:1, runId, instanceId, seq:++seq, timestamp:new Date(wallClock()).toISOString(),
      elapsedMs:monotonicClock()-started, pid, requestId, ...fields};
    try { write(row); }
    catch (error) { diagnose(`mellum-trace: record not written: ${error.message}`); }
  }
  function toolFields(event) {
    const requestId = toolRequests.get(event.toolCallId) ?? null;
    return { requestId, ...(event.toolCallId !== undefined ? {toolCallId:event.toolCallId} : {}),
      ...(event.parentToolCallId !== undefined ? {parentToolCallId:event.parentToolCallId} : {}),
      ...(requestId === null ? {associationIssue:'tool request association unavailable'} : {}) };
  }
  record({type:'instance_start', runtime}, null);
  pi.on('before_provider_request', event => {
    activeRequest = `${instanceId}:${++requests}`;
    record({type:'provider_request', request:requests, payload:event.payload});
  });
  pi.on('provider_stream_event', event => {
    record({type:'provider_stream_event', provider:event.provider, api:event.api, model:event.model, data:event.data,
      ...(activeRequest === null ? {associationIssue:'no observed active request'} : {})});
  });
  pi.on('message_end', event => {
    if (event.message.role !== 'assistant') return;
    for (const block of event.message.content ?? []) {
      if (block.type === 'toolCall' && block.id) toolRequests.set(block.id, activeRequest);
    }
    record({type:'message_end', message:event.message});
    activeRequest = null;
  });
  // Compaction is a budget question: whether Pi asked, and whether the worker
  // let it. The recorder loads after the worker, so a compaction the worker
  // cancels never reaches this handler: a `before_compact` row only appears
  // when a compaction was allowed to run.
  pi.on('session_before_compact', event =>
    record({type:'before_compact', reason: event?.reason ?? null}));
  pi.on('tool_call', event => { record({type:'tool_call', toolName:event.toolName, input:event.input, ...toolFields(event)}); });
  pi.on('tool_result', event => { record({type:'tool_result', toolName:event.toolName, isError:event.isError, content:event.content, ...toolFields(event)}); });
  pi.on('tool_execution_start', event => { record({type:'tool_execution_start', toolName:event.toolName, args:event.args, ...toolFields(event)}); });
  pi.on('tool_execution_end', event => {
    record({type:'tool_execution_end', toolName:event.toolName, result:event.result, isError:event.isError,
      ...toolFields(event), ...(event.durationMs !== undefined ? {durationMs:event.durationMs} : {})});
  });
  pi.on('agent_start', () => { record({type:'agent_start'}, null); });
  pi.on('agent_end', () => { record({type:'agent_end'}, null); });
  pi.on('agent_settled', event => {
    record({type:'agent_settled', ...(event.aborted !== undefined ? {aborted:event.aborted} : {})}, null);
    activeRequest = null;
  });
}

export default function install(pi) {
  if (process.env.MELLUM_TRACE_FILE) installRecorder(pi);
}
