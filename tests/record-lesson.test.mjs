import assert from "node:assert/strict";
import test from "node:test";
import { installRecorder } from "../extensions/mellum-recorder.ts";

function capture() {
  const handlers = {}, rows = [];
  installRecorder({ on: (name, fn) => { handlers[name] = fn; } },
    { write: (row) => rows.push(row), runId: "run", pid: 7 });
  return { handlers, rows };
}

test("the recorder keeps the run's shape", () => {
  const { handlers: h, rows } = capture();
  h.before_provider_request({ payload: { messages: [] } });
  h.message_end({ message: { role: "assistant", content: [{ type: "text", text: "ok" }] } });
  h.tool_call({ toolCallId: "c1", toolName: "bash", input: { command: "ls" } });
  h.tool_result({ toolCallId: "c1", toolName: "bash", isError: true });
  h.agent_settled({ aborted: false });
  assert.deepEqual(rows.map((r) => r.type), [
    "instance_start", "provider_request", "message_end", "tool_call",
    "tool_result", "agent_settled",
  ]);
  assert.deepEqual(rows.map((r) => r.seq), [1, 2, 3, 4, 5, 6]);
  assert.equal(rows[1].request, 1);
  assert.equal(rows[4].isError, true);
  for (const row of rows) {
    assert.equal(row.traceSchema, 1);
    assert.equal(row.runId, "run");
    assert.ok(Number.isFinite(Date.parse(row.timestamp)));
  }
});

test("the recorder notes an attempted compaction", () => {
  const { handlers: h, rows } = capture();
  h.session_before_compact({ reason: "threshold" });
  assert.deepEqual(rows.map((r) => r.type), ["instance_start", "before_compact"]);
  assert.equal(rows[1].reason, "threshold");
});
