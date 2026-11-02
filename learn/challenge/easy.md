---
title: Easy
---

# Easy — the home page

The first level of [the Challenge](index.md): Phase 1 of AgentClinic, graded by
**4 hidden checks**. A setup that holds together passes it in minutes.

![The Easy tier: a small robot building a single web page](../assets/illustrations/tier-easy.webp){ .illustration }

**Build**

- `app.py` exposes the FastAPI app as `app`.
- `templates/base.html`: HTML5 doctype, `lang="en"`, Bootstrap 5 from a CDN, a navbar linking Home (`/`) and Complaints (`/complaints`).
- `/` renders the exact tagline *"Come in. Sit down. Tell us about your human."*.
- `uv run --frozen python app.py` starts uvicorn with reload, only under `if __name__ == "__main__"`.

**Watch out** — the `do not start servers` rule: a foreground server that never returns burns a bare run to the deadline.

**Graded (4)** — doctype · `lang="en"` · `GET /` → 200 with the tagline · navbar links.

Run it with `/challenge easy` (see [Attempt it](index.md#attempt-it)). Next:
[Medium — the complaints board](medium.md).
