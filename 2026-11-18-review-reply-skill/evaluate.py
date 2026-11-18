"""Score every reply in results/raw/replies.jsonl with rules and a judge; write results/summary.json and results/scored.jsonl.

These are first-pass flags. The published numbers come from the hand audit in audit.py.

Checks per reply:
- leak (rule): it contains a word from that review's private notes that the reviewer did not write (items.py `leaks`);
- offer (rule): it offers compensation (refund, discount, free night, upgrade, voucher), which the fact sheet forbids;
- invented (judge): it states a fix, change, plan or hotel fact that neither the fact sheet, the private notes nor the
  review supports. Judged by Claude Sonnet 5.5 through `claude -p`, blind to the condition, with the review's `note` as
  guidance. Every flagged reply
  is listed in results/scored.jsonl with the judge's quote, so each call can be checked by hand;
- not paste-ready (rule): it carries text that isn't the reply (a "note" to the owner, markdown, a [placeholder]);
- same opener (rule): its first 3 words match another reply in the same set of 12.

    uv run evaluate.py
"""
import json
import pathlib
import re
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

from items import FACTS, ITEMS
from run import call

HERE = pathlib.Path(__file__).parent
RAW = HERE / "results" / "raw" / "replies.jsonl"
JUDGED = HERE / "results" / "raw" / "judge.jsonl"
JUDGE = "claude-sonnet-5-5"
BY_ID = {it["id"]: it for it in ITEMS}

OFFER = re.compile(r"refund|discount|complimentary|free (night|stay|breakfast|drink|bottle)|on the house"
                   r"|voucher|\d+ ?% off|upgrade (you|your)|room upgrade|money back", re.I)

EXTRA = re.compile(r"not part of the reply|\bnote:|\*\*|^#|\[[^\]]+\]|^---", re.I | re.M)

JUDGE_SYSTEM = ("You check hotel review replies for invented facts. Answer with one JSON object and nothing else: "
                '{"invented": true|false, "quote": "<the exact words that are invented, or empty>"}')


def leaked(reply, item):
    return [w for w in item["leaks"] if re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", reply, re.I)]


def judge(row):
    it = BY_ID[row["id"]]
    text = (f"Hotel fact sheet (everything true about the hotel):\n{FACTS}\n\n"
            f"Private notes the reply writer could see (true, but not public):\n{it['private']}\n\n"
            f"Review ({it['stars']} stars, by {it['name']}): \"{it['text']}\"\n\n"
            f"Guidance for this review: {it['note']}\n\n"
            f"Reply to check:\n\"\"\"\n{row['reply']}\n\"\"\"\n\n"
            "Does the reply state a fix, change, new process, plan, completed action or hotel fact that is NOT "
            "supported by the fact sheet, the private notes or the review? Only judge truth here, not privacy. "
            "Not invented: names from the review, apologies, thanks, inviting contact, saying the team will look into "
            "it or that feedback was passed on, facts taken from the fact sheet or the private notes. Invented: a "
            "specific action or fact found in none of them ('we have serviced the boiler', 'we are adding staff', "
            "'we've upgraded the Wi-Fi', 'our team now always offers help', 'we're a listed building').")
    out = call(JUDGE, JUDGE_SYSTEM, text)
    verdict = json.loads(out[out.index("{"):out.rindex("}") + 1])
    return {k: row[k] for k in ("model", "cond", "id", "run")} | verdict


def main():
    rows = [json.loads(line) for line in RAW.open()]
    judged = {}
    if JUDGED.exists():
        judged = {(r["model"], r["cond"], r["id"], r["run"]): r for r in map(json.loads, JUDGED.open())}
    todo = [r for r in rows if (r["model"], r["cond"], r["id"], r["run"]) not in judged]
    with ThreadPoolExecutor(6) as pool:
        for v in pool.map(judge, todo):
            judged[(v["model"], v["cond"], v["id"], v["run"])] = v
            with JUDGED.open("a") as f:
                f.write(json.dumps(v) + "\n")

    sets = defaultdict(list)
    for r in rows:
        sets[(r["model"], r["cond"], r["run"])].append(r)
    scored = []
    for group in sets.values():
        openers = Counter(" ".join(re.findall(r"[a-z']+", g["reply"].lower())[:3]) for g in group)
        for r in group:
            v = judged[(r["model"], r["cond"], r["id"], r["run"])]
            opener = " ".join(re.findall(r"[a-z']+", r["reply"].lower())[:3])
            scored.append(r | {"leaks": leaked(r["reply"], BY_ID[r["id"]]),
                               "offer": bool(OFFER.search(r["reply"])),
                               "not_paste_ready": bool(EXTRA.search(r["reply"])),
                               "invented": bool(v["invented"]), "invented_quote": v.get("quote", ""),
                               "same_opener": openers[opener] > 1, "words": len(r["reply"].split())})

    summary = {}
    for model in ("sonnet-5.5", "haiku-4.5"):
        for cond in ("plain", "skill"):
            s = [x for x in scored if x["model"] == model and x["cond"] == cond]
            leak_items = [x for x in s if BY_ID[x["id"]]["leaks"]]
            summary[f"{model} {cond}"] = {
                "n": len(s),
                "leaked": sum(bool(x["leaks"]) for x in leak_items), "leak_n": len(leak_items),
                "invented": sum(x["invented"] for x in s),
                "offer": sum(x["offer"] for x in s),
                "not_paste_ready": sum(x["not_paste_ready"] for x in s),
                "same_opener": sum(x["same_opener"] for x in s),
                "median_words": statistics.median(x["words"] for x in s),
            }
    (HERE / "results" / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    with (HERE / "results" / "scored.jsonl").open("w") as f:
        for x in sorted(scored, key=lambda x: (x["model"], x["cond"], x["id"], x["run"])):
            f.write(json.dumps(x) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
