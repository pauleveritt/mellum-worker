Task: rename the function `fetch_rows` to `load_rows` everywhere in this repo (/private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-th4dgls3/rung3).

Exact scope (verified with rg, do not expand):
- rows.py line 1: `def fetch_rows(source):` -> `def load_rows(source):`
- report.py line 1: `from rows import fetch_rows` -> `from rows import load_rows`
- report.py line 5: `fetch_rows(source)` call -> `load_rows(source)`

Rules:
- Make ONLY these renames. Do not reformat, do not add comments, do not rename anything else, do not create new files, do not touch tests' logic.
- After editing, run `grep -rn "fetch_rows" .` and confirm it prints nothing (exit status 1).
- Report back: the exact commands you ran, the diff (`git diff`), and the grep result. If anything unexpected appears, stop and report it rather than guessing.