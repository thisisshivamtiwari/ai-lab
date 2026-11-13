# Post kit: decision-calibration (ai-lab 2026-11-13)

Facts only. The writer turns this into a post in his voice.

## The one finding
Before you trust a model's yes/no probability to auto-approve anything, check its calibration. I asked Claude Haiku
4.5 and Claude Sonnet 5.5 the same yes/no question about 80 synthetic support messages, twice each, and they hedged
in different ways:

- **Sonnet** was under-confident. It gave 0.75 to 0.85 to messages that were clearly yes. With a 0.1/0.9 auto-decide
  band, it would send 28.1% of messages to a person; Haiku would send 12.5%.
- **Haiku** was more decisive but less stable. One message went from 0.80 to 0.15 between two identical runs.
- **Errors:** neither model had a wrong answer inside the auto-decide band.

This is the baseline for Google's new Gemini Decisions API, which claims calibrated probabilities. The harness is
ready, and the Gemini run is next once a key is added.

## 3 facts with sources
1. **Launch:** Google launched the Gemini Decisions API and the `gemini-decision-1` model on 11 Nov 2026. It covers
   yes/no, choice and rubric-score questions and returns probabilities. The post is titled "Fast, calibrated
   multimodal decisions". Source: https://blog.google/innovation-and-ai/technology/developers-tools/gemini-decisions-api/
2. **Pricing:** Google lists it at $0.10 per million input tokens, with output free, and a no-cost tier in AI Studio
   for prototyping. Same source as above. Check current pricing before quoting it.
3. **Independent test:** Simon Willison tried one video with four yes/no questions and got scores such as 0.923 and
   0.050, where Jev and OpenAI's decision models return 1.0 or 0.0. He did not test calibration. Source:
   https://simonwillison.net/2026/Nov/11/gemini-decisions-api/

## Our numbers (label them "our small test")
Setup: 80 synthetic messages, 2 runs per model, verbalised probabilities via `claude -p`, ECE with 5 bins.

| Measure | Haiku 4.5 | Sonnet 5.5 |
|---|---|---|
| ECE, 2 runs pooled | 0.031 | 0.077 |
| Sent to a human (0.1–0.9 band) | 12.5% | 28.1% |
| Wrong inside the band | 0 of 140 | 0 of 115 |
| Accuracy at 0.5 | 97.5–98.8% | 97.5–98.8% |

## Visual
`media/reliability.png`: a reliability chart with both models, the diagonal and the human-review band shaded.

## Repo
https://github.com/thisisshivamtiwari/ai-lab/tree/main/2026-11-13-decision-calibration

## The honest limit
- **Gemini wasn't run.** There's no key yet, so the launch's own claim is untested.
- **Small, synthetic set.** 80 items, one labeller, and a 50% base rate. The middle bins hold 1 to 8 points.
- **Not a benchmark.** It doesn't show either model is "better". It shows why you measure calibration before choosing
  a threshold.
- **Context to keep out of the post:** no hotels, RBS, Retvens or client context.
