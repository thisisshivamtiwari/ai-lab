"""Score tiny-voca's transcripts next to the 16 Nov run's and draw the chart.

Same items, same Whisper model and the same scoring as ../2026-11-16-tts-number-reading: an item passes when every
one of its facts is heard (see items.py); both sides go through Whisper's English normaliser with spaces removed.
The ZONOS3-Mini and macOS say transcripts are read from that folder, not re-run. Writes results/summary.json and
media/overall.png.

    uv run evaluate.py
"""
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from whisper_normalizer.english import EnglishTextNormalizer

from items import ITEMS

HERE = Path(__file__).parent
EARLIER = HERE.parent / "2026-11-16-tts-number-reading" / "results" / "transcripts.jsonl"
# label, size note, runs per item
CONDITIONS = {"tiny-voca-F2": ("tiny-voca, voice F2", "4.5M params, CPU", 1),
              "tiny-voca-M2": ("tiny-voca, voice M2", "4.5M params, CPU", 1),
              "zonos3-norm-on": ("ZONOS3-Mini, normaliser on", "800M total / 100M active", 3),
              "zonos3-norm-off": ("ZONOS3-Mini, normaliser off", "800M total / 100M active", 3),
              "macos-say": ("macOS say (Daniel)", "rule-based, built in", 1)}
norm = EnglishTextNormalizer()


def squash(text):
    return norm(text).replace(" ", "")


def score(row):
    category, text, facts = ITEMS[row["no"]]
    heard = squash(row["heard"])
    missed = [f[0] for f in facts if not any(squash(form) in heard for form in f)]
    return {**row, "category": category, "text": text, "passed": not missed, "missed": missed}


def main():
    lines = list((HERE / "results" / "transcripts.jsonl").open()) + list(EARLIER.open())
    rows = [score(json.loads(line)) for line in lines]
    by = defaultdict(list)
    for r in rows:
        by[r["condition"]].append(r["passed"])
        by[(r["condition"], r["category"])].append(r["passed"])
    categories = list(dict.fromkeys(c for c, _, _ in ITEMS))
    summary = {
        "setup": "36 items; tiny-voca once per voice (deterministic, n=36 each) on CPU with its dizione front end; "
                 "ZONOS3-Mini 3 seeds (n=108) and macOS say once (n=36) from the 16 Nov run; all transcribed with "
                 "mlx-community/whisper-large-v3-turbo, temperature 0",
        "overall": {c: {"passed": sum(by[c]), "n": len(by[c])} for c in CONDITIONS},
        "by_category": {c: {k: {"passed": sum(by[(c, k)]), "n": len(by[(c, k)])} for k in categories}
                        for c in CONDITIONS},
        "failures": [{k: r[k] for k in ("no", "condition", "seed", "text", "heard", "missed")}
                     for r in rows if not r["passed"] and r["condition"].startswith("tiny-voca")],
    }
    (HERE / "results" / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))

    fig, ax = plt.subplots(figsize=(9, 4.2))
    names = list(CONDITIONS)[::-1]
    share = [100 * sum(by[c]) / len(by[c]) for c in names]
    colours = ["#2a6f97" if c.startswith("tiny-voca") else "#b8c4cc" for c in names]
    ax.barh(range(len(names)), share, height=0.6, color=colours)
    for y, c in enumerate(names):
        o = summary["overall"][c]
        ax.text(share[y] + 1, y, f"{o['passed']}/{o['n']}", va="center", fontsize=10, color="#333333")
    ax.set_yticks(range(len(names)),
                  [f"{CONDITIONS[c][0]}\n{CONDITIONS[c][1]}" for c in names], fontsize=9)
    ax.set_xlim(0, 110)
    ax.set_xlabel("items where every number, date and code came back right (%)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Same 36 tricky sentences, round trip through Whisper (our small test)\n"
                 "tiny-voca: once per voice; ZONOS3-Mini: 3 seeds; say: once", fontsize=11)
    fig.tight_layout()
    fig.savefig(HERE / "media" / "overall.png", dpi=160)
    for c in CONDITIONS:
        print(c, summary["overall"][c], {k: v["passed"] for k, v in summary["by_category"][c].items()})
    for f in summary["failures"]:
        print(f"{f['no']:02d} {f['condition']}: {f['text']} -> {f['heard']}  missed {f['missed']}")


if __name__ == "__main__":
    main()
