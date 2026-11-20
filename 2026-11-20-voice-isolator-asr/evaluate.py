"""Score results/transcripts.jsonl and draw the chart.

- written: the 19 Nov rule. A sentence passes only if every fact appears in a form a person would type ("£45",
  "07:45", "QX7-42B") in the raw transcript, lowercased, with spaces, thousands commas and full stops (not decimal
  points) removed. Written forms: items.py plus OVERRIDES below (copied from the 19 Nov experiment).
- word error rate: jiwer over the whole set, after Whisper's English normaliser on both sides.
- fixed / broken: the same clip with and without isolation, so a sentence that passes only after isolation is
  "fixed" and one that passes only before it is "broken".

Writes results/summary.json and media/isolation.png.

    uv run evaluate.py
"""
import json
import re
from collections import defaultdict
from pathlib import Path

import jiwer
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from whisper_normalizer.english import EnglishTextNormalizer

from items import ITEMS

HERE = Path(__file__).parent
NOISES = {"clean": "clean speech", "white-5db": "white noise, 5 dB SNR", "babble-0db": "4-voice babble, 0 dB SNR"}
NUMBER_WORDS = re.compile(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|twelve|fifteen|eighteen|twenty|"
                          r"thirty|forty|fifty|sixty|hundred|thousand|million|billion|point|quarter|half|o'clock)\b")
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
norm = EnglishTextNormalizer()


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
    raw = flat(row["heard"])
    missed = [f[0] for f in written_forms(row["no"]) if not any(flat(form) in raw for form in f)]
    return {**row, "text": ITEMS[row["no"]][1], "written": not missed, "missed_written": missed}


def wer(rows):
    return round(jiwer.wer([norm(r["text"]) for r in rows], [norm(r["heard"]) or "-" for r in rows]), 4)


def main():
    rows = [score(json.loads(line)) for line in (HERE / "results" / "transcripts.jsonl").open()]
    by = defaultdict(list)
    for r in rows:
        by[(r["noise"], r["isolated"])].append(r)
    pairs = defaultdict(dict)
    for r in rows:
        pairs[(r["noise"], r["voice"], r["no"])][r["isolated"]] = r
    timing = [json.loads(line) for line in (HERE / "results" / "isolation_seconds.jsonl").open()]
    summary = {
        "setup": "36 sentences x 3 macOS say voices (Daniel en_GB, Samantha en_US, Karen en_AU) = 108 clips at 48 kHz, "
                 "each clean, with white noise at 5 dB SNR and with 4-voice synthetic babble at 0 dB SNR; each clip "
                 "transcribed as is and after inworld/voice-isolator (offline model, inworld-voice-isolation 1.0.0, "
                 "torch 2.15.0 on MPS, fp32); Whisper large-v3-turbo via mlx-whisper 0.4.3, temperature 0; "
                 "one MacBook (Apple M2), one run each",
        "written": {n: {("isolated" if i else "as_is"): {"passed": sum(r["written"] for r in by[(n, i)]),
                                                         "n": len(by[(n, i)])} for i in (False, True)} for n in NOISES},
        "wer": {n: {("isolated" if i else "as_is"): wer(by[(n, i)]) for i in (False, True)} for n in NOISES},
        "fixed_broken": {n: {"fixed": sum(p[True]["written"] and not p[False]["written"]
                                          for k, p in pairs.items() if k[0] == n),
                             "broken": sum(p[False]["written"] and not p[True]["written"]
                                           for k, p in pairs.items() if k[0] == n)} for n in NOISES},
        "isolation_realtime_factor": round(sum(t["seconds"] for t in timing) / sum(t["audio_seconds"] for t in timing), 3),
        "changed_by_isolation": [{"noise": k[0], "voice": k[1], "text": p[False]["text"], "as_is": p[False]["heard"],
                                  "isolated": p[True]["heard"], "written_as_is": p[False]["written"],
                                  "written_isolated": p[True]["written"]}
                                 for k, p in pairs.items() if p[False]["written"] != p[True]["written"]],
    }
    (HERE / "results" / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))

    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 5.2))
    width = 0.36
    for i, (iso, colour, label) in enumerate([(False, "#999999", "as recorded"),
                                              (True, "#2a6f97", "after Voice Isolator")]):
        key = "isolated" if iso else "as_is"
        xs = [x + (i - 0.5) * width for x in range(len(NOISES))]
        written = [100 * summary["written"][n][key]["passed"] / summary["written"][n][key]["n"] for n in NOISES]
        errors = [100 * summary["wer"][n][key] for n in NOISES]
        left.bar(xs, written, width, color=colour, label=label)
        right.bar(xs, errors, width, color=colour, label=label)
        for x, v, n in zip(xs, written, NOISES):
            left.text(x, v + 1, f"{summary['written'][n][key]['passed']}/{summary['written'][n][key]['n']}",
                      ha="center", fontsize=8)
        for x, v in zip(xs, errors):
            right.text(x, v + 0.3, f"{v:.1f}", ha="center", fontsize=8)
    for ax, ylabel in ((left, "sentences with every number written right (%)"), (right, "word error rate (%), lower is better")):
        ax.set_xticks(range(len(NOISES)), [s.replace(", ", "\n") for s in NOISES.values()], fontsize=9)
        ax.set_ylabel(ylabel)
        ax.spines[["top", "right"]].set_visible(False)
    left.set_ylim(0, 110)
    fig.legend(*left.get_legend_handles_labels(), frameon=False, loc="lower center", ncol=2, fontsize=9)
    fig.suptitle("Does cleaning noisy speech first help Whisper write prices, dates and codes?\n"
                 "our small test: 36 sentences x 3 synthetic macOS voices, n=108 clips per bar, one run each",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(HERE / "media" / "isolation.png", dpi=160)
    print(json.dumps({k: summary[k] for k in ("written", "wer", "fixed_broken", "isolation_realtime_factor")}))


if __name__ == "__main__":
    main()
