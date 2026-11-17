# Post kit: a 4.5M-parameter voice model on the price-and-date test (2026-11-17)

**The one finding:** in our small test, tiny-voca, a new open text-to-speech model with only 4.5M parameters
(18 MB, runs on a laptop CPU), got every amount, date and code right in 34 of 36 tricky sentences with each of its
two voices. Both misses came from the rules that write numbers out as words before the model speaks ("2h 15m"
became "two hours fifteen meters"), the same two sentences that tripped a model 20 times bigger the night before.

**Everyday analogy for the pipeline step (for the writer):** it's like writing a cheque. The amount is spelled out
in words before anyone reads it aloud; if the words are wrong, even a perfect reader says the wrong amount. The
"text front end" is that spelled-out line, and it decided the result here, not the size of the voice model.

**Facts and sources**
1. tiny-voca was released on 14 Nov 2026 by Muhammed Nazeem: an English TTS model with two voices and 4,537,291
   parameters, trained from scratch on about 18 hours of synthetic speech, Apache 2.0, runs on CPU or in the browser.
   Source: https://huggingface.co/n4ze3m/tiny-voca and https://github.com/n4ze3m/tiny-voca ;
   second source: https://digg.com/ai/z4bnw15r
2. Our small test: the same 36 made-up sentences (prices, dates, times, codes, units) as our 16 Nov ZONOS3-Mini
   test, each spoken once per voice (the output is identical every run), transcribed by Whisper large-v3-turbo; an
   item passes only if every key value comes back. tiny-voca 34/36 for each voice; on the same items ZONOS3-Mini
   (800M total / 100M active) got 93/108 over 3 seeds, macOS say 33/36.
   Source: results/summary.json in the repo folder below.
3. Both tiny-voca misses are visible in the front end's own text output, before any audio: "Tue 9 Feb" stays
   "tue" (Whisper heard "2"), "2h 15m" becomes "fifteen meters". On our Apple M2 it made 108.5 s of audio in 2.4 s
   on 4 CPU threads (about 45 times real time).
   Source: results/words.json and results/speed.json in the repo folder below.

**Visual:** media/overall.png (one bar per setup, with n next to each). Audio: media/00-tiny-voca-F2.mp3 (the
£1,249.50 invoice sentence) and media/11-tiny-voca-F2.mp3 ("2h 15m" read as "fifteen meters").

**Repo:** https://github.com/thisisshivamtiwari/ai-lab/tree/main/2026-11-17-tts-tiny-voca

**The honest limit:** 36 sentences, English only, the "listener" is Whisper, not people, so these are upper
bounds. The gap to ZONOS3-Mini is about 2 items and the two runs used different runtimes, so this does not say
tiny-voca is the better voice; it sounds clearly synthetic. It says the number step matters more than model size.

**Angle for the writer (facts only):** voice agents don't need a big model to say numbers right; they need a
number rulebook they have tested. That rulebook is text in, text out, so you can check your own prices, booking
codes and "2h 15m"-style shorthand in milliseconds before you generate a second of audio.
