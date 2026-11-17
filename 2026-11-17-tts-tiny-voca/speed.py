"""Time tiny-voca on this Mac's CPU: all 36 items, each voice, 4 threads, after one warm-up item.

Prints and writes results/speed.json: seconds of audio made per second of compute (the real-time factor).

    uv run speed.py
"""
import json
import os
import platform
import time
from pathlib import Path

HERE = Path(__file__).parent
os.environ.setdefault("DIZIONE_DATA", str(HERE / "weights" / "phonemizer"))

import torch
from tiny_voca.infer import load_model, match_frontend, speak_text

from items import ITEMS

CHECKPOINT = HERE / "weights" / "tiny-voca.pt"


def main():
    torch.set_num_threads(4)
    match_frontend(CHECKPOINT)
    model = load_model(CHECKPOINT)
    speak_text(model, ITEMS[0][1], "F2")
    out = {"machine": platform.machine(), "cpu": platform.processor(), "threads": 4}
    for voice in ("F2", "M2"):
        audio_s, start = 0.0, time.perf_counter()
        with torch.inference_mode():
            for _, text, _ in ITEMS:
                audio_s += len(speak_text(model, text, voice)[0]) / model.config.sample_rate
        compute = time.perf_counter() - start
        out[voice] = {"audio_s": round(audio_s, 1), "compute_s": round(compute, 2),
                      "x_real_time": round(audio_s / compute, 1)}
    (HERE / "results" / "speed.json").write_text(json.dumps(out, indent=1))
    print(out)


if __name__ == "__main__":
    main()
