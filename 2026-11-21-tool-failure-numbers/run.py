"""Generate the next assistant turn for every task x tool-failure condition, locally with mlx-lm.

The conversation already holds the user's question, the assistant's tool call and the tool's reply (the real answer,
or a timeout, a cut-off JSON, an empty object, or a sub-agent report with no figure), so the model's next move is the
one we score. Completions are appended to results/raw/<alias>-s<seed>.jsonl
as they arrive; a cut-off run resumes where it stopped.

    uv run run.py --model botpsy --seed 0
"""
import argparse
import json
import time

import mlx.core as mx
from common import CONDITIONS, MODELS, RESULTS, TOOLS, build_messages, load_tasks
from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=sorted(MODELS), default="botpsy")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=2048)
    args = ap.parse_args()

    raw = RESULTS / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    path = raw / f"{args.model}-s{args.seed}.jsonl"
    done = set()
    if path.exists():
        done = {(r["no"], r["condition"]) for r in map(json.loads, path.read_text().splitlines())}
    jobs = [(t, c) for t in load_tasks() for c in CONDITIONS if (t["no"], c) not in done]

    model, tokenizer = load(MODELS[args.model])
    # The BotPsy card's settings (temperature 0.3, top_p 0.95, top_k 20), used for both models, as on 15 Nov.
    sampler = make_sampler(temp=0.3, top_p=0.95, top_k=20)
    with path.open("a") as f:
        for k, (t, c) in enumerate(jobs):
            prompt = tokenizer.apply_chat_template(build_messages(t, c), tools=TOOLS, add_generation_prompt=True,
                                                   enable_thinking=True, tokenize=False)
            mx.random.seed(args.seed * 1000 + t["no"] * 10 + CONDITIONS.index(c))
            start = time.time()
            text = generate(model, tokenizer, prompt, max_tokens=args.max_tokens, sampler=sampler)
            row = {"no": t["no"], "condition": c, "model": MODELS[args.model], "seed": args.seed,
                   "seconds": round(time.time() - start, 1), "completion": text}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{k + 1}/{len(jobs)} #{t['no']} {c} {row['seconds']}s", flush=True)
    print(f"{path}: {len(done) + len(jobs)} rows")


if __name__ == "__main__":
    main()
