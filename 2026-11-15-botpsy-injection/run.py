"""Generate the next assistant turn for every scenario x injection style, locally with mlx-lm.

The conversation already holds Sam's request, the assistant's read call and the tool result (with or without an
injection), so the model's next move is the one we score. Completions are appended to results/raw/<alias>-s<seed>.jsonl
as they arrive; a cut-off run resumes where it stopped.

    uv run run.py --model botpsy --seed 0
"""
import argparse
import json
import time

import mlx.core as mx
from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler

from common import MODELS, RESULTS, STYLES, TOOLS, build_messages, load_scenarios


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
        done = {(r["no"], r["style"]) for r in map(json.loads, path.read_text().splitlines())}
    jobs = [(sc, style) for sc in load_scenarios() for style in STYLES if (sc["no"], style) not in done]

    model, tokenizer = load(MODELS[args.model])
    # The BotPsy card's settings (temperature 0.3, top_p 0.95, top_k 20), used for both models. Its presence
    # penalty of 1.5 isn't in mlx-lm's sampler, so it's left out for both.
    sampler = make_sampler(temp=0.3, top_p=0.95, top_k=20)
    with path.open("a") as f:
        for k, (sc, style) in enumerate(jobs):
            prompt = tokenizer.apply_chat_template(build_messages(sc, style), tools=TOOLS, add_generation_prompt=True,
                                                   enable_thinking=True, tokenize=False)
            mx.random.seed(args.seed * 1000 + sc["no"] * 10 + STYLES.index(style))
            start = time.time()
            text = generate(model, tokenizer, prompt, max_tokens=args.max_tokens, sampler=sampler)
            row = {"no": sc["no"], "style": style, "model": MODELS[args.model], "seed": args.seed,
                   "seconds": round(time.time() - start, 1), "completion": text}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{k + 1}/{len(jobs)} #{sc['no']} {style} {row['seconds']}s", flush=True)
    print(f"{path}: {len(done) + len(jobs)} rows")


if __name__ == "__main__":
    main()
