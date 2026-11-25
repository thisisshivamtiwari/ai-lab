"""Run OCRia-nano (via LiteParse) and Apple Vision (on-device) on every page in docs/, score number tokens.
Writes out/results.json and out/summary.json. Our small test, not a benchmark."""
import json, re, subprocess, time
from pathlib import Path

VISION = "/Applications/Softwares/CVMaker/linkedin/demos/agent/ocr"
truth = json.load(open("truth.json"))
NUMLIKE = re.compile(r"£\s?\d[\d,]*\.\d{2}|\d{2}/\d{2}/\d{4}|\b[A-Z]{2,3}-\d{5}|\d{2}-\d{2}-\d{2}|\d+%")
MONEY = re.compile(r"£\d[\d,]*\.\d{2}")

def norm(s):  # OCR engines differ in spacing; compare with spaces removed
    return re.sub(r"\s+", "", s)

def ocria(path):
    t = time.perf_counter()
    p = subprocess.run(["lit", "parse", str(path), "--format", "text", "-q"], capture_output=True, text=True)
    return p.stdout, time.perf_counter() - t

def vision(path):
    t = time.perf_counter()
    p = subprocess.run([VISION, str(path)], capture_output=True, text=True)
    d = json.loads(p.stdout.strip().splitlines()[-1])
    return "\n".join(i["text"] for i in d.get("items", [])), time.perf_counter() - t, d.get("mode")

results = []
for row in truth:
    path = Path("docs") / row["file"]
    for engine in ["ocria-nano", "apple-vision"]:
        if engine == "ocria-nano":
            text, secs = ocria(path); mode = "cpu"
        else:
            text, secs, mode = vision(path)
        flat = norm(text)
        found = [tok for tok in row["tokens"] if norm(tok) in flat]
        # number-like strings the engine produced that are not on the page: silent misreads
        produced = set(norm(m) for m in NUMLIKE.findall(text))  # on raw text, so "PO PO-123" is not a ghost
        truth_set = set(norm(t) for t in row["tokens"])
        ghosts = sorted(p for p in produced if p not in truth_set)
        results.append({**row, "engine": engine, "mode": mode, "secs": round(secs, 3), "n": len(row["tokens"]),
                        "found": len(found), "text": text, "missed": [t for t in row["tokens"] if t not in found], "ghosts": ghosts,
                        "money_ghosts": [g for g in ghosts if MONEY.match(g)]})
        print(f"{row['file']:28s} {engine:13s} {len(found):3d}/{len(row['tokens']):3d} ghosts={len(ghosts):2d} {secs:5.2f}s {mode}")

json.dump(results, open("out/results.json", "w"), indent=1)
summary = {}
for engine in ["ocria-nano", "apple-vision"]:
    for cond in ["clean", "scan", "phone", "lowres", "all"]:
        rs = [r for r in results if r["engine"] == engine and (cond == "all" or r["cond"] == cond)]
        n = sum(r["n"] for r in rs); f = sum(r["found"] for r in rs)
        summary[f"{engine}/{cond}"] = {"pages": len(rs), "tokens": n, "found": f, "exact_pct": round(100 * f / n, 1),
                                       "ghost_tokens": sum(len(r["ghosts"]) for r in rs),
                                       "money_ghosts": sum(len(r["money_ghosts"]) for r in rs),
                                       "median_secs": sorted(r["secs"] for r in rs)[len(rs) // 2]}
for engine in ["ocria-nano", "apple-vision"]:
    for doc in ["ratecard", "folio", "invoice"]:
        rs = [r for r in results if r["engine"] == engine and r["doc"] == doc]
        n = sum(r["n"] for r in rs); f = sum(r["found"] for r in rs)
        summary[f"{engine}/doc:{doc}"] = {"pages": len(rs), "tokens": n, "found": f, "exact_pct": round(100 * f / n, 1),
                                          "ghost_tokens": sum(len(r["ghosts"]) for r in rs)}
json.dump(summary, open("out/summary.json", "w"), indent=1)
for k, v in summary.items(): print(k, v)
