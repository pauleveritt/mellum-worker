# Architecture decision records

One file per decision we want to be able to come back to: what we decided, why, what it costs, and the evidence.
A decision that changes gets a new record that supersedes the old one; the old one stays, marked superseded.

Format: `NNNN-short-title.md` with **Status**, **Context**, **Decision**, **Consequences**, **Evidence**.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-training-data-in-the-repo.md) | Training data is committed, sectioned under 45 MB, never rebuilt in place | Accepted |
| [0002](0002-on-policy-preference-pairs.md) | Preference pairs come from the model's own runs, judged by hidden tests | Accepted |
| [0003](0003-choosing-a-checkpoint.md) | Checkpoints are chosen on screens: Medium first, then faulty calls | Accepted |
| [0004](0004-publishing-a-tune.md) | Publish only after checks and a smoke test, private first, public on a clear win | Accepted |
| [0005](0005-new-tokens-in-spare-rows.md) | Teach a new format by adding real tokens in spare rows and training only those rows plus LoRA | Accepted |
| [0006](0006-deepseek-tool-format.md) | The 1.5B learns DeepSeek's tool markers, not Qwen's `<tool_call>` | Accepted |
| [0007](0007-speculative-decoding-baseline.md) | N-gram speculation is the baseline a trained draft head must beat | Accepted |
| [0008](0008-the-small-model-thesis.md) | The goal: prove a small model becomes powerful when fine-tuned and harnessed properly | Accepted |
| [0009](0009-small-model-pathologies-in-the-harness.md) | Small-model pathologies are removed by Pi extensions first, data second; train and serve the same shape | Accepted |
| [0010](0010-the-target-is-tool-calling.md) | The target is tool calling, added to a model that lacks it, by a method that works on any model | Accepted |
| [0011](0011-graders-match-whole-test-ids.md) | Graders match whole test ids; a parametrized test passes only when every case does | Accepted |
| [0012](0012-a-trained-thinking-switch.md) | Thinking on and off is a trained switch, a control token, not a template trick | Proposed |
| [0013](0013-mixture-of-experts-for-the-small-model.md) | A mixture-of-experts effect for the small model: options recorded, deferred | Deferred |
| [0014](0014-records-carry-prompt-tools-and-weights.md) | Run records carry the prompt, the tools and the weights the model was actually served | Accepted |
