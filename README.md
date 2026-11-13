# ai-lab

One small, honest experiment with each new AI launch: new models (Claude, Gemini, GPT, open weights), video, voice
and image models, agent SDKs and protocols, dev tools and papers.

Each folder is one night's work: what launched (with sources), what I tried, how to reproduce it, the result, and what
didn't work. Numbers here are small tests on my own machine, not benchmarks; the setup and sample size sit next to
every number.

## Experiments (newest first)

| Date | Experiment | Launch | What I found |
|---|---|---|---|
| 2026-11-13 | [decision-calibration](2026-11-13-decision-calibration/) | [Gemini Decisions API](https://blog.google/innovation-and-ai/technology/developers-tools/gemini-decisions-api/) | Harness + Claude baseline: on 80 synthetic support messages, Sonnet 5.5 hedged on true yeses (28.1% sent to a human vs 12.5% for Haiku 4.5); Haiku moved 0.80 → 0.15 on one message between runs. Gemini run pending a key. |
