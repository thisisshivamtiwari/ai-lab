"""Calibration report: Ivonnet-0.8B (native probabilities) next to the 13 Nov Claude baseline (stated probabilities).

    uv run evaluate.py

Same 80 messages, same question, same metrics and the same auto-decide band as 2026-11-13-decision-calibration.
"""
import json

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import BASELINE, HERE, RESULTS, load_messages

BINS = 5           # 80 items: 10 bins would leave most bins with a handful of points
BAND = (0.1, 0.9)  # auto-decide when p <= 0.1 or p >= 0.9, otherwise a human looks


def ece(p, y, bins=BINS):
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    total = 0.0
    rows = []
    for b in range(bins):
        mask = idx == b
        if mask.any():
            conf, acc = p[mask].mean(), y[mask].mean()
            total += mask.mean() * abs(conf - acc)
            rows.append((conf, acc, int(mask.sum())))
    return total, rows


def report(name, probs, messages):
    scored = [m for m in messages if probs.get(m["id"]) is not None]
    p = np.array([probs[m["id"]] for m in scored])
    y = np.array([m["label"] for m in scored])
    hard = np.array([m["difficulty"] == "hard" for m in scored])
    auto = (p <= BAND[0]) | (p >= BAND[1])
    calib, rows = ece(p, y)
    wrong_confident = [m["id"] for m, pi, a in zip(scored, p, auto) if a and (pi >= 0.5) != bool(m["label"])]
    wrong = [m["id"] for m, pi in zip(scored, p) if (pi >= 0.5) != bool(m["label"])]
    return {
        "name": name,
        "n": len(scored),
        "accuracy_at_0.5": round(float(((p >= 0.5) == y).mean()), 3),
        "accuracy_hard": round(float(((p[hard] >= 0.5) == y[hard]).mean()), 3),
        "brier": round(float(((p - y) ** 2).mean()), 3),
        "ece_5bin": round(float(calib), 3),
        "auto_share": round(float(auto.mean()), 3),
        "auto_accuracy": round(float(((p[auto] >= 0.5) == y[auto]).mean()), 3) if auto.any() else None,
        "wrong_at_0.5": wrong,
        "confident_and_wrong": wrong_confident,
        "distinct_values": len({round(float(x), 2) for x in p}),
        "bins": [{"mean_p": round(float(c), 3), "frac_yes": round(float(a), 3), "n": n} for c, a, n in rows],
    }


def change(a, b):
    """How far the probability moves between two runs (or two wordings) on the same 80 messages."""
    ids = sorted(set(a) & set(b))
    diff = np.array([abs(a[i] - b[i]) for i in ids])
    flips = [i for i in ids if (a[i] >= 0.5) != (b[i] >= 0.5)]
    band = [i for i in ids if ((a[i] <= BAND[0]) or (a[i] >= BAND[1])) != ((b[i] <= BAND[0]) or (b[i] >= BAND[1]))]
    return {"mean_abs_change": round(float(diff.mean()), 4), "max_abs_change": round(float(diff.max()), 4),
            "label_flips": flips, "band_switches": len(band)}


def load_runs(folder):
    return {p.stem: json.loads(p.read_text()) for p in sorted(folder.glob("*.json")) if p.name != "summary.json"}


def pooled(messages, prob_runs):
    """Several runs of one model on the same messages, as one longer list (more points per bin)."""
    many = [dict(m, id=f'{m["id"]}#{k}') for k in range(len(prob_runs)) for m in messages]
    merged = {f"{i}#{k}": v for k, pr in enumerate(prob_runs) for i, v in pr.items()}
    return many, merged


def main():
    messages = load_messages()
    ours, base = load_runs(RESULTS), load_runs(BASELINE)

    curves = []
    for label, runs in [("Haiku 4.5, stated (13 Nov, 2 runs)", [base["claude-haiku-run1"], base["claude-haiku-run2"]]),
                        ("Sonnet 5.5, stated (13 Nov, 2 runs)", [base["claude-sonnet-run1"], base["claude-sonnet-run2"]]),
                        ("Ivonnet-0.8B, native, original wording", [ours["ivonnet-original-run1"]]),
                        ("Ivonnet-0.8B, native, plain wording", [ours["ivonnet-plain-run1"]])]:
        many, merged = pooled(messages, [r["probs"] for r in runs])
        curves.append(report(label, merged, many))

    orig, orig2, plain = (ours[k]["probs"] for k in ("ivonnet-original-run1", "ivonnet-original-run2",
                                                    "ivonnet-plain-run1"))
    moves = {"ivonnet run1 vs run2 (same wording)": change(orig, orig2),
             "ivonnet original vs plain wording": change(orig, plain),
             "haiku run1 vs run2 (13 Nov)": change(base["claude-haiku-run1"]["probs"], base["claude-haiku-run2"]["probs"]),
             "sonnet run1 vs run2 (13 Nov)": change(base["claude-sonnet-run1"]["probs"],
                                                    base["claude-sonnet-run2"]["probs"])}
    speed = {k: {f: v[f] for f in ("device", "dtype", "machine", "torch", "seconds_per_message")}
             for k, v in ours.items()}
    (RESULTS / "summary.json").write_text(json.dumps({"models": curves, "movement": moves, "speed": speed}, indent=1))

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12, 6), dpi=150)
    ax.plot([0, 1], [0, 1], color="#999999", lw=1, ls="--", label="perfectly calibrated")
    ax.axvspan(BAND[0], BAND[1], color="#eeeeee", label="human review band (0.1 to 0.9)")
    for r, colour in zip(curves, ["#2a6fdb", "#e0803a", "#3aa76d", "#9b59b6"]):
        xs = [b["mean_p"] for b in r["bins"]]
        ys = [b["frac_yes"] for b in r["bins"]]
        ax.plot(xs, ys, marker="o", color=colour,
                label=f'{r["name"]}: ECE {r["ece_5bin"]}, to human {100 * (1 - r["auto_share"]):.1f}%, '
                      f'wrong {len(r["wrong_at_0.5"])}/{r["n"]}')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("probability of yes (bin mean)")
    ax.set_ylabel("share actually yes")
    ax.set_title("Calibration, our small test:\n80 synthetic support messages, 5 bins", fontsize=10)
    ax.legend(loc="upper left", fontsize=6.5, frameon=False)

    ids = [m["id"] for m in messages]
    y = np.array([m["label"] for m in messages])
    xo, xp = np.array([orig[i] for i in ids]), np.array([plain[i] for i in ids])
    bx.plot([0, 1], [0, 1], color="#999999", lw=1, ls="--")
    bx.scatter(xo[y == 1], xp[y == 1], s=18, color="#3aa76d", label="label: yes (refund or dispute)")
    bx.scatter(xo[y == 0], xp[y == 0], s=18, color="#c0392b", marker="x", label="label: no")
    bx.axvline(0.5, color="#dddddd", lw=1)
    bx.axhline(0.5, color="#dddddd", lw=1)
    bx.set_xlim(-0.02, 1.02)
    bx.set_ylim(-0.02, 1.02)
    bx.set_xlabel("Ivonnet p(yes), original question")
    bx.set_ylabel("Ivonnet p(yes), same rule in plainer words")
    m = moves["ivonnet original vs plain wording"]
    bx.set_title(f"Ivonnet-0.8B, same 80 messages, question reworded:\n"
                 f"p(yes) moves {m['mean_abs_change']:.2f} on average, {len(m['label_flips'])} answers flip", fontsize=10)
    bx.legend(loc="upper left", fontsize=7, frameon=False)
    (HERE / "media").mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(HERE / "media" / "calibration-and-wording.png")
    for r in curves:
        print(json.dumps({k: v for k, v in r.items() if k != "bins"}))
    print(json.dumps(moves))


if __name__ == "__main__":
    main()
