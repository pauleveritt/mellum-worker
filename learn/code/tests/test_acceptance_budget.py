"""Whole-task budgets must include requests outside normal agent hooks."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from acceptance_budget import reconcile, summarize, wilson


LOG = '''slot operator(): id 0 | task 10 | new prompt, task.n_tokens = 200
slot print_timing: id 0 | task 10 | prompt eval time = 3.0 ms / 200 tokens
slot print_timing: id 0 | task 10 | eval time = 4.0 ms / 50 tokens
slot operator(): id 0 | task 11 | new prompt, task.n_tokens = 300
slot print_timing: id 0 | task 11 | prompt eval time = 3.0 ms / 100 tokens
slot print_timing: id 0 | task 11 | eval time = 4.0 ms / 70 tokens
'''
RELAY = [{"boundary": "created", "id": "a", "method": "POST", "path": "/v1/chat/completions", "timestamp": "2026-11-04T01:00:00Z"},
         {"boundary": "complete", "id": "a"},
         {"boundary": "created", "id": "b", "method": "POST", "path": "/v1/chat/completions", "timestamp": "2026-11-04T01:00:02Z"},
         {"boundary": "complete", "id": "b"}]


def test_compaction_and_failed_usage_are_included_in_backend_totals():
    trace = [{"type": "provider_request", "requestId": "agent"},
             {"type": "message_end", "requestId": "agent", "message": {"role": "assistant", "stopReason": "error"}}]
    result = reconcile(LOG, RELAY, trace, [])
    assert result["requests"] == 2 and result["output_tokens"] == 120
    assert result["outside_agent_requests"] == 1 and result["agent_output_tokens"] is None
    assert result["reconciled"]


def test_unfinished_generation_is_unknown_not_a_partial_sum():
    result = reconcile(LOG.split("slot print_timing: id 0 | task 11 | eval time")[0], RELAY, [], [])
    assert result["output_tokens"] is None and not result["reconciled"]
    assert result["requests"] == 2


def test_non_generation_gets_are_excluded_and_repairs_share_task_budget():
    relay = [{"boundary": "created", "id": "health", "method": "GET", "path": "/health"}, *RELAY]
    receipts = [{"continue": True, "timestamp": "2026-11-04T01:00:01Z"}]
    result = reconcile(LOG, relay, [], receipts)
    assert [r["repair_index"] for r in result["generations"]] == [0, 1]
    assert result["requests"] == 2


def test_total_cost_includes_unsuccessful_tasks_and_zero_success_is_undefined():
    results = [{"usable": True, "budget": {"requests": 2, "output_tokens": 120, "reconciled": True}},
               {"usable": False, "budget": {"requests": 3, "output_tokens": 300, "reconciled": True}}]
    total = summarize(results)
    assert total["output_tokens"] == 420 and total["output_per_usable"] == 420
    assert total["requests_per_usable"] == 5
    assert summarize([results[1]])["output_per_usable"] is None


def test_missing_usage_prevents_budget_decision():
    total = summarize([{"usable": True, "budget": {"requests": 1, "output_tokens": None, "reconciled": False}}])
    assert total["output_tokens"] is None and total["output_per_usable"] is None


def test_wilson_reports_uncertainty_even_for_twenty_passes():
    low, high = wilson(20, 20)
    assert .83 < low < .85 and high == 1
