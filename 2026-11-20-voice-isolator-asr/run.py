"""Make the clips, clean every clip with Voice Isolator, then transcribe raw and cleaned clips with Whisper.

Speech: the 36 sentences of the 16 and 19 Nov tests, spoken by three macOS voices (Daniel en_GB, Samantha en_US,
Karen en_AU) through `say`, written at 48 kHz. Each clip comes three ways:
- clean;
- white noise at 5 dB SNR (as on 19 Nov), seeded per clip;
- babble at 0 dB SNR: four other macOS voices (Moira, Fred, Aman, Kathy) reading other sentences from the list at
  the same time, looped to the clip's length. A made-up crowd, so no real person's voice is used.
Every clip is then run through inworld/voice-isolator (offline model) and both versions go to
mlx-community/whisper-large-v3-turbo. Isolation runs first and Whisper after, because two models taking turns on
the GPU made every call slow (16 Nov lab). Finished clips and transcripts are skipped, so a cut-off run resumes.

    uv run run.py
"""
import json
import subprocess
import time
from pathlib import Path

import mlx_whisper
import numpy as np
import soundfile as sf
from inworld import voice_isolation

from items import ITEMS

HERE = Path(__file__).parent
AUDIO = HERE / "results" / "audio"
OUT = HERE / "results" / "transcripts.jsonl"
VOICES = ["Daniel", "Samantha", "Karen"]
CROWD = ["Moira", "Fred", "Aman", "Kathy"]
NOISES = {"clean": None, "white-5db": 5, "babble-0db": 0}
ISOLATOR = "inworld/voice-isolator"
WHISPER = "mlx-community/whisper-large-v3-turbo"
RATE = 48000


def speak(text, voice, out):
    aiff = out.with_suffix(".aiff")
    subprocess.run(["say", "-v", voice, "-o", str(aiff), text], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(aiff), "-ar", str(RATE), "-ac", "1", str(out)],
                   check=True)
    aiff.unlink()


def crowd(no, length):
    """Four other voices reading four other sentences at once, each looped to `length` samples."""
    total = np.zeros(length)
    for k, voice in enumerate(CROWD):
        wav = AUDIO / "crowd" / f"{no:02d}-{voice}.wav"
        if not wav.exists():
            speak(ITEMS[(no + 7 * (k + 1)) % len(ITEMS)][1], voice, wav)
        talk, _ = sf.read(wav)
        total += np.resize(talk, length)
    return total


def add_noise(no, voice, noise, out):
    speech, _ = sf.read(AUDIO / f"{no:02d}-{voice}-clean.wav")
    seed = 1000 * VOICES.index(voice) + no
    noise_wav = np.random.default_rng(seed).standard_normal(len(speech)) if noise == "white-5db" else crowd(no, len(speech))
    noise_wav *= np.sqrt(np.mean(speech ** 2) / (np.mean(noise_wav ** 2) * 10 ** (NOISES[noise] / 10)))
    mixed = speech + noise_wav
    sf.write(out, mixed / max(1.0, np.abs(mixed).max()), RATE)


def clips():
    for noise in NOISES:
        for voice in VOICES:
            for no in range(len(ITEMS)):
                yield noise, voice, no, AUDIO / f"{no:02d}-{voice}-{noise}.wav"


def isolated(wav):
    return wav.with_name(wav.stem + "-isolated.wav")


def done():
    if not OUT.exists():
        return set()
    return {(r["noise"], r["isolated"], r["voice"], r["no"]) for r in map(json.loads, OUT.open())}


def write(row):
    with OUT.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    (AUDIO / "crowd").mkdir(parents=True, exist_ok=True)
    for noise, voice, no, wav in clips():
        if wav.exists():
            continue
        if noise == "clean":
            speak(ITEMS[no][1], voice, wav)
        else:
            add_noise(no, voice, noise, wav)

    timing = HERE / "results" / "isolation_seconds.jsonl"
    model = None
    for noise, voice, no, wav in clips():
        if isolated(wav).exists():
            continue
        model = model or voice_isolation.VoiceIsolator(ISOLATOR)
        audio, rate = voice_isolation.load_audio(str(wav))
        start = time.time()
        clean = model.isolate(audio, rate)
        with timing.open("a") as f:
            f.write(json.dumps({"clip": wav.name, "seconds": round(time.time() - start, 3),
                                "audio_seconds": round(len(audio) / rate, 2)}) + "\n")
        voice_isolation.save_audio(str(isolated(wav)), clean, rate)
    del model

    seen = done()
    for noise, voice, no, wav in clips():
        for iso in (False, True):
            if (noise, iso, voice, no) in seen:
                continue
            start = time.time()
            path = isolated(wav) if iso else wav
            heard = mlx_whisper.transcribe(str(path), path_or_hf_repo=WHISPER, language="en", temperature=0.0)["text"]
            write({"noise": noise, "isolated": iso, "voice": voice, "no": no, "heard": heard.strip(),
                   "seconds": round(time.time() - start, 3)})


if __name__ == "__main__":
    main()
