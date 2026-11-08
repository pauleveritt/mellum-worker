# `prompt/verify-the-spec` on Easy — a screen, a lead (n = 3 per arm)

Same host and settings as [R.1 step three](../2026-11-07-r1-step-three/table.md), with the host card
refreshed (`~/mellum-runs/r1/host-card-screen3.json`, sha256 `9b201fd5d567197a…`). Base is Vanilla,
so the unit runs as `--arm vanilla --remedy prompt/verify-the-spec`. Runs under
`~/mellum-runs/r1/screen3`, raw traces not committed. Analysis in the
[note](../../docs/superpowers/research/2026-11-08-verify-the-spec-screen.md). It is not a rate.

| Arm | n | Mean checks | Full passes | Stalled | Censored | Budget endings | Median requests | Median output tokens |
|---|---|---|---|---|---|---|---|---|
| vanilla | 3 | 7.67 | 0 | 1 | 0 | 0 | 40.5 | 11,732.5 |
| verify-the-spec | 3 | 10 | 0 | 1 | 0 | 0 | 24 | 8,295.5 |

## Misses per check

| Check | vanilla (of 3) | verify-the-spec (of 3) |
|---|---|---|
| test_extending_page_can_override_layout_title | 3 | 3 |
| test_main_guard_launches_uvicorn_with_reload_and_keeps_serving | 2 | 0 |
| each of 6 layout and template checks | 1 | 1 |
| each of 5 home-page checks | 1 | 0 |

## Did the hook act?

Yes. The line reached every request in all three unit sessions (`line_in_trace` 13, 33 and 19 for
13, 31 and 17 requests).

## The sessions

| Session | Ending | Failed | Requests | What happened |
|---|---|---|---|---|
| vanilla-r01 | stalled | 13 | 63 | ended on a foreground `uvicorn … --reload` |
| vanilla-r02 | settled | 1 | 48 | title only |
| vanilla-r03 | settled | 2 | 33 | title and launch |
| verify-the-spec-r01 | stalled | 1 | 13 | title only; ended on a foreground `python app.py` |
| verify-the-spec-r02 | settled | 7 | 31 | built no templates: its pages are in `app.py` |
| verify-the-spec-r03 | settled | 1 | 17 | title only |

The means are not comparable at this n: Vanilla's is carried by r01's 13 failures, and the unit's by
r02's seven. r03's reasoning names the requirement and defers it: "We'll set in base template block
title maybe but for now just `<title>AgentClinic</title>`."
