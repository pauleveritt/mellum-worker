# `--acceptance-test` in Mode vs shipped Mode — rung 9

6-bit Mellum, `--mode mode` (`mellum-mode.ts` + `mellum-guards.ts` +
`mellum-facts.ts`), rung 9, n=3.

| config | rung 9 | wall | `mellum-ncm.ts` fires |
|---|---|---|---|
| shipped Mode — no `--acceptance-test`, no gate ([record](../2026-10-21-shipped-mode-rung9/)) | **0/3** | 250–402s | n/a |
| + `--acceptance-test` (frozen test) + `mellum-ncm.ts` (this record) | **3/3** | 110 / 145 / 108s | **0** |

**`--acceptance-test` is the lever** (0/3 → 3/3): it gives v7 its named target.
**`mellum-ncm.ts` fired 0 times** — the 6-bit passes first-try, so the gate is a
non-regressing safety net here, not the driver. For reference, direct +
`--acceptance-test` was also 3/3.
