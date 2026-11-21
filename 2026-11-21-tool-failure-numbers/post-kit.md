# Post kit: when the tool fails, does a small agent model make the number up? (2026-11-21)

**The one finding:** in our small test, a loud tool failure (a timeout error) never led to a made-up figure (0 of 40
answers), but quiet failures did: a cut-off JSON, an empty `{}`, or a sub-agent saying "everything looks normal"
with no figure led to a made-up figure in 21 of 120 answers. The usual pattern: a missing value read as zero ("0
units in stock"; "spent £0, so £20,000 over budget"). A simple "reject any number no tool gave you" check caught 17
of those 21, but also blocked 20 of 40 correct answers (every sum, "6:55 PM", "1 GBP = 1.1642 EUR").

**Everyday analogy for the writer:** it's like ringing the warehouse for a stock count. If nobody answers, you know
you don't have the number. If someone picks up and says "yep, all fine" and hangs up, it's easy to walk away
thinking the answer was "zero" or "plenty". The fix is making the warehouse say "I don't have that number".

**Facts and sources**
1. BotPsy-0.8B: open (Apache 2.0) on-device tool-calling model from Tether AI Research (QVAC), released 11 Nov 2026,
   built on Qwen3.5-0.8B. Source: https://huggingface.co/blog/qvac/botpsy ; second source:
   https://casrai.org/news/huggingface-qvac-botpsy-sub-billion-agentic-model-2026
2. Our small test: 10 made-up tasks (order total, stock count, exchange rate, flight time, three that need a sum)
   × 5 tool replies (real answer, timeout, cut-off JSON, `{}`, sub-agent with no figure) × 2 seeds × 2 models
   (BotPsy-0.8B and its base Qwen3.5-0.8B) = 200 answers, local MLX on one Apple M2. Every answer to a failed tool
   that didn't retry was read by hand (69). Made-up figures: timeout 0/40; cut-off JSON 4/40; `{}` 7/40;
   sub-agent with no figure 10/40 (base model 7/20, BotPsy 3/20). No answer wrote a tool call as plain text (0/200).
   Source: results/summary.json and data/hand_labels.json in the repo folder below.
3. The number-grounding check: caught 17 of 21 made-up figures; missed 4 written in words ("no units in stock");
   blocked 5 of 48 fine failure answers and 20 of 40 correct normal answers. Allowing one +−×÷ step: blocked 8 of
   40 correct answers but caught only 12 of 21. Source: same folder, README tables.

**Visual:** media/tool-failure.png (per failure type, what each model said next; n=20 per bar).

**Repo:** https://github.com/thisisshivamtiwari/ai-lab/tree/main/2026-11-21-tool-failure-numbers

**The honest limit:** 10 made-up tasks, 2 seeds, two 0.8B models, one completion per case (not a full agent loop);
hand labels are one reader's call. Bigger models may do better or worse; we didn't test them.

**Angle for the writer (facts only):** this answers questions peers asked in three of his 21 Nov comment threads (who
asked what is in team message T0088, not in this public repo). The practical habit: make every tool failure loud (turn `{}`, cut-off JSON and figure-less sub-agent replies into an explicit
error) and use a number check as an alarm, not a gate.
