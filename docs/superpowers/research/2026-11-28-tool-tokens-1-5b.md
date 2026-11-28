# Adding tool calling to a 1.5B model through new tokens

Running record of the work in the [plan](../plans/2026-11-28-r1d-tool-tokens.md). Updated at each step.

## What is measured

- DeepSeek-R1-Distill-Qwen-1.5B has no tool calling. Its chat template writes DeepSeek's tool markers
  (`<｜tool▁calls▁begin｜>` and eight more), but its tokenizer has none of them: each marker splits into about
  11 ordinary tokens (checked with its own `tokenizer.json`, and with llama.cpp's `/tokenize` on the
  original GGUF).
- Its embedding table and its language-model head are separate (`tie_word_embeddings: false`), both
  151,936 x 1,536, while the tokenizer uses IDs up to 151,664: 271 rows are spare.
- `learn/finetune/r1d/add_tokens.py` adds the nine markers as special tokens at IDs 151665-151673, sets each
  new embedding and head row to the mean of the rows of its old pieces, and leaves every other row as it was.
  Proven by 14 tests (`learn/finetune/r1d/tests/`) and by llama.cpp reading each marker as one token in the
  converted GGUF, with every old special token at its old ID.
- `learn/finetune/r1d/deepseek_tools.jinja` is the chat template: llama.cpp's DeepSeek R1 tool template with
  three fixes (a turn with text keeps its calls; string arguments are not JSON-encoded twice; each run of tool
  results opens its own block). All four template tests fail on the stock template and pass on ours.

## A bug the tests caught

The first build looked right in the plain tokenizer but broke in the GGUF: end-of-sentence landed on a tool
marker, and `<think>` and the other specials moved. The original `tokenizer_config.json` has no
`added_tokens_decoder`; the surgery created one holding only the nine new tokens. With `config.json` present,
transformers loads its Qwen2 tokenizer, which rebuilds the special tokens from that section when it exists, so
a partial list re-laid all of them; the GGUF converter reads the vocabulary through transformers and copied
the result. The fix lists every added token in that section. The test that now guards it loads the tokenizer
from a folder holding the real `config.json`; it was shown red with the old code (151653 where 151643 was
expected) before the fix.

## What is conjecture

- That starting each new row at the mean of its old pieces trains faster than a random start. Untested.
- That LoRA plus the nine new rows, with every old row frozen, can teach the format from a few thousand
  examples drawn from Mellum's and Tsunami's passing runs, and leave plain answers unchanged.
- That n-gram speculative decoding (`--spec-type ngram-mod`) speeds up agent turns noticeably, because edits
  and tool arguments repeat text already in the context. llama.cpp checks every draft token, so outputs
  should not change; to be confirmed side by side.

## Next

1. Build the supervised set in the DeepSeek tool format, committed with a SOURCE.md.
2. Train LoRA plus the new rows; record a MANIFEST.
3. Measure before and after: marker emission where a call belongs, parsed tool calls from llama-server, the
   Easy screen, and plain prompts.
4. Measure n-gram speculation speed and output match: the baseline.
5. Train our own draft head on the trained 1.5B and test it against n-gram on the same agent turns.

## Log

- 2026-11-28: Mellum switch-training timing test (8 examples, LoRA on 16 layers, 6-bit base): one update at
  20.5 GB in 0.5 min, the next at 92 GB peak (swapping on a 48 GB Mac) and 15 min. A long example does not fit
  Mellum in one pass; the earlier Mellum tunes used 2,048-token chunks. Mellum's switch set is capped at 8,192
  tokens (most off-mode examples fit; median about 4,000) and re-timed before the real run. Its marker rate was
  already 5/5 at step 0: Mellum calls tools after an empty think block on single steps, it fails over whole runs,
  so Mellum's switch is judged on harness runs with `--thinking off`, not on the marker rate.

- 2026-11-28: thinking switch added (ADR 0012). Two more tokens, `<｜think▁on｜>` and `<｜think▁off｜>`, at 151674
  and 151675; the template names the mode at the start of each generated turn, and `enable_thinking: false` (what
  Pi sends for `--thinking off`) gives an empty thinking block. The builder writes every teacher step in both
  modes. Rebuilt as `hf-tooltokens-v2`; llama.cpp reads all 11 new tokens as single tokens and switches mode
  from `chat_template_kwargs`. Mellum's own untrained switch was obeyed but looped without thinking (ADR 0012).

- 2026-11-28: supervised set `learn/finetune/r1d/data_sft_v1` built (736825b6): 3,208 train / 369 valid
  examples (held out by run), 25.4M tokens, one per assistant step of a passing phase, failed calls skipped.
  3,058 end in a tool call. Median 7,619 tokens, longest 19,577. Its SOURCE.md has the command and output.
  While building it, real payloads turned out to send some content as a list of text parts; the template
  now accepts both (test shown red first).

- 2026-11-28: where the completion tokens go in `data_sft_v1` (train): 1,575,265 in all, of which thinking is
  1,252,885 (80%). 3,160 tool calls. JSON arguments cost +17% over the raw values for `write`, +19% for `bash`,
  about 0 for `edit`; the call markers, `function` and the code fence are 9 fixed tokens per call (about 2% of
  completion tokens); the tools preamble plus system prompt is 1,397 tokens, once per conversation and cached.
  So the template is not where the tokens go; thinking is. Two levers follow: shorter thinking, and capping
  tool results in the harness the way the training prompts were capped (400 + 200 characters), which Pi does
  not do at inference. JSON escaping inside written code is a correctness risk for a small model; judge it on
  the faulty-call types after training before changing the format.
- 2026-11-28: the GPU was cleared for this work by stopping a Tsunami evaluation on the Python training-task
  suite after 2 of 9 tasks (0/6 passed; base scored 5/27 on the whole suite, mix120 2/27). It was a scorecard
  fill-in, not a held-out test, and Tsunami's training was already finished.

## What would falsify this / Risks

- After training, llama-server returns no parsed tool calls, or the Easy screen stays at its baseline: the
  tokens were added but not learned.
- Plain prompts change noticeably: freezing the old rows was not enough to protect the rest of the model.
- The supervised data is Mellum's thinking style; a 1.5B model may copy the format without the judgement.
- Mellum's traces run to 41,000 tokens; a 1.5B model may handle the context poorly whatever it learns.
