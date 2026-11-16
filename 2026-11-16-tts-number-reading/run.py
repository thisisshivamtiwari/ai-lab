"""Speak every item, then transcribe every clip with Whisper.

Conditions: ZONOS3-Mini with its text normaliser on (the default), the same model with it off, and the macOS `say`
voice Daniel (en_GB) as a familiar baseline. ZONOS3 runs 3 seeds per item; `say` is deterministic, so it runs once.
Needs a ZONOS3 MLX server on 127.0.0.1:1919 (see README). All clips are made first (4 at a time, the server's batch)
and transcribed after, because swapping the GPU between the two models made every call slow. Finished clips and
transcripts are skipped, so a cut-off run resumes.

    uv run run.py
"""
import json
import subprocess
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import mlx_whisper

from items import ITEMS

HERE = Path(__file__).parent
AUDIO = HERE / "results" / "audio"
SERVER = "http://127.0.0.1:1919"
VOICE = "BritishFemale"  # one of the model's stock voices
SEEDS = [1, 2, 3]
MAX_FRAMES = 400  # caps a run-on generation (the server default is 2000); every sentence fits well inside it
WHISPER = "mlx-community/whisper-large-v3-turbo"


def zonos(text, seed, normalise, out):
    speakers = httpx.get(f"{SERVER}/v2/speakers").json()["speakers"]
    voice = next(s["id"] for s in speakers if s["label"] == VOICE)
    body = {"text": text, "language": "en_gb", "stream": False, "format": "wav", "seed": seed,
            "text_normalization": normalise, "speaker_embedding_id": voice, "max_tokens": MAX_FRAMES}
    r = httpx.post(f"{SERVER}/v2/generate", json=body, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)


def say(text, out):
    aiff = out.with_suffix(".aiff")
    subprocess.run(["say", "-v", "Daniel", "-o", str(aiff), text], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(aiff), str(out)], check=True)
    aiff.unlink()


def jobs():
    for no, (category, text, _) in enumerate(ITEMS):
        for seed in SEEDS:
            yield no, "zonos3-norm-on", seed, lambda o, t=text, s=seed: zonos(t, s, True, o)
            yield no, "zonos3-norm-off", seed, lambda o, t=text, s=seed: zonos(t, s, False, o)
        yield no, "macos-say", 0, lambda o, t=text: say(t, o)


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    todo = [(AUDIO / f"{no:02d}-{condition}-s{seed}.wav", speak) for no, condition, seed, speak in jobs()]
    with ThreadPoolExecutor(4) as pool:
        list(pool.map(lambda job: job[1](job[0]), [job for job in todo if not job[0].exists()]))

    out_file = HERE / "results" / "transcripts.jsonl"
    done = set()
    if out_file.exists():
        done = {(r["no"], r["condition"], r["seed"]) for r in map(json.loads, out_file.open())}
    with out_file.open("a") as f:
        for no, condition, seed, _ in jobs():
            if (no, condition, seed) in done:
                continue
            wav = AUDIO / f"{no:02d}-{condition}-s{seed}.wav"
            heard = mlx_whisper.transcribe(str(wav), path_or_hf_repo=WHISPER, language="en",
                                           temperature=0.0)["text"].strip()
            with wave.open(str(wav)) as w:
                seconds = round(w.getnframes() / w.getframerate(), 2)
            f.write(json.dumps({"no": no, "condition": condition, "seed": seed, "seconds": seconds,
                                "heard": heard}) + "\n")
            f.flush()
            print(f"{no:02d} {condition:16s} s{seed} {seconds:5.1f}s  {heard}", flush=True)


if __name__ == "__main__":
    main()
