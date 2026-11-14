"""Send every item in every format to a Claude model through the Claude Code CLI (`claude -p`), one call each.

Raw replies are appended to results/raw/<alias>.jsonl as they arrive, so a cut-off run resumes where it stopped.
They stay out of git (the CLI adds account-level instructions that replies sometimes quote); evaluate.py
writes the scored rows that are committed.

    uv run run.py --model haiku
"""
import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor

from common import FORMATS, RESULTS, SYSTEM, build_prompt, load_items


def ask(model, prompt):
    out = subprocess.run(
        ["claude", "-p", prompt, "--model", model, "--output-format", "json", "--tools", "",
         "--strict-mcp-config", "--setting-sources", "", "--system-prompt", SYSTEM],
        capture_output=True, text=True, check=True, timeout=300, stdin=subprocess.DEVNULL,
    )
    reply = json.loads(out.stdout)
    return reply["result"], sorted(reply.get("modelUsage", {}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--run", type=int, default=1, help="repeat number; run 2+ writes its own file")
    ap.add_argument("--styles", default="", help="comma-separated injection styles to send (default: all)")
    args = ap.parse_args()

    raw = RESULTS / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    path = raw / (f"{args.model}.jsonl" if args.run == 1 else f"{args.model}-run{args.run}.jsonl")
    styles = set(filter(None, args.styles.split(",")))
    done = set()
    if path.exists():
        done = {(r["no"], r["format"]) for r in map(json.loads, path.read_text().splitlines())}
    jobs = [(item, fmt) for item in load_items() for fmt in FORMATS
            if (item["no"], fmt) not in done and (not styles or item["style"] in styles)]

    def one(job):
        item, fmt = job
        text, models = ask(args.model, build_prompt(item, fmt))
        return {"no": item["no"], "doc": item["id"], "style": item["style"], "format": fmt,
                "models": models, "reply": text}

    with ThreadPoolExecutor(args.workers) as pool, path.open("a") as f:
        for row in pool.map(one, jobs):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
    print(f"{path}: {len(done) + len(jobs)} rows")


if __name__ == "__main__":
    main()
