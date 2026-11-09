#!/usr/bin/env node
// A fake Pi for phase runs: writes the app it is given, the gate verdicts and trace lines it is told
// to, records its prompt, and with FAKE_SPEND asks for completions until the budget refuses it.
import {appendFileSync, copyFileSync, readFileSync} from 'node:fs';
if (process.argv.includes('--version')) { console.log('1.4.0'); process.exit(0); }
if (process.env.FAKE_APP) copyFileSync(process.env.FAKE_APP, 'app.py');
if (process.env.FAKE_TRACE_LINE) appendFileSync(process.env.MELLUM_TRACE_FILE, process.env.FAKE_TRACE_LINE + '\n');
if (process.env.FAKE_GATE && process.env.MELLUM_GATE_LOG) appendFileSync(process.env.MELLUM_GATE_LOG, process.env.FAKE_GATE);
appendFileSync('prompts-seen.txt', JSON.stringify(process.argv.at(-1)) + '\n');
if (process.env.FAKE_SPEND) {
  const models = JSON.parse(readFileSync(`${process.env.PI_CODING_AGENT_DIR}/models.json`, 'utf8'));
  const base = Object.values(models.providers)[0].baseUrl;
  for (let i = 0; i < 50; i++) {
    const response = await fetch(`${base}/chat/completions`, {method: 'POST', headers: {'content-type': 'application/json'},
      body: JSON.stringify({messages: [{role: 'user', content: 'hi'}], stream: true})});
    await response.arrayBuffer();
    if (response.status !== 200) process.exit(1);
  }
}
process.exit(0);
