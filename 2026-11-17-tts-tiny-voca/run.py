"""Speak every item with tiny-voca's two voices, then transcribe every clip with Whisper.

tiny-voca runs on the CPU through its own speak_text (dizione front end, the one the checkpoint was trained with).
The card says the same text gets the same delivery every time, so each voice reads each item once; run.py checks
that by speaking item 0 twice and comparing the samples. Clips are made first and transcribed after, with the same
Whisper model and settings as the 16 Nov ZONOS3-Mini run, so the pass rates line up. Finished clips and
transcripts are skipped, so a cut-off run resumes.

    uv run run.py
"""
import json
import os
from pathlib import Path

HERE = Path(__file__).parent
os.environ.setdefault("DIZIONE_DATA", str(HERE / "weights" / "phonemizer"))

import mlx_whisper
import soundfile as sf
import torch
from tiny_voca.infer import load_model, match_frontend, speak_text

from items import ITEMS

AUDIO = HERE / "results" / "audio"
CHECKPOINT = HERE / "weights" / "tiny-voca.pt"
VOICES = ["F2", "M2"]
WHISPER = "mlx-community/whisper-large-v3-turbo"


def main():
    torch.set_num_threads(4)
    frontend = match_frontend(CHECKPOINT)
    model = load_model(CHECKPOINT)
    AUDIO.mkdir(parents=True, exist_ok=True)

    first = [speak_text(model, ITEMS[0][1], "F2")[0] for _ in range(2)]
    deterministic = torch.equal(*first)
    print(f"front end {frontend}; item 0 spoken twice, identical samples: {deterministic}")

    for no, (_, text, _) in enumerate(ITEMS):
        for voice in VOICES:
            wav = AUDIO / f"{no:02d}-tiny-voca-{voice}.wav"
            if not wav.exists():
                with torch.inference_mode():
                    audio, _ = speak_text(model, text, voice)
                sf.write(wav, audio.numpy(), model.config.sample_rate, subtype="PCM_16")

    out_file = HERE / "results" / "transcripts.jsonl"
    done = set()
    if out_file.exists():
        done = {(r["no"], r["condition"]) for r in map(json.loads, out_file.open())}
    with out_file.open("a") as f:
        for no in range(len(ITEMS)):
            for voice in VOICES:
                condition = f"tiny-voca-{voice}"
                if (no, condition) in done:
                    continue
                wav = AUDIO / f"{no:02d}-{condition}.wav"
                heard = mlx_whisper.transcribe(str(wav), path_or_hf_repo=WHISPER, language="en",
                                               temperature=0.0)["text"].strip()
                seconds = round(sf.info(wav).duration, 2)
                f.write(json.dumps({"no": no, "condition": condition, "seed": 0, "seconds": seconds,
                                    "heard": heard}) + "\n")
                f.flush()
                print(f"{no:02d} {condition:14s} {seconds:5.1f}s  {heard}", flush=True)
    (HERE / "results" / "run.json").write_text(json.dumps(
        {"frontend": frontend, "item0_identical_twice": deterministic, "voices": VOICES, "whisper": WHISPER},
        indent=1))


if __name__ == "__main__":
    main()
