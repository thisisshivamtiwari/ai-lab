# Post kit: does a new open TTS model read prices, dates and codes right? (2026-11-16)

**The one finding:** in our small test, Zyphra's new open ZONOS3-Mini voice model got the key value right in
93/108 sentences full of prices, dates, codes and units, but only 59/108 with its text normaliser turned off.
Every miss with the normaliser on traced back to the normaliser itself ("Tue" read as "Tew", "2h 15m" read as
"two H fifteen M", "approx." read as "a prox"), never to the voice. With it off, the model said £1,249.50 as
£1,449.50 or £1,049.50.

**Facts and sources**
1. Zyphra released ZONOS3-Mini on 9 Nov 2026: an open text-to-speech and voice-cloning model, a mixture of
   experts with 800M total and 100M active parameters, Apache 2.0, with runtimes for the browser (WebGPU),
   SGLang, ggml and Apple-silicon MLX. The model card lists 43 languages.
   Source: https://www.zyphra.com/our-work/zonos3-mini and https://huggingface.co/Zyphra/ZONOS3-Mini ;
   second source: https://aireiter.com/blog/zonos3-mini-review
2. Our small test: 36 made-up English sentences in 9 categories, ZONOS3-Mini run locally on a Mac (MLX server,
   one stock British voice, 3 seeds), each clip transcribed by Whisper large-v3-turbo; an item passes only if
   every key value (amount, date, code) comes back. Normaliser on: 93/108. Normaliser off: 59/108.
   macOS `say` baseline: 33/36.
   Source: results/summary.json in the repo folder below.
3. With the normaliser on, all 15 misses were the same 5 sentences on all 3 seeds, and the normaliser's own
   output shows why: "Tue 9 Feb" → "Tue the ninth of february", "2h 15m" → "two H fifteen M", "approx." left
   as is, "101–110" with no "to", "3-7" → "three-seven". It also reads "code 4417" as "four thousand four hundred
   and seventeen" and "18:00" as "eighteen o'clock", which Whisper still scores as right but no person would say.
   Source: results/normalised.json and README.md in the repo folder below.

**Visual:** media/categories.png (bars per category: normaliser on, normaliser off, macOS say; n=12 per ZONOS3
bar, n=4 per say bar). Audio pair for a video or carousel: media/invoice-normaliser-on.mp3 ("£1,249.50") and
media/invoice-normaliser-off.mp3 (heard as "£1,449.50").

**Repo:** https://github.com/thisisshivamtiwari/ai-lab/tree/main/2026-11-16-tts-number-reading

**The honest limit:** 36 sentences, English only, one voice, 3 seeds, and the "listener" is Whisper, not people.
Whisper can repair audio a person would mishear, so these are upper bounds. This says nothing about the model's
voice quality or how it compares with other open TTS models; `say` passing 33/36 doesn't make it better.

**Angle for the writer (facts only):** in a voice agent, the most dangerous words are numbers, and here they were
handled by a plain text-rewriting step before the model, not by the model. That step can be unit-tested without
generating any audio. Test it with your own prices, codes and abbreviations before you ship, and keep it on.
