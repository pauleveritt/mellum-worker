| Arm | n | Mean checks | Full passes | Strict passes | Stalled | Censored | Budget endings | Median requests | Median output tokens |
|---|---|---|---|---|---|---|---|---|---|
| base | 3 | 13.67 | 0 | 0 | 0 | 0 | 1 | 331 | 253976 |
| vanilla | 3 | 8.33 | 0 | 0 | 0 | 0 | 1 | 123 | 77518 |

## Misses per check

| Check | base (of 3) | vanilla (of 2) |
|---|---|---|
| test_complaint_identity_is_stable_and_keyword_only | 3 | 2 |
| test_reopen_route_marks_complaint_open_and_redirects | 3 | 2 |
| test_resolve_reopen_does_not_reorder_the_board | 3 | 2 |
| test_resolve_route_marks_complaint_resolved_and_redirects | 3 | 2 |
| test_seed_complaints_have_distinct_ids | 1 | 2 |
| test_complaint_model_contract_is_preserved | 0 | 1 |
