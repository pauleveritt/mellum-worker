| witness | Paul's label | verdict | as expected | failing tests |
|---|---|---|---|---|
| known_good | valid | pass | yes |  |
| caption | valid | pass | yes |  |
| strong_caption | valid | pass | yes |  |
| state_caption | valid | pass | yes |  |
| post_init_counter | valid | pass | yes |  |
| emphasised_word_after_text | valid | pass | yes |  |
| comment_in_card | valid | pass | yes |  |
| newest_first | valid | reject | yes | test_board_shows_status_badge_and_the_action_forms |
| textual_date | valid | pass | yes |  |
| inline_brand | valid | pass | yes |  |
| separate_route_counter | defect | reject | yes | test_new_complaints_default_open_with_distinct_auto_ids |
| renumber_on_append | defect | reject | yes | test_new_complaints_default_open_with_distinct_auto_ids |
| route_overwrites_with_max | defect | reject | yes | test_new_complaints_default_open_with_distinct_auto_ids |
| negated_caption | defect | reject | yes | test_board_shows_status_badge_and_the_action_forms, test_resolve_then_reopen_sets_status_303_and_keeps_order |
| negated_strong | defect | reject | yes | test_board_shows_status_badge_and_the_action_forms, test_resolve_then_reopen_sets_status_303_and_keeps_order |
| negated_span | defect | reject | yes | test_board_shows_status_badge_and_the_action_forms, test_resolve_then_reopen_sets_status_303_and_keeps_order |
| hidden_label | defect | reject | yes | test_board_shows_status_badge_and_the_action_forms, test_resolve_then_reopen_sets_status_303_and_keeps_order |
| both_labels | defect | reject | yes | test_board_shows_status_badge_and_the_action_forms, test_resolve_then_reopen_sets_status_303_and_keeps_order |
| state_never_changes | defect | reject | yes | test_board_shows_status_badge_and_the_action_forms, test_resolve_then_reopen_sets_status_303_and_keeps_order |
| redirect_home | defect | reject | yes | test_home_renders_the_tagline_and_base_layout |
| redirect_board | defect | reject | yes | test_add_complaint_redirects_303_to_the_board_and_appears, test_add_form_posts_to_complaints_with_the_named_fields, test_board_lists_seed_complaints_with_name_date_and_text, test_board_shows_status_badge_and_the_action_forms, test_resolve_then_reopen_sets_status_303_and_keeps_order |
| html4_doctype | defect | reject | yes | test_board_lists_seed_complaints_with_name_date_and_text, test_home_renders_the_tagline_and_base_layout |
| brand_in_comment | defect | reject | yes | test_board_lists_seed_complaints_with_name_date_and_text, test_home_renders_the_tagline_and_base_layout |
| no_nav | defect | reject | yes | test_board_lists_seed_complaints_with_name_date_and_text, test_home_renders_the_tagline_and_base_layout |
| hidden_nav | defect | reject | yes | test_board_lists_seed_complaints_with_name_date_and_text, test_home_renders_the_tagline_and_base_layout |
| seed_suffix | defect | reject | yes | test_seed_complaints_include_the_exact_scope_creep_text |
| date_tokens | defect | reject | yes | test_board_lists_seed_complaints_with_name_date_and_text |
| disconnected_form | defect | reject | yes | test_add_form_posts_to_complaints_with_the_named_fields |
| disabled_input | defect | reject | yes | test_add_form_posts_to_complaints_with_the_named_fields |
| fieldset_disabled | defect | reject | yes | test_add_form_posts_to_complaints_with_the_named_fields |
| hidden_name_input | defect | reject | yes | test_add_form_posts_to_complaints_with_the_named_fields |
| hidden_input | defect | reject | yes | test_add_form_posts_to_complaints_with_the_named_fields |
| truncating_store | defect | reject | yes | test_add_complaint_redirects_303_to_the_board_and_appears, test_new_complaints_default_open_with_distinct_auto_ids |
| no_model_state | defect | reject | yes | test_board_shows_status_badge_and_the_action_forms, test_resolve_then_reopen_sets_status_303_and_keeps_order |
| changes_every_complaint | defect | reject | yes | test_board_shows_status_badge_and_the_action_forms, test_resolve_then_reopen_sets_status_303_and_keeps_order |
| buttons_do_not_submit | defect | reject | yes | test_board_shows_status_badge_and_the_action_forms, test_resolve_then_reopen_sets_status_303_and_keeps_order |
| disabled_buttons | defect | reject | yes | test_board_shows_status_badge_and_the_action_forms, test_resolve_then_reopen_sets_status_303_and_keeps_order |
| reverses_board | defect | reject | yes | test_board_shows_status_badge_and_the_action_forms, test_resolve_then_reopen_sets_status_303_and_keeps_order |
| swaps_seed_order | defect | reject | yes | test_board_shows_status_badge_and_the_action_forms, test_resolve_then_reopen_sets_status_303_and_keeps_order |
| string_ids | defect | reject | yes | test_new_complaints_default_open_with_distinct_auto_ids, test_resolve_then_reopen_sets_status_303_and_keeps_order |
| float_ids | defect | reject | yes | test_new_complaints_default_open_with_distinct_auto_ids |
| base-r02 | defect | reject | yes | test_board_lists_seed_complaints_with_name_date_and_text, test_complaint_dataclass_carries_the_spec_fields, test_home_renders_the_tagline_and_base_layout, test_new_complaints_default_open_with_distinct_auto_ids |
| base-r03 | defect | reject | yes | test_board_lists_seed_complaints_with_name_date_and_text, test_complaint_dataclass_carries_the_spec_fields, test_home_renders_the_tagline_and_base_layout, test_new_complaints_default_open_with_distinct_auto_ids |

43/43 as expected
