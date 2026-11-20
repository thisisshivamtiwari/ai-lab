# Post kit: does cleaning noisy speech first help speech-to-text? (2026-11-20)

**The one finding:** in our small test, putting Inworld's new open denoiser (Voice Isolator, 18 Nov) in front of
Whisper changed nothing on clean speech (107 of 108 transcripts identical), helped in a noisy crowd (sentences with
every number written right went from 67 to 76 of 108; word error rate 45% → 33%), and was a draw in white noise
(98 = 98). It wasn't free: in the crowd, 8 sentences that were right before isolation came out wrong after, a few
with a different number (180°C → "190 degrees", 2.4 GB → "2.0 GB").

**Everyday analogy for the pipeline step (for the writer):** it's like asking someone to close the door to a busy
corridor before you read out a phone number. Most of the time the listener gets it right more often. Now and then
the door also muffles a digit. A quieter room helps, but you still read the number back.

**Facts and sources**
1. Inworld Voice Isolator: open 48 kHz speech denoiser, Apache 2.0, offline model 64M parameters and realtime
   model 58M (20 ms look-ahead), released 18 Nov 2026. Inworld says it only denoises, on purpose, so it adds no
   bias to downstream speech-to-text. They publish no speech-to-text numbers.
   Source: https://inworld.ai/blog/introducing-voice-isolator ; second source:
   https://explainx.ai/blog/inworld-voice-isolator-open-apache-48khz-realtime-64m-parameters-2026
2. Our small test: 36 made-up sentences with prices, dates, times and codes × 3 macOS voices = 108 clips, each
   clean, with white noise (5 dB) and with a made-up crowd of 4 other synthetic voices (0 dB). Whisper
   large-v3-turbo on each clip as recorded and after isolation. Written right (every value typed the way a person
   would): clean 102 → 102, white noise 98 → 98, crowd 67 → 76. Word error rate: 10.9% → 10.9%, 12.3% → 14.2%,
   45.1% → 33.0%. One Apple M2, one run each.
   Source: results/summary.json in the repo folder below.
3. How it helped in the crowd: Whisper's inserted words almost halved (91 → 49). Before isolation it wrote down
   the crowd ("The site is 5269 Air Force in the United States" for "The year 1066 changed England"); after, the
   sentence. Isolation ran at about 0.7 s per second of audio on the laptop.
   Source: results/transcripts.jsonl in the repo folder below.

**Visual:** media/isolation.png (left: sentences written right; right: word error rate; n=108 per bar).

**Repo:** https://github.com/thisisshivamtiwari/ai-lab/tree/main/2026-11-20-voice-isolator-asr

**The honest limit:** synthetic voices and a synthetic crowd, English only, one transcriber, one run. The crowd
voices were each quieter than the speaker, which is the easy case for a model that keeps the loudest voice. +9 of
108 is a real-looking gap on this set, not a promise for real calls.

**Angle for the writer (facts only):** this is the fourth voice test this week (saying numbers, writing numbers,
now cleaning the audio first). The practical habit it suggests: clean the audio when the noise is other people
talking, skip it when the audio is already clean, and keep a read-back or check on any number the system acts on.
