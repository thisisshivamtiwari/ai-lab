"""Speak every item with three macOS voices, then transcribe every clip three ways.

Voices: Daniel (en_GB), Samantha (en_US), Karen (en_AU), all through `say`, so the audio is the same for every
transcriber. Each clip also gets a noisy copy: white noise at 5 dB SNR, seeded per clip. Transcribers:
Rumble-2-Flash with its `digits` option on (the default) and off, and mlx-community/whisper-large-v3-turbo. All Rumble clips run first and Whisper after, because two models taking turns
on the GPU made every call slow (16 Nov lab). Finished clips and transcripts are skipped, so a cut-off run resumes.

    uv run run.py
"""
import json
import subprocess
import time
from pathlib import Path

import mlx_whisper
import numpy as np
import soundfile as sf
import torch
from transformers import AutoModelForMultimodalLM, AutoProcessor

from items import ITEMS

HERE = Path(__file__).parent
AUDIO = HERE / "results" / "audio"
OUT = HERE / "results" / "transcripts.jsonl"
VOICES = ["Daniel", "Samantha", "Karen"]
RUMBLE = "Reson8/Rumble-2-Flash"
WHISPER = "mlx-community/whisper-large-v3-turbo"
SNR_DB = 5


def speak(text, voice, out):
    aiff = out.with_suffix(".aiff")
    subprocess.run(["say", "-v", voice, "-o", str(aiff), text], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(aiff), "-ar", "16000", "-ac", "1", str(out)],
                   check=True)
    aiff.unlink()


def add_noise(clean, out, seed):
    speech, rate = sf.read(clean)
    noise = np.random.default_rng(seed).standard_normal(len(speech))
    noise *= np.sqrt(np.mean(speech ** 2) / (np.mean(noise ** 2) * 10 ** (SNR_DB / 10)))
    mixed = speech + noise
    sf.write(out, mixed / max(1.0, np.abs(mixed).max()), rate)


def done():
    if not OUT.exists():
        return set()
    return {(r["condition"], r["audio"], r["voice"], r["no"]) for r in map(json.loads, OUT.open())}


def write(row):
    with OUT.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def clips():
    for audio in ("clean", "noisy"):
        for voice in VOICES:
            for no in range(len(ITEMS)):
                yield audio, voice, no, AUDIO / f"{no:02d}-{voice}-{audio}.wav"


def rumble(seen):
    processor = AutoProcessor.from_pretrained(RUMBLE)
    model = AutoModelForMultimodalLM.from_pretrained(RUMBLE, device_map="mps", dtype=torch.float16)
    for digits in (True, False):
        condition = "rumble-digits-on" if digits else "rumble-digits-off"
        for audio, voice, no, wav in clips():
            if (condition, audio, voice, no) in seen:
                continue
            start = time.time()
            inputs = processor.apply_transcription_request(audio=str(wav), language="English", digits=digits)
            inputs = inputs.to(model.device, dtype=model.dtype)
            out = model.generate(**inputs, max_new_tokens=256, do_sample=False)
            heard = processor.decode(out[:, inputs["input_ids"].shape[-1]:], return_format="transcription_only")[0]
            write({"condition": condition, "audio": audio, "voice": voice, "no": no, "heard": heard,
                   "seconds": round(time.time() - start, 3)})


def whisper(seen):
    for audio, voice, no, wav in clips():
        if ("whisper-turbo", audio, voice, no) in seen:
            continue
        start = time.time()
        heard = mlx_whisper.transcribe(str(wav), path_or_hf_repo=WHISPER, language="en", temperature=0.0)["text"]
        write({"condition": "whisper-turbo", "audio": audio, "voice": voice, "no": no, "heard": heard.strip(),
               "seconds": round(time.time() - start, 3)})


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    for audio, voice, no, wav in clips():
        if wav.exists():
            continue
        if audio == "clean":
            speak(ITEMS[no][1], voice, wav)
        else:
            add_noise(AUDIO / f"{no:02d}-{voice}-clean.wav", wav, seed=1000 * VOICES.index(voice) + no)
    rumble(done())
    whisper(done())


if __name__ == "__main__":
    main()
