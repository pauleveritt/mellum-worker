#!/usr/bin/env node
// A fake Pi that asks its profile's provider for completions until it is refused, then exits at once.
import {readFileSync, writeFileSync} from 'node:fs';
if (process.argv.includes('--version')) { console.log('1.4.0'); process.exit(0); }
const models = JSON.parse(readFileSync(`${process.env.PI_CODING_AGENT_DIR}/models.json`, 'utf8'));
const base = Object.values(models.providers)[0].baseUrl;
let ok = 0, status = 200;
while (ok < 50) {
  const response = await fetch(`${base}/chat/completions`, {method: 'POST', headers: {'content-type': 'application/json'},
    body: JSON.stringify({messages: [{role: 'user', content: 'hi'}], stream: true})});
  await response.arrayBuffer();
  status = response.status;
  if (status !== 200) break;
  ok += 1;
}
writeFileSync('requests.txt', `${ok} ${status}\n`);
process.exit(status === 200 ? 0 : 1);
