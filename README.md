# ai-lab

One small, honest experiment with each new AI launch: new models (Claude, Gemini, GPT, open weights), video, voice
and image models, agent SDKs and protocols, dev tools and papers.

Each folder is one night's work: what launched (with sources), what I tried, how to reproduce it, the result, and what
didn't work. Numbers here are small tests on my own machine, not benchmarks; the setup and sample size sit next to
every number.

## Experiments (newest first)

| Date | Experiment | Launch | What I found |
|---|---|---|---|
| 2026-11-16 | [tts-number-reading](2026-11-16-tts-number-reading/) | [Zyphra ZONOS3-Mini](https://huggingface.co/Zyphra/ZONOS3-Mini) | Can a new open 100M-active TTS model say £1,249.50, 07:45 and SW1A 1AA right? Round trip through Whisper on 36 made-up sentences: 93/108 with its text normaliser, 59/108 without (it said £1,449.50). Every miss with the normaliser on came from the normaliser ("Tue" → "Tew", "2h 15m" → "two H fifteen M"). macOS say 33/36 (one voice, 3 seeds, local MLX). |
| 2026-11-15 | [botpsy-injection](2026-11-15-botpsy-injection/) | [QVAC BotPsy-0.8B](https://huggingface.co/blog/qvac/botpsy) | A new 0.8B tool-calling model vs its base, with instructions hidden in tool results: a plain injected note hijacked BotPsy 4/30 vs 8/30 for the base, but a fake 'User:' turn hijacked both (20/30, 23/30). Neither warned once in 180 completions (10 synthetic tasks, benign canaries, 3 seeds, local MLX). |
| 2026-11-14 | [llmon-transfer](2026-11-14-llmon-transfer/) | [IBM LLMON + Granite 4.1 LLMON preview](https://huggingface.co/blog/ibm-granite/llmon-an-llm-native-markup-language-now-in-granite) | LLMON markup pasted into models never trained on it: a fake instruction block in the prompt's own syntax hijacked Sonnet 5.5 18/20 with XML tags, 1/20 with LLMON (10 synthetic tasks, benign canary, 2 runs). Haiku 4.5 obeyed 0. Granite run pending disk space. |
| 2026-11-13 | [decision-calibration](2026-11-13-decision-calibration/) | [Gemini Decisions API](https://blog.google/innovation-and-ai/technology/developers-tools/gemini-decisions-api/) | Harness + Claude baseline: on 80 synthetic support messages, Sonnet 5.5 hedged on true yeses (28.1% sent to a human vs 12.5% for Haiku 4.5); Haiku moved 0.80 → 0.15 on one message between runs. Gemini run pending a key. |
