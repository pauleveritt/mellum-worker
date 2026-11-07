# 6-bit Mellum — new rungs 10–12 (n=3, mediated)

Model: `Mellum2.1-12B-A2.5B-Thinking-6bit`. Direct mode, `tuned`, guards on,
native tool-calling, **mediated** (committed frozen phase test placed,
`--redispatch 5`, effort-ramp). Repeat 3 per rung.

| rung | run | result | wall | redispatches | phase |
|---|---|---|---|---|---|
| 10 | r1 | **PASS** | 226s | 2 | 5 — Archive & Audit |
| 10 | r2 | **PASS** | 174s | 1 | |
| 10 | r3 | **PASS** | 127s | 0 | |
| 11 | r1 | **PASS** | 161s | 2 | 6 — DB reporting |
| 11 | r2 | **PASS** | 74s | 0 | |
| 11 | r3 | **PASS** | 144s | 2 | |
| 12 | r1 | **PASS** | 53s | 0 | 7 — sum a huge file |
| 12 | r2 | **PASS** | 83s | 1 | |
| 12 | r3 | **PASS** | 111s | 2 | |
| **rung 10** | | **3/3** | 176s avg | | |
| **rung 11** | | **3/3** | 126s avg | | |
| **rung 12** | | **3/3** | 82s avg | | |
| **total** | | **9/9** | | | |

The mediation is load-bearing: **7 of 9** runs were re-dispatched at least once
(the frozen test caught a near-miss and the worker fixed it), and only 2 passed
on the first attempt. The rungs are winnable and repeatable with the run
standard; the decoy (rung 10), the trap row (rung 11) and the context overflow
(rung 12) did not trip the 6-bit.
