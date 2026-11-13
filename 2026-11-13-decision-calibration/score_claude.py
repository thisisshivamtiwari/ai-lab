"""Ask Claude (through the Claude Code CLI, `claude -p`) for a verbalised probability per message.

Claude has no decision endpoint, so this is the baseline a decision API has to beat: the model writes its
probability as a number. Messages go in shuffled batches of 20 (fixed seed) to keep the number of calls small.

    uv run score_claude.py --model haiku --run 1
"""
import argparse
import json
import random
import re
import subprocess

from common import QUESTION, RESULTS, load_messages

SYSTEM = (
    "You are a classifier for a payments app's support desk. For each customer message, give the probability "
    "(a number from 0 to 1) that the answer to the question is yes. Use the full range: say 0.5 when you are "
    "unsure. Output one JSON object mapping message id to probability, and nothing else."
)


def ask(model, batch):
    lines = "\n".join(f'{m["id"]}: {m["text"]}' for m in batch)
    prompt = f"Question: {QUESTION}\n\nMessages:\n{lines}"
    out = subprocess.run(
        ["claude", "-p", prompt, "--model", model, "--output-format", "json", "--tools", "",
         "--strict-mcp-config", "--setting-sources", "", "--system-prompt", SYSTEM],
        capture_output=True, text=True, check=True, timeout=300,
    )
    reply = json.loads(out.stdout)
    text = reply["result"]
    probs = json.loads(re.search(r"\{.*\}", text, re.DOTALL).group(0))
    return probs, list(reply.get("modelUsage", {}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--run", type=int, default=1, help="repeat number; run 2+ re-asks the same batches")
    args = ap.parse_args()

    messages = load_messages()
    random.Random(13).shuffle(messages)
    probs, models = {}, set()
    for i in range(0, len(messages), args.batch):
        got, used = ask(args.model, messages[i:i + args.batch])
        probs.update({k: float(v) for k, v in got.items()})
        models.update(used)
    missing = [m["id"] for m in messages if m["id"] not in probs]
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / f"claude-{args.model}-run{args.run}.json"
    path.write_text(json.dumps({"source": "claude -p (verbalised probability)", "alias": args.model,
                                "models": sorted(models), "batch": args.batch, "run": args.run, "missing": missing,
                                "probs": probs}, indent=1))
    print(f"wrote {path} ({len(probs)} scored, {len(missing)} missing, models {sorted(models)})")


if __name__ == "__main__":
    main()
