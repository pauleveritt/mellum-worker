import assert from 'node:assert/strict';
import test from 'node:test';
import {install} from '../remedies/check/external-acceptance.ts';

function fixture(replies) {
  const handlers = {}, requests = [];
  const pi = {on: (name, fn) => {handlers[name] = fn;}};
  install(pi, {taskId: 'task', exchange: async request => {
    requests.push(request);
    const reply = replies.shift();
    return {...reply, task_id: request.task_id, request_id: request.request_id};
  }});
  return {handlers, requests};
}

test('protected acceptance requires a controller before any inference', () => {
  assert.throws(() => install({on() {}}, {taskId: ''}), /controller/);
});

test('pass settles without a model continuation', async () => {
  const {handlers, requests} = fixture([{status:'verified', continue:false}]);
  assert.equal(await handlers.agent_before_settle({}), undefined);
  assert.equal(requests.length, 1);
});

test('failure continues same task with bounded custom feedback; final failure still checked', async () => {
  const {handlers, requests} = fixture([
    {status:'repairing', continue:true, feedback:'fix requirement'},
    {status:'repairing', continue:true, feedback:'x'.repeat(10000)},
    {status:'repair_exhausted', continue:false},
  ]);
  const first = await handlers.agent_before_settle({});
  assert.equal(first.continue, true);
  assert.equal(first.entries[0].customType, 'external-acceptance');
  assert.equal(first.entries[0].content, 'fix requirement');
  assert.equal((await handlers.agent_before_settle({})).entries[0].content.length, 8000);
  assert.equal(await handlers.agent_before_settle({}), undefined);
  assert.deepEqual(requests.map(r => r.sequence), [1,2,3]);
  assert.equal(new Set(requests.map(r => r.request_id)).size, 3);
  assert.equal(new Set(requests.map(r => r.task_id)).size, 1);
});

test('stale or malformed reply cannot continue', async () => {
  let handler;
  install({on: (_name, fn) => {handler = fn;}}, {taskId:'task', exchange: async () => ({
    task_id:'other', request_id:'stale', continue:true, feedback:'untrusted'
  })});
  await assert.rejects(handler({}), /reply/);
});

test('checker error and timeout do not trigger inference repairs', async () => {
  for (const status of ['checker_error','timeout','integrity_error']) {
    const {handlers} = fixture([{status,continue:false}]);
    assert.equal(await handlers.agent_before_settle({}), undefined);
  }
});
