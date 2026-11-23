# Post kit: a free 0.8B "decision model" on a laptop, are its probabilities safe to act on? (2026-11-23)

**The one finding:** in our small test, Illuin's new open decision model Ivonnet-0.8B ran on a plain MacBook CPU (about
2 s per message) and gave smooth, perfectly repeatable probabilities. However, it got 67 of 80 synthetic support
messages right, against 157 of 160 for Claude Haiku 4.5 writing its own probability. Rewording the question flipped
10 of its 80 answers. With a "decide alone only above 0.9 or below 0.1" rule it stayed fairly safe (26 of the 27
it decided alone were right), but it sent two thirds of the messages to a person.

**Everyday analogy for the writer:** it's like a new hire who sorts the post by spotting words on the envelope.
Anything that says "refund" goes in the refunds tray, even "Can you explain what a chargeback is?". They are fast and
always sort the same envelope the same way. But if you change one word in the instruction you gave them, a tenth of
their piles change. So you let them handle only the envelopes they're sure about, and you write the instruction
down once and never tweak it casually.

**Facts and sources**
1. Illuin released two open (Apache 2.0) decision models on 23 Nov 2026: IVE-4B and Ivonnet-0.8B. Each returns a
   probability for every option of a multiple-choice or yes/no question in one forward pass, with no text generated.
   The card claims a 2.3% calibration error for Ivonnet on its benchmark.
   Source: https://huggingface.co/blog/QuentinJG/ive-release (card: https://huggingface.co/illuin/Ivonnet-0.8B);
   second source: https://123456.ai/en/ (open-source item, 23 Nov 2026).
2. Our small test: the same 80 synthetic messages and yes/no question ("is the customer asking for money back or
   contesting a charge?") as our 13 Nov experiment, 40 of them deliberately tricky, on one Apple M2 CPU.
   - Correct at 0.5: Ivonnet 67/80. On 13 Nov, Haiku 4.5 and Sonnet 5.5 each got 157/160 over 2 runs.
   - Calibration error: 0.093 for Ivonnet, against 0.031 (Haiku) and 0.077 (Sonnet).
   - Sent to a person by the 0.1–0.9 band: 66% for Ivonnet, against 12.5% and 28%.
   - 10 of Ivonnet's 13 misses were "no" messages containing money words, e.g. "I'd like to send money back to a
     friend who paid me by mistake" (0.91).

   Source: results/summary.json and the README table in the repo folder below.
3. Rewording the question ("Does this customer want money returned to them, or say a payment on their account is
   wrong?") moved Ivonnet's probability by 0.12 on average and up to 0.49. It flipped 10 answers, and correct answers
   fell to 59/80. Two identical runs gave bit-identical numbers. Source: same folder.

**Visual:** media/calibration-and-wording.png (left: calibration curves for all four runs; right: each message's
probability under the original question against the reworded one).

**Repo:** https://github.com/thisisshivamtiwari/ai-lab/tree/main/2026-11-23-local-decision-model

**The honest limit:** one task, 80 items written and labelled by one person, a 0.8B model against much larger chat
models, and two wordings. The bigger IVE-4B (9.1 GB) didn't fit this 8 GB Mac and is untested. This shows what a
free local model gives you on a task it never saw. It is not a ranking.

**Angle for the writer (facts only):** probability models make "act alone only when sure" rules easy to set. But the
question text becomes part of the model: freeze it, version it and test it like code. Also, a vendor's calibration
number is measured on their tasks; check it on 50–100 of your own before trusting a threshold.
