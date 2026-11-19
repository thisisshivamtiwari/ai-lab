"""Score results/transcripts.jsonl two ways and draw the chart.

- meaning: the 16 Nov rule, kept in summary.json only. Every fact in items.py must be heard in any of its forms,
  after Whisper's English normaliser with spaces removed, so "fourteen" and "14" both count. The normaliser also
  drops hyphens, so "chapter 37" passes for "3-7"; that is why the chart uses the written score.
- written: every fact must appear in a form a person would type (digits and symbols, see `written_forms`), in the
  raw transcript, lowercased, spaces, thousands commas and full stops (not decimal points) removed. Only scored for the
  digit-writing conditions; Rumble with digits off writes words on purpose.

Rumble with digits off is transcribed and kept in summary.json, but left out of the chart: most of its misses are
the normaliser not turning words like "dash" or "fifty pence" back into digits, so its score measures our scorer.

Writes results/summary.json and media/written.png (written score only).

    uv run evaluate.py
"""
import json
import re
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from whisper_normalizer.english import EnglishTextNormalizer

from items import ITEMS

HERE = Path(__file__).parent
CONDITIONS = {"rumble-digits-on": "Rumble-2-Flash (0.5B), digits on",
              "whisper-turbo": "Whisper large-v3-turbo (0.8B)",
              "rumble-digits-off": "Rumble-2-Flash, digits off"}
WRITING = ["rumble-digits-on", "whisper-turbo"]
AUDIOS = ["clean", "noisy"]
NUMBER_WORDS = re.compile(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|twelve|fifteen|eighteen|twenty|"
                          r"thirty|forty|fifty|sixty|hundred|thousand|million|billion|point|quarter|half|o'clock)\b")
# facts whose written forms aren't in items.py, or where items.py lists a spoken-only form
OVERRIDES = {
    4: [["14th of February", "February 14th", "14 February", "February 14", "14/02"], ["2027"]],
    10: [["18:00", "18.00", "1800", "6pm"], ["UK"]],
    16: [["QX7-42B", "QX742B"]],
    11: [["2h", "2 hours", "2 hrs"], ["15m", "15 minutes", "15 min"]],
    20: [["5 km", "5 kilometres", "5 kilometers"]],
    25: [["3-7", "3–7", "3 to 7"]],
    26: [["101-110", "101–110", "101 to 110"], ["1st floor", "first floor"]],
    29: [["API"], ["JSON"], ["HTTPS"]],
    30: [["ETA"], ["approx", "approximately"], ["10 min", "10 minutes"]],
}
# Rumble with digits off writes what the voice said: "chapters three seven", "a ratio of three, one" for every voice.
# No transcriber can put back a separator nobody spoke, so these two are also scored without them.
UNSPOKEN = {15, 25}
norm = EnglishTextNormalizer()


def squash(text):
    return norm(text).replace(" ", "")


def flat(text):
    text = re.sub(r"(?<=\d),(?=\d)", "", text.lower()).replace("a.m.", "am").replace("p.m.", "pm")
    return re.sub(r"\.(?!\d)", "", text).replace(" ", "")


def written_forms(no):
    if no in OVERRIDES:
        return OVERRIDES[no]
    facts = []
    for forms in ITEMS[no][2]:
        keep = [f for f in forms if not NUMBER_WORDS.search(f.lower()) and not re.fullmatch(r"([A-Z] )+[A-Z]", f)]
        facts.append(keep or forms)
    return facts


def score(row):
    category, text, facts = ITEMS[row["no"]]
    heard = squash(row["heard"])
    meaning = [f[0] for f in facts if not any(squash(form) in heard for form in f)]
    raw = flat(row["heard"])
    written = [f[0] for f in written_forms(row["no"]) if not any(flat(form) in raw for form in f)]
    return {**row, "category": category, "text": text, "meaning": not meaning, "written": not written,
            "missed_meaning": meaning, "missed_written": written}


def tally(rows, key):
    return {"passed": sum(r[key] for r in rows), "n": len(rows)}


def main():
    rows = [score(json.loads(line)) for line in (HERE / "results" / "transcripts.jsonl").open()]
    by = defaultdict(list)
    for r in rows:
        by[(r["condition"], r["audio"])].append(r)
    speed = {c: round(sum(r["seconds"] for r in rows if r["condition"] == c) / sum(r["condition"] == c for r in rows), 2)
             for c in CONDITIONS}
    summary = {
        "setup": "36 sentences x 3 macOS say voices (Daniel en_GB, Samantha en_US, Karen en_AU) = 108 clips, each "
                 "clean and with white noise at 5 dB SNR; Rumble-2-Flash via transformers 5.23.0 on MPS fp16, greedy; "
                 "Whisper via mlx-whisper 0.4.3, temperature 0; one MacBook (Apple silicon), one run each",
        "meaning": {c: {a: tally(by[(c, a)], "meaning") for a in AUDIOS} for c in CONDITIONS},
        "written": {c: {a: tally(by[(c, a)], "written") for a in AUDIOS} for c in WRITING},
        "written_without_unspoken": {c: {a: tally([r for r in by[(c, a)] if r["no"] not in UNSPOKEN], "written")
                                         for a in AUDIOS} for c in WRITING},
        "seconds_per_clip": speed,
        "written_failures": [{k: r[k] for k in ("condition", "audio", "voice", "text", "heard", "missed_written")}
                             for r in rows if r["condition"] in WRITING and not r["written"]],
        "meaning_failures_digits_off": [{k: r[k] for k in ("audio", "voice", "text", "heard", "missed_meaning")}
                                        for r in rows if r["condition"] == "rumble-digits-off" and not r["meaning"]],
    }
    (HERE / "results" / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))

    fig, ax = plt.subplots(figsize=(9, 5.4))
    bars = [(kind, c) for c in WRITING for kind in ("written", "written_without_unspoken")]
    colours = {"rumble-digits-on": "#2a6f97", "whisper-turbo": "#999999"}
    labels = {"written": "all 36 sentences", "written_without_unspoken": "without the 2 the voice didn't say"}
    width = 0.2
    for i, (kind, c) in enumerate(bars):
        values = [100 * summary[kind][c][a]["passed"] / summary[kind][c][a]["n"] for a in AUDIOS]
        xs = [x + (i - 1.5) * width for x in range(len(AUDIOS))]
        ax.bar(xs, values, width, color=colours[c], hatch="//" if kind != "written" else None, edgecolor="white",
               label=f"{CONDITIONS[c]}, {labels[kind]}")
        for x, v in zip(xs, values):
            ax.text(x, v + 1, f"{v:.0f}", ha="center", fontsize=8)
    ax.set_xticks(range(len(AUDIOS)), ["clean speech", "white noise, 5 dB SNR"])
    ax.set_ylabel("sentences with every number written right (%)")
    ax.set_ylim(0, 110)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=8.5)
    ax.set_title("Prices, dates, times and codes: does speech-to-text get them right?\n"
                 "our small test: 36 sentences x 3 synthetic macOS voices; n=108 per plain bar, n=102 hatched\n"
                 "right = written the way a person would type it (£45, 07:45, QX7-42B)", fontsize=10)
    fig.tight_layout()
    fig.savefig(HERE / "media" / "written.png", dpi=160)
    print(json.dumps({k: summary[k] for k in ("meaning", "written", "written_without_unspoken", "seconds_per_clip")}))


if __name__ == "__main__":
    main()
