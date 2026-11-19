# Post kit: does speech-to-text write the numbers right? (2026-11-19)

**The one finding:** in our small test, a new 0.5B open speech-to-text model (Reson8 Rumble-2-Flash) and Whisper
large-v3-turbo wrote prices, dates and codes about equally well: 96 vs 102 of 108 sentences on clean speech, 93 vs
88 in noise. The more useful result was why two sentences failed for everyone: the voice never said the "to" in
"chapters 3-7" or "3:1". In noise both models wrote "chapter 37". Turning the new model's digits off showed what
it heard: "chapters three seven", for all three voices.

**Everyday analogy for the pipeline step (for the writer):** it's like taking down a phone number someone reads
out. If they say "three seven" when they meant "three to seven", no note-taker can write the dash back in. The
mistake happened in the voice, not the ears. Switching the model to "write everything as words" is like asking the
note-taker to repeat back exactly what they heard.

**Facts and sources**
1. Rumble-2-Flash is an open speech-recognition model from Reson8 (Resonate Labs, Amsterdam): 0.5B parameters,
   45 languages, Apache 2.0, with a `digits` on/off switch. Its card was updated on 18 Nov 2026 with Open ASR
   Leaderboard v1.16.1 results (their figure: English average WER 6.60).
   Source: https://huggingface.co/Reson8/Rumble-2-Flash ; second source:
   https://artificialanalysis.ai/speech-to-text/models/reson8
2. Our small test: 36 made-up sentences × 3 macOS voices (British, American, Australian) = 108 clips, plus each
   with white noise at 5 dB. A sentence passes only if every value is written the way a person would type it
   (£45, 07:45, QX7-42B). Rumble-2-Flash 96/108 clean, 93/108 noisy; Whisper large-v3-turbo 102/108 clean,
   88/108 noisy. On one Apple M2 laptop: 0.23 s vs 1.2 s per clip, but on different runtimes (PyTorch vs MLX),
   so that is not a fair speed comparison.
   Source: results/summary.json in the repo folder below.
3. Specific misses: Rumble wrote "QX7 negative 42B" for a booking code (one voice, clean and noisy) and "1,5750"
   for 15,750 in noise; Whisper wrote "45 pounds" where Rumble wrote "£45". Both wrote "chapter 37" for "chapters
   3-7" in noise.
   Source: results/transcripts.jsonl in the repo folder below.

**Visual:** media/written.png (four bars per condition, with n in the title).

**Repo:** https://github.com/thisisshivamtiwari/ai-lab/tree/main/2026-11-19-asr-number-writing

**The honest limit:** synthetic voices, English only, one run each, white noise only. The differences between
the two models are 5–6 sentences out of 108, which is not enough to call either one better.

**Angle for the writer (facts only):** this closes the loop on the 16 and 17 Nov voice tests. A voice pipeline
has two number steps (saying and writing), and in our three tests the failures were in the hand-off between
them more than in either model. A practical habit: test the transcriber in "words" mode once, to hear what your
voice actually says, before grading it on digits.
