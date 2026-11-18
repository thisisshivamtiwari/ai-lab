# Post kit: a free marketing skill vs an AI agent replying to hotel reviews (2026-11-18)

**The one finding:** in our small test, Claude drafted owner replies to 12 made-up hotel reviews with private booking
notes beside each one. Without the new free `reviews` skill, 10 of 44 replies told the public something only the
booking system knew (a honeymoon, a room number, a room-move request). With the skill, 2 of 44. But the skill did
not stop the smaller model promising fixes that hadn't happened: 5 of 24 replies with it, 5 of 24 without.

**Everyday analogy for the writer:** it's like giving a new receptionist the guest file while they answer a complaint
at the front desk, in front of a queue. A written house rule ("never say what's in the file") stopped most of the
oversharing. It didn't stop the junior one saying "the engineer's coming to fix it" when nobody knows what's wrong.

**Facts and sources**
1. boringmarketer/boring-marketing-skills: 32 free, MIT-licensed marketing skills for AI coding agents (copy, SEO,
   ads, reviews, a local-business pack), repo created 16 Nov 2026, trending on GitHub this week.
   Source: https://github.com/boringmarketer/boring-marketing-skills ; second source:
   https://www.bitdoze.com/news/2026-11-18/
2. Our small test: 12 made-up reviews of a made-up hotel, Claude Sonnet 5.5 and Claude Haiku 4.5, with and without the
   `reviews` skill, 2 runs each = 96 replies, every reply read and labelled by hand. Leaked a private booking detail:
   Sonnet 4/22 → 1/22 with the skill, Haiku 6/22 → 1/22. Invented a fix, promise or hotel fact: Sonnet 0/24 both ways,
   Haiku 5/24 both ways.
   Source: results/audited.json and audit.py in the repo folder below.
3. On the review about two mornings without hot water (the notes say the cause isn't known yet), all 4 Haiku replies
   said a contractor would fix or repair it; all 4 Sonnet replies said the cause wasn't known yet.
   Source: results/scored.jsonl (review R03) in the repo folder below.

**Visual:** media/honesty.png (two bar panels, hand-checked counts printed on every bar).

**Repo:** https://github.com/thisisshivamtiwari/ai-lab/tree/main/2026-11-18-review-reply-skill

**The honest limit:** 96 replies on one invented hotel show a pattern, not a rate. The skill is a 33,000-character
prompt, so this can't say which rule did the work. A Claude Code account adds its own instructions to every call
(in both setups), which may have lowered leaks in both. The labels are one person's reading, all listed in the repo.

**Angle for the writer (facts only):** for anyone letting an AI answer reviews: a written rulebook helped with privacy,
and the bigger model was the one that didn't make promises. Keep the booking notes away from the reply-writer, or
read every reply that mentions a fix before it goes live.
