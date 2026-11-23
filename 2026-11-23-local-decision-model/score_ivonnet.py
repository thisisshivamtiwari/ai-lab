"""Score the 80 messages with Illuin's Ivonnet-0.8B decision model, on this laptop (no NVIDIA GPU).

    uv run score_ivonnet.py                    # CPU, float32, both question wordings
    uv run score_ivonnet.py --device mps       # Apple GPU instead

Downloads the model (1.7 GB, Apache 2.0) into weights/ on first run and imports the `decision_model`
package that ships inside the model repo, pinned to the revision below.
"""
import argparse
import json
import platform
import sys
import time

import torch

from common import QUESTIONS, RESULTS, WEIGHTS, load_messages

REPO = "illuin/Ivonnet-0.8B"
REVISION = "main"  # resolved to a commit sha in the results file


def load(device):
    from huggingface_hub import HfApi, snapshot_download

    sha = HfApi().model_info(REPO, revision=REVISION).sha
    snapshot_download(REPO, revision=sha, local_dir=WEIGHTS)
    sys.path.insert(0, str(WEIGHTS / "source" / "src"))
    from decision_model import DecisionModel

    t = time.perf_counter()
    model = DecisionModel.from_pretrained(WEIGHTS, device=device)
    return model, sha, time.perf_counter() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--repeat", type=int, default=2, help="runs of the original wording (checks determinism)")
    args = ap.parse_args()

    model, sha, load_s = load(args.device)
    print(json.dumps({"load_s": round(load_s, 1), "attention_check": model.attention_check}, default=str))
    messages = load_messages()
    runs = [("original", k + 1) for k in range(args.repeat)] + [("plain", 1)]
    RESULTS.mkdir(exist_ok=True)
    for wording, run in runs:
        question = {"type": "noul", "instructions": QUESTIONS[wording]}
        probs, seconds = {}, []
        for m in messages:
            t = time.perf_counter()
            out = model.decide(m["text"], {"q": question})
            seconds.append(time.perf_counter() - t)
            probs[m["id"]] = round(float(out["answers"]["q"]["noul"]), 4)
        name = f"ivonnet-{wording}-run{run}"
        (RESULTS / f"{name}.json").write_text(json.dumps({
            "source": "Ivonnet-0.8B decision model (native probability, one forward pass)",
            "models": [f"{REPO}@{sha[:7]}"],
            "question": QUESTIONS[wording],
            "device": args.device,
            "dtype": str(model.dtype),
            "machine": f"{platform.machine()} {platform.mac_ver()[0] or platform.platform()}",
            "torch": torch.__version__,
            "seconds_per_message": {"median": round(sorted(seconds)[len(seconds) // 2], 3),
                                    "max": round(max(seconds), 3), "first": round(seconds[0], 3)},
            "probs": probs,
        }, indent=1))
        print(name, "median s/message", round(sorted(seconds)[len(seconds) // 2], 3))


if __name__ == "__main__":
    main()
