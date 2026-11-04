import assert from 'node:assert/strict';
import test from 'node:test';
import { channel } from 'node:diagnostics_channel';
import { installTransportObserver } from '../extensions/mellum-recorder.ts';

test('passive transport events retain boundaries and redact sensitive fields', () => {
  const rows = [];
  const stop = installTransportObserver({ write: r => rows.push(r), requestId: () => 'model:1' });
  const request = { method: 'POST', path: '/v1/chat/completions?secret=value',
    origin: 'http://user:password@localhost:8002', headers: 'Authorization: secret' };
  try {
    channel('undici:request:create').publish({request});
    channel('undici:request:headers').publish({request, response: {statusCode: 200,
      headers: [Buffer.from('x-mellum-transport-id'), Buffer.from('relay-1'),
        Buffer.from('set-cookie'), Buffer.from('secret')]}});
    const cause = Object.assign(new Error('secret response'), {code:'ECONNRESET'});
    channel('undici:request:error').publish({request,
      error: new TypeError('secret URL', {cause})});
    assert.deepEqual(rows.map(r => r.boundary), ['created', 'headers', 'error']);
    assert.equal(rows[1].relayId, 'relay-1');
    assert.equal(rows[0].requestId, 'model:1');
    assert.equal(rows[2].causes[1].code, 'ECONNRESET');
    assert.equal(rows[0].transportId, rows[2].transportId);
    assert.doesNotMatch(JSON.stringify(rows), /secret|password|Authorization|set-cookie/);
    assert.equal(request.path, '/v1/chat/completions?secret=value');
  } finally { stop(); }
});

test('diagnostic sink failure cannot escape a diagnostics callback', () => {
  const errors = [];
  const stop = installTransportObserver({ write: () => { throw new Error('disk full'); },
    diagnose: text => errors.push(text) });
  try {
    assert.doesNotThrow(() => channel('undici:request:create').publish({request:{}}));
    assert.equal(errors.length, 1);
  } finally { stop(); }
});
