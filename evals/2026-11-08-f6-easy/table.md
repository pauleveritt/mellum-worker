# F.6 — four Easy arms on one held A40 pod (counted, n = 24 per arm)

Pod `g5my3h9kfd9x9g` (NVIDIA A40, Secure Cloud, $0.59/hour), [host card](host-card.json), commit
`26b17d60`, 2026-11-08 14:45 to 20:57 UTC. 96 sessions, arms interleaved round-robin, every session
as the unprivileged `mellum-session` user, `--arm vanilla`, budget 64 requests / 32,000 output
tokens, stall 180 s. Arms in [arms.json](arms.json). Runs under `~/mellum-runs/f6/f6-easy`, raw traces
not committed. Pod numbers do not pool with the Mac's, and the launch check does not compare with
R.1's: see the [note](../../docs/superpowers/research/2026-11-08-f6-held-pod.md).

The medians below leave out stalled sessions; the note gives the all-session medians.

| Arm | n | Mean checks | Full passes | Stalled | Censored | Budget endings | Median requests | Median output tokens |
|---|---|---|---|---|---|---|---|---|
| mediated | 24 | 11.96 | 11 | 14 | 0 | 6 | 45.50 | 32245.50 |
| settle-only | 24 | 12.08 | 16 | 12 | 0 | 0 | 31.50 | 16094 |
| show-only | 24 | 9.54 | 6 | 12 | 0 | 3 | 35 | 15716 |
| vanilla | 24 | 9.88 | 2 | 6 | 0 | 0 | 23.50 | 9595.50 |

## Misses per check

| Check | mediated (of 24) | settle-only (of 24) | show-only (of 24) | vanilla (of 24) |
|---|---|---|---|---|
| test_extending_page_can_override_layout_title | 11 | 5 | 16 | 22 |
| test_main_guard_launches_uvicorn_with_reload_and_keeps_serving | 3 | 5 | 9 | 9 |
| test_home_has_hero_and_welcoming_paragraph | 1 | 2 | 6 | 4 |
| test_home_still_has_navigation_links | 1 | 1 | 6 | 4 |
| test_home_still_returns_200_and_tagline | 1 | 1 | 6 | 4 |
| test_home_has_html5_doctype | 1 | 1 | 5 | 4 |
| test_home_html_element_declares_english_language | 1 | 1 | 5 | 4 |
| test_home_renders_home_template_extending_shared_base | 1 | 1 | 5 | 4 |
| test_layout_ends_body_with_bootstrap5_cdn_bundle | 1 | 1 | 5 | 4 |
| test_layout_has_bootstrap5_cdn_stylesheet_in_head | 1 | 1 | 5 | 4 |
| test_layout_has_python_favicon | 1 | 1 | 5 | 4 |
| test_layout_has_responsive_viewport | 1 | 1 | 5 | 4 |
| test_layout_title_defaults_to_agentclinic | 1 | 1 | 5 | 4 |
