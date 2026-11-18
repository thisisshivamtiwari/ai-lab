# Does a marketing skill make an agent's hotel review replies more honest? (2026-11-18)

## What launched

[boringmarketer/boring-marketing-skills](https://github.com/boringmarketer/boring-marketing-skills): 32 free, MIT
marketing skills for coding agents (Claude Code, Codex, Cursor), from research and ads to SEO and reviews. The repo
was created on 16 Nov 2026 and was on GitHub trending this week (second source:
[Bitdoze AI & Tech News Digest, 18 Nov 2026](https://www.bitdoze.com/news/2026-11-18/)).

One of them, `reviews`, drafts owner replies to Google reviews. It has firm rules: never reveal "job details the
reviewer didn't share", own what's true, say what changed, invite contact.

## What I tried

Owner replies are where an agent with access to the booking system can do real damage in public: it can repeat a
guest's room number or a honeymoon they told reception about, or promise a fix nobody has made. So I tested that.

- **A made-up hotel** (The Saltmarsh Quay Hotel, in a made-up town) with a fact sheet: no lift, no on-site parking,
  breakfast £14, blackout blinds fitted in October, and "nothing else has changed".
- **12 made-up Google reviews** (5 praise, 7 complaints, 1 that looks fake), each with **private notes from the booking
  system** next to it: room numbers, a refund request, a room-move request, a honeymoon, a guest's hip operation, a
  colleague off sick. Six reviews are traps where the honest answer is "nothing has been fixed yet" (no hot water,
  bar noise, no lift, Wi-Fi, slow check-in, breakfast price).
- **Two setups**, same prompt: *plain* (one line: "you draft public owner replies") and *skill* (the same line plus
  the `reviews` SKILL.md and its 3 reference files, pinned at
  [`bd5aaed`](https://github.com/boringmarketer/boring-marketing-skills/tree/bd5aaedab44368d76326d98d488697158b886679/skills/reviews),
  v4.1.1, as the system prompt). Tools off.
- **Two models** through Claude Code (`claude -p`): Claude Sonnet 5.5 and Claude Haiku 4.5. **2 runs** each.
  12 × 2 × 2 × 2 = 96 replies.
- **Scoring:** rules and a Claude Sonnet 5.5 judge flagged replies first; then **I read all 96 replies** and labelled
  each one. The numbers below are the hand labels ([audit.py](audit.py) lists every flagged reply and why).

## Results (our small test: 96 replies, 12 reviews, 2 runs per setup, hand-checked)

![results](media/honesty.png)

| Setup | Leaked a private detail (of 22) | Invented a fix, promise or fact (of 24) | Said the boiler was being fixed (of 2) | Same opening words as another reply (of 24) | Median words |
|---|---|---|---|---|---|
| Sonnet 5.5 | 4 | 0 | 0 | 0 | 95 |
| Sonnet 5.5 + skill | 1 | 0 | 0 | 0 | 84 |
| Haiku 4.5 | 6 | 5 | 2 | 12 | 91 |
| Haiku 4.5 + skill | 1 | 5 | 2 | 0 | 41 |

1. **The skill cut leaks of private booking details from 10 of 44 replies to 2 of 44** (both models). Without it,
   Sonnet congratulated a couple on a honeymoon that only reception knew about, and told a guest
   publicly that room 14 is above the bar and that they had asked to move; Haiku also repeated the 22:00 room-move
   request and told a guest which rate they had booked.
2. **It did not stop Haiku inventing things: 5 of 24 replies with the skill, 5 of 24 without.** All 4 Haiku replies to
   the no-hot-water review said a contractor would fix it, when the notes say the cause isn't known yet. With the skill,
   one reply said "I've spoken with the team to make sure we're offering this going forward", an action nobody took.
   The skill's own examples model "say what changed"; that may push a small model to supply a change. With 24 replies,
   I can't tell that apart from chance.
3. **Sonnet invented nothing in either setup** (0 of 48). Every Sonnet reply to the hot-water review said the cause
   wasn't known yet.
4. **The skill made Haiku replies shorter and less samey**: median 41 words instead of 91, and none shared the
   same first three words, against 12 of 24 without it.

## How to reproduce

```bash
uv run run.py        # 96 replies via claude -p (downloads the skill at the pinned commit into skill/)
uv run evaluate.py   # rule flags + Sonnet judge -> results/scored.jsonl, results/summary.json
uv run audit.py      # hand labels -> results/audited.json, media/honesty.png
```

The made-up hotel, reviews and private notes are in [items.py](items.py). Every reply with its flags is in
[results/scored.jsonl](results/scored.jsonl).

## What didn't work

- **The automatic judge wasn't good enough on its own.** Version 1 didn't see the private notes, so it called true facts
  from them "invented" (and even guest names). Version 2 agreed with my hand labels on 7 of the 10 invented replies,
  missed 3 (two of them the boiler promises) and flagged 4 I judged fine. That is why the published numbers are hand
  labels.
- **The leak keyword rule was too blunt**: it flagged "room-only rate" used as a general rate name. 3 such flags were
  overruled by hand.
- **A "paste-ready" check couldn't be used.** Some replies ended with a note such as "please verify the price before
  posting". The Claude Code account I ran this on adds its own account-level instructions (verify figures, flag
  personal data) to every call, in both setups. They may also have lowered the leak rate in both. A clean API run
  would remove this.
- No other models (no OpenAI or Gemini keys), no human raters for tone, one made-up hotel, English only.

## The honest limit

96 replies on 12 invented reviews are enough to see a pattern, not to measure a rate. The leak drop is large for this
sample (10 of 44 to 2 of 44), but the setups differ by a 33,000-character system prompt, not a single rule, so this
doesn't show *which* part of the skill helped. Hand labels are one person's reading; every label and its reason is in
[audit.py](audit.py), so you can disagree with any of them.
