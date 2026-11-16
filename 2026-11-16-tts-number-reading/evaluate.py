"""Score results/transcripts.jsonl and draw the chart.

An item passes when every one of its facts is heard (see items.py). Both sides go through Whisper's English
normaliser, then all spaces are removed, so "B A 2490" and "BA2490" match. Writes results/summary.json and
media/categories.png.

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
CONDITIONS = {"zonos3-norm-on": "ZONOS3-Mini, normaliser on (default)",
              "zonos3-norm-off": "ZONOS3-Mini, normaliser off",
              "macos-say": "macOS say (Daniel)"}
norm = EnglishTextNormalizer()


def squash(text):
    return norm(text).replace(" ", "")


def score(row):
    category, text, facts = ITEMS[row["no"]]
    heard = squash(row["heard"])
    missed = [f[0] for f in facts if not any(squash(form) in heard for form in f)]
    return {**row, "category": category, "text": text, "passed": not missed, "missed": missed}


def main():
    rows = [score(json.loads(line)) for line in (HERE / "results" / "transcripts.jsonl").open()]
    by = defaultdict(list)
    for r in rows:
        by[r["condition"]].append(r["passed"])
        by[(r["condition"], r["category"])].append(r["passed"])
    categories = list(dict.fromkeys(c for c, _, _ in ITEMS))
    summary = {
        "setup": "36 items x 3 seeds for each ZONOS3-Mini condition (n=108), 36 items once for macOS say (n=36); "
                 "BritishFemale stock voice, en_gb, backbone-ptq.gguf + zac-keep2 decoder on the MLX server; "
                 "transcribed with mlx-community/whisper-large-v3-turbo, temperature 0",
        "overall": {c: {"passed": sum(by[c]), "n": len(by[c])} for c in CONDITIONS},
        # under 1 s of audio for a whole sentence: the model stopped almost at once (Whisper then tends to hear
        # "Thank you.")
        "early_stop": {c: sum(r["seconds"] < 1 for r in rows if r["condition"] == c) for c in CONDITIONS},
        "by_category": {c: {k: {"passed": sum(by[(c, k)]), "n": len(by[(c, k)])} for k in categories}
                        for c in CONDITIONS},
        "failures": [{k: r[k] for k in ("no", "condition", "seed", "text", "heard", "missed")}
                     for r in rows if not r["passed"]],
    }
    (HERE / "results" / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))

    fig, ax = plt.subplots(figsize=(10, 5.8))
    width = 0.27
    colours = {"zonos3-norm-on": "#2a6f97", "zonos3-norm-off": "#a9c5d9", "macos-say": "#999999"}
    for i, c in enumerate(CONDITIONS):
        share = [100 * sum(by[(c, k)]) / len(by[(c, k)]) for k in categories]
        o = summary["overall"][c]
        ax.bar([x + (i - 1) * width for x in range(len(categories))], share, width, color=colours[c],
               label=f"{CONDITIONS[c]}: {o['passed']}/{o['n']}")
    ax.set_xticks(range(len(categories)), categories, rotation=20, ha="right")
    ax.set_ylabel("items read correctly (%)")
    ax.set_ylim(0, 105)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=9)
    ax.set_title("Does the TTS say the number right? Round trip through Whisper\n"
                 "our small test: 4 sentences per category; ZONOS3 n=12 per bar (3 seeds), say n=4", fontsize=11)
    fig.tight_layout()
    fig.savefig(HERE / "media" / "categories.png", dpi=160)
    for c in CONDITIONS:
        print(c, summary["overall"][c])


if __name__ == "__main__":
    main()
