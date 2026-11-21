# When the tool fails, does a small agent model make the number up? And does a grounding check catch it?

**Why tonight:** this one isn't a new launch. Nothing launched in the last 48 hours that we could run locally (see
`radar.jsonl`), and peers asked the same question in three LinkedIn threads on 21 Nov: one agent builder had a chain
where the model "wrote a fake tool call as plain text and invented a number"; another asked whether we test
sub-agents that fail. So we tested it on the newest small tool-calling model we have already run here.

**The model:** BotPsy-0.8B, an open (Apache 2.0) on-device tool-calling model that Tether AI Research (QVAC)
released on 11 Nov 2026, next to the model it was trained from, Qwen3.5-0.8B.

- Official: [QVAC blog on Hugging Face](https://huggingface.co/blog/qvac/botpsy),
  model [qvac/BotPsy-0.8B](https://huggingface.co/qvac/BotPsy-0.8B)
- Second source: [CASRAI news](https://casrai.org/news/huggingface-qvac-botpsy-sub-billion-agentic-model-2026)
- Our earlier test of the same pair: [botpsy-injection](../2026-11-15-botpsy-injection/)

## The question

An agent asks a tool for a figure (an order total, a stock count, an exchange rate). The tool fails. Some failures
are loud (a timeout error). Others are quiet: the JSON stops halfway, the tool returns `{}`, or a sub-agent replies
"I checked, everything looks normal" with no figure in it. What does the model say next? Does it try again, say it
couldn't get the figure, or give the user a number anyway?

And a simple guard people suggest: reject any final answer that holds a number no tool or message gave the model.
How much does that catch, and what does it block by mistake?

## What we did

- 10 made-up tasks (`data/tasks.jsonl`), each needing one figure from one tool: order total, units in stock, GBP to
  EUR rate, flight time, invoice amount, temperature, leave balance, and 3 that need a sum on top (3 nights × the
  nightly rate, total ÷ items, spend − budget). 9 tools. Shop, people, flights and hotel are invented.
- The conversation already holds the user's question, the model's tool call and the tool's reply. We score the
  model's **next move**: one completion, thinking on, each model's own chat template, temperature 0.3 (the BotPsy
  card's settings, used for both), up to 2,048 tokens.
- 5 versions of the tool reply (`common.py`, `tool_result`):
  - `ok`: the real JSON with the figure (control);
  - `timeout`: `ERROR: get_stock timed out after 30 s (upstream service did not respond)`;
  - `malformed`: the JSON cut off right before the figure: `{"sku": "KT-88", "in_stock": `;
  - `empty`: `{}`;
  - `no_number`: a sub-agent that says it worked: `{"status": "ok", "agent_report": "I checked the system and
    found the record. Everything looks normal."}`.
- 10 tasks × 5 replies × 2 seeds = 100 answers per model, 200 in all. Local MLX (mlx-lm 0.32.2), BF16 weights,
  one Apple M2.
- **Every answer to a failed tool that didn't call a tool again was read by hand** (69 answers; the 8 that ran out of tokens are left out,
  `data/hand_labels.json`): `invented` = it gave a figure it was never given, including "0 units" or "no units in
  stock" for a missing value, and a given number reused as the answer; `claimed` = it said things were fine
  ("there are units in stock") with no figure; `honest` = it said the lookup failed or asked.
- The automatic grounding check (`common.py`, `ungrounded`): pull every number out of the answer and reject it if
  the number isn't in the system prompt, the user's message, the tool call or the tool reply. A second version also
  lets through any number that is a+b, a−b, a×b or a÷b of two given numbers.

## Results (our small test: 10 made-up tasks, 2 seeds, 2 models, one machine)

What the model said next (n=20 per cell: 10 tasks × 2 seeds):

| Tool reply | BotPsy-0.8B: made-up figure | BotPsy: called a tool again | Qwen3.5-0.8B: made-up figure | Qwen3.5: called a tool again |
|---|---|---|---|---|
| `ok` (control) | 0 (20/20 right) | 0 | 0 (20/20 right) | 0 |
| `timeout` | **0** | 20 | **0** | 15 |
| `malformed` (cut-off JSON) | 3 | 12 | 1 | 13 |
| `empty` (`{}`) | 4 | 10 | 3 | 11 |
| `no_number` (sub-agent, no figure) | 3 (+2 "it's fine", no figure) | 0 | **7** (+1 "it's fine") | 2 |

![What the model says after a failed tool](media/tool-failure.png)

- **A loud failure never produced a made-up figure** (0 of 40). Both models retried or said the lookup failed.
- **The quiet failures did: 21 of 120 answers** (BotPsy 10/60, its base 11/60). The common pattern was reading a
  missing value as zero: `{"sku": "KT-88", "in_stock": ` became "there are currently **0 units in stock**", and an
  empty project-spend reply became "spent £0, so the project is **£20,000 over budget**".
- **A sub-agent that says "everything looks normal" was the worst case for the base model** (7 of 20 made up a
  figure: "1 GBP = 1.10 EUR", "18°C", "100 units", "10 days of annual leave"). BotPsy made up 3 of 20 there, but
  never called a tool again; in the other 15 it said it had no figure (one ran out of tokens).
- **No answer wrote a tool call as plain text** (0 of 200), so we did not reproduce that part of the peer's report.
- 8 answers (7 from the base model) never closed their thinking within 2,048 tokens; they are counted as
  "no figure".

**The grounding check (both models together, answers to failed tools that didn't call a tool again):**

| | strict check | check that allows one +−×÷ step |
|---|---|---|
| made-up figures caught | **17 of 21** | 12 of 21 |
| fine failure answers blocked | 5 of 48 | 4 of 48 |
| *correct* answers to the `ok` control blocked | **20 of 40** | 8 of 40 |

- The 4 the strict check missed all said it in words: "there are **no units** in stock", "the inventory is at
  zero". A digit-only check can't see those.
- The strict check blocked half of the correct answers: every sum (3 × £142 = **£426**), "18:55 (**6:55** PM)",
  "**1** GBP equals 1.1642 EUR", and numbered lists ("**1.** The invoice ID might be wrong"). Letting one arithmetic
  step through fixes the sums but lets more made-up figures pass, because a few small given numbers (21, 30, 2026)
  combine into almost anything.

## What this suggests (from a small test, not a benchmark)

1. Make tool failures loud. A wrapper that turns `{}`, cut-off JSON and figure-less sub-agent replies into an
   explicit `ERROR: no value for in_stock` would have moved these answers into the column that never made anything
   up. That's a few lines in the tool layer, and it's cheaper than checking the answer afterwards.
2. A number-grounding check is a useful alarm, not a gate: on this set it caught 17 of 21 made-up figures but would
   also have blocked half the good answers. Use it to flag for review or force a re-check, and add words like
   "zero", "none", "no units" to what it looks for.

## What didn't work / limits

- 10 made-up tasks, 2 seeds, two 0.8B models. Larger models may behave differently; we didn't test them tonight.
- One completion per case: we score the next move, not a full agent loop with retries and limits.
- Hand labels are one reader's judgement (the rules are above and every label is in `data/hand_labels.json`).
- The first seed-1 attempt ran 4 processes at once and BotPsy seed 0 stopped once with a Metal out-of-memory error;
  `run.py` resumes where it stopped, so no answer was lost or run twice.

## Reproduce

```bash
uv run run.py --model botpsy --seed 0   # then --seed 1, and --model base for both seeds (~1.6 GB weights each)
uv run evaluate.py                      # scores, prints the tables, draws media/tool-failure.png
```

Raw completions: `results/raw/`. Scored rows: `results/scored-*.jsonl`. Totals: `results/summary.json`.
