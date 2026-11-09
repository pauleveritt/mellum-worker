**Rule result:** not met (strict passes 25 against 2, met; median requests 2.40 times, met; median output tokens 4.47 times, not met). The medians in this table leave out stalled sessions; the rule's are over all 32: vanilla 21.5 requests and 7,598.5 output tokens, base 51.5 and 33,993.5. See [the result note](../../docs/superpowers/research/2026-11-09-easy-count-result.md).

| Arm | n | Mean checks | Full passes | Strict passes | Stalled | Censored | Budget endings | Median requests | Median output tokens |
|---|---|---|---|---|---|---|---|---|---|
| base | 32 | 12.88 | 30 | 25 | 0 | 0 | 10 | 51.50 | 33993.50 |
| vanilla | 32 | 9.91 | 2 | 2 | 7 | 0 | 0 | 21 | 7597 |

## Misses per check

| Check | base (of 32) | vanilla (of 31) |
|---|---|---|
| test_extending_page_can_override_layout_title | 1 | 28 |
| test_main_guard_launches_uvicorn_with_reload_and_keeps_serving | 1 | 12 |
| test_home_has_hero_and_welcoming_paragraph | 1 | 5 |
| test_home_still_returns_200_and_tagline | 1 | 5 |
| test_home_has_html5_doctype | 0 | 4 |
| test_home_html_element_declares_english_language | 0 | 4 |
| test_home_renders_home_template_extending_shared_base | 0 | 4 |
| test_home_still_has_navigation_links | 0 | 4 |
| test_layout_ends_body_with_bootstrap5_cdn_bundle | 0 | 4 |
| test_layout_has_bootstrap5_cdn_stylesheet_in_head | 0 | 4 |
| test_layout_has_python_favicon | 0 | 4 |
| test_layout_has_responsive_viewport | 0 | 4 |
| test_layout_title_defaults_to_agentclinic | 0 | 4 |
