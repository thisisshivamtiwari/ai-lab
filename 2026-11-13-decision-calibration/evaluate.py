"""Calibration report for every results/*.json: accuracy, Brier score, ECE, and the auto-decide band.

    uv run evaluate.py
"""
import json

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import HERE, RESULTS, load_messages

BINS = 5          # 80 items: 10 bins would leave most bins with a handful of points
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
    return {
        "name": name,
        "n": len(scored),
        "accuracy_at_0.5": round(float(((p >= 0.5) == y).mean()), 3),
        "accuracy_hard": round(float(((p[hard] >= 0.5) == y[hard]).mean()), 3),
        "brier": round(float(((p - y) ** 2).mean()), 3),
        "ece_5bin": round(float(calib), 3),
        "auto_share": round(float(auto.mean()), 3),
        "auto_accuracy": round(float(((p[auto] >= 0.5) == y[auto]).mean()), 3) if auto.any() else None,
        "confident_and_wrong": wrong_confident,
        "distinct_values": sorted({round(float(x), 2) for x in p}),
        "bins": [{"mean_p": round(float(c), 3), "frac_yes": round(float(a), 3), "n": n} for c, a, n in rows],
    }


def stability(a, b):
    """How much the same model's stated probability moves between two runs on the same 80 messages."""
    ids = sorted(set(a) & set(b))
    diff = np.array([abs(a[i] - b[i]) for i in ids])
    flips = [i for i in ids if (a[i] >= 0.5) != (b[i] >= 0.5)]
    band = [i for i in ids if ((a[i] <= BAND[0]) or (a[i] >= BAND[1])) != ((b[i] <= BAND[0]) or (b[i] >= BAND[1]))]
    return {"mean_abs_change": round(float(diff.mean()), 3), "max_abs_change": round(float(diff.max()), 3),
            "label_flips": flips, "band_switches": len(band)}


def main():
    messages = load_messages()
    runs = {}
    for path in sorted(RESULTS.glob("*.json")):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text())
        runs[path.stem] = data
    reports = [report(f'{stem} ({", ".join(d.get("models", []))})', d["probs"], messages)
               for stem, d in runs.items()]

    # Pool the runs of each model for the reliability curve (more points per bin; same messages each run).
    pooled = {}
    for stem, d in runs.items():
        model = stem.rsplit("-run", 1)[0]
        pooled.setdefault(model, []).append(d["probs"])
    curves, stable = [], {}
    for model, prob_runs in pooled.items():
        twice = [dict(m, id=f'{m["id"]}#{k}') for k in range(len(prob_runs)) for m in messages]
        merged = {f"{i}#{k}": v for k, pr in enumerate(prob_runs) for i, v in pr.items()}
        curves.append(report(f"{model} ({len(prob_runs)} runs pooled)", merged, twice))
        if len(prob_runs) > 1:
            stable[model] = stability(prob_runs[0], prob_runs[1])
    (RESULTS / "summary.json").write_text(json.dumps({"per_run": reports, "pooled": curves,
                                                      "run_to_run": stable}, indent=1))

    fig, ax = plt.subplots(figsize=(6.4, 6.4), dpi=150)
    ax.plot([0, 1], [0, 1], color="#999999", lw=1, ls="--", label="perfectly calibrated")
    ax.axvspan(BAND[0], BAND[1], color="#eeeeee", label="human review band (0.1 to 0.9)")
    for r, colour, offset in zip(curves, ["#2a6fdb", "#e0803a", "#3aa76d"], [(6, -10), (-30, 6), (6, 6)]):
        xs = [b["mean_p"] for b in r["bins"]]
        ys = [b["frac_yes"] for b in r["bins"]]
        ax.plot(xs, ys, marker="o", color=colour,
                label=f'{r["name"]}: ECE {r["ece_5bin"]}, sent to human {100 * (1 - r["auto_share"]):.1f}%')
        for x, yv, b in zip(xs, ys, r["bins"]):
            ax.annotate(f'n={b["n"]}', (x, yv), textcoords="offset points", xytext=offset, fontsize=7,
                        color=colour)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("stated probability of yes (bin mean)")
    ax.set_ylabel("share actually yes")
    ax.set_title("Are verbalised yes/no probabilities calibrated?\n"
                 "our small test: 80 synthetic support messages x 2 runs, 5 bins", fontsize=10)
    ax.legend(loc="upper left", fontsize=7, frameon=False)
    (HERE / "media").mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(HERE / "media" / "reliability.png")
    for r in reports + curves:
        print(json.dumps({k: v for k, v in r.items() if k not in ("bins", "distinct_values")}))
    print(json.dumps(stable))


if __name__ == "__main__":
    main()
