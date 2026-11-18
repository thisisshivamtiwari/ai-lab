"""Draft an owner reply to every review, with and without the `reviews` skill, through the Claude Code CLI (`claude -p`).

The skill text (SKILL.md and its 3 reference files) is downloaded at a pinned commit into skill/ and given to the model as
its system prompt, which is what loading the skill puts in front of it. Tools are switched off. Raw replies are appended
to results/raw/replies.jsonl as they arrive, so a cut-off run resumes where it stopped.

    uv run run.py            # 12 reviews x 2 conditions x 2 models x 2 runs = 96 calls
"""
import json
import pathlib
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from items import FACTS, ITEMS

REPO = "boringmarketer/boring-marketing-skills"
SHA = "bd5aaedab44368d76326d98d488697158b886679"  # main on 18 Nov 2026, version 4.1.1
FILES = ["SKILL.md", "references/reply-playbook.md", "references/review-policy-facts.md", "references/ask-playbook.md"]
MODELS = {"sonnet-5.5": "claude-sonnet-5-5", "haiku-4.5": "claude-haiku-4-5-20251001"}
RUNS = 2
HERE = pathlib.Path(__file__).parent
RAW = HERE / "results" / "raw" / "replies.jsonl"

BASE = "You help a hotel's marketing team. You draft public owner replies to Google reviews."


def skill_text():
    out = []
    for f in FILES:
        path = HERE / "skill" / f
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            url = f"https://raw.githubusercontent.com/{REPO}/{SHA}/skills/reviews/{f}"
            path.write_bytes(urllib.request.urlopen(url, timeout=30).read())
        out.append(f"<file path=\"skills/reviews/{f}\">\n{path.read_text()}\n</file>")
    return "\n\n".join(out)


def prompt(item):
    return (f"Hotel fact sheet:\n{FACTS}\n\n"
            f"Internal notes for this review (from the booking system and staff):\n{item['private']}\n\n"
            f"The review (Google, {item['stars']} stars, {item['date']}, by {item['name']}):\n\"{item['text']}\"\n\n"
            "Draft the owner reply to post on Google. Output only the reply text.")


def call(model, system, text):
    out = subprocess.run(
        ["claude", "-p", text, "--model", model, "--output-format", "json", "--tools", "",
         "--strict-mcp-config", "--setting-sources", "", "--system-prompt", system],
        capture_output=True, text=True, check=True, timeout=300, stdin=subprocess.DEVNULL,
    )
    return json.loads(out.stdout)["result"].strip()


def main():
    systems = {"plain": BASE,
               "skill": BASE + " The `reviews` skill is loaded; follow it.\n\n" + skill_text()}
    done = set()
    if RAW.exists():
        done = {(r["model"], r["cond"], r["id"], r["run"]) for r in map(json.loads, RAW.open())}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    jobs = [(m, c, it, r) for m in MODELS for c in systems for it in ITEMS for r in range(RUNS)
            if (m, c, it["id"], r) not in done]
    print(f"{len(jobs)} calls to make")

    def one(job):
        m, c, it, r = job
        reply = call(MODELS[m], systems[c], prompt(it))
        row = {"model": m, "cond": c, "id": it["id"], "run": r, "reply": reply}
        with RAW.open("a") as f:
            f.write(json.dumps(row) + "\n")
        return row

    with ThreadPoolExecutor(6) as pool:
        for row in pool.map(one, jobs):
            print(row["model"], row["cond"], row["id"], row["run"], len(row["reply"].split()), "words")


if __name__ == "__main__":
    main()
