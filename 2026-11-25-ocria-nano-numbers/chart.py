"""Chart + near-miss analysis. Reads out/results.json, writes media/number-accuracy.png and out/near_miss.json."""
import json, re
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = json.load(open("out/results.json"))
S = json.load(open("out/summary.json"))
# near-miss amounts: amount-shaped strings in the output (any currency-ish glyph) that are not a true amount on the page
AMT = re.compile(r"[£§$S8€]\s?(\d[\d,]*[.,]\d{2})")
near = {}
for r in R:
    truth_amts = {re.sub(r"[£,]", "", t) for t in r["tokens"] if t.startswith("£")}
    out_amts = [m.replace(",", "").replace(" ", "") for m in AMT.findall(r["text"])]
    bad = [a for a in out_amts if a.replace(",", ".") not in truth_amts]
    key = f'{r["engine"]}/{r["cond"]}'
    d = near.setdefault(key, {"pages": 0, "amount_strings_out": 0, "near_miss_amounts": 0, "examples": []})
    d["pages"] += 1; d["amount_strings_out"] += len(out_amts); d["near_miss_amounts"] += len(bad)
    if bad and len(d["examples"]) < 6:
        d["examples"].append({"file": r["file"], "wrong": bad[:3]})
json.dump(near, open("out/near_miss.json", "w"), indent=1)
for k, v in near.items(): print(k, {x: v[x] for x in v if x != "examples"})

conds = ["clean", "scan", "phone", "lowres"]
labels = ["Clean\n200 dpi", "Photocopy\n(blur, grain, tilt)", "Phone photo\n(shade, tilt, 150 dpi)", "Fax-like\n100 dpi, 1-bit"]
engines = [("ocria-nano", "OCRia-nano-1 (8M params, CPU)", "#1f4e79"), ("apple-vision", "Apple Vision (on-device)", "#8c8c8c")]
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=160)
w = 0.38
for i, (eng, name, col) in enumerate(engines):
    vals = [S[f"{eng}/{c}"]["exact_pct"] for c in conds]
    xs = [x + (i - 0.5) * w for x in range(len(conds))]
    bars = ax.bar(xs, vals, w, label=name, color=col)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.0f}%", ha="center", fontsize=9, color=col)
ax.set_xticks(range(len(conds))); ax.set_xticklabels(labels, fontsize=9)
ax.set_ylim(0, 110); ax.set_ylabel("Number tokens read exactly (%)")
ax.set_title("Can a 48 MB OCR read the money on hotel paperwork?\nOur small test: 60 synthetic pages, 1,500 prices, dates and references", fontsize=11)
ax.spines[["top", "right"]].set_visible(False); ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2, fontsize=9)
ax.text(-0.6, -34, "Synthetic rate cards, guest folios and supplier invoices (5 seeds x 3 types x 4 conditions). Exact-match after removing spaces.\n"
        "Neither engine was tuned. One Mac, one run. Not a benchmark. github.com/thisisshivamtiwari/ai-lab", fontsize=7.5, color="#555", transform=ax.transData)
fig.tight_layout(); fig.savefig("media/number-accuracy.png", bbox_inches="tight")
print("chart written")
