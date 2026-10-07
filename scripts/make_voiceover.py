"""Generate the voice-over track from audio/voiceover.json with Kokoro (open-weight TTS, runs locally).

    pip install kokoro-onnx soundfile numpy
    # model files: github.com/thewh1teagle/kokoro-onnx/releases (model-files-v1.0)
    python scripts/make_voiceover.py --model kokoro-v1.0.onnx --voices voices-v1.0.bin

Writes audio/voiceover.wav (44.1 kHz mono, full video length) and prints where each line lands.
A line too long for its window is re-synthesised slightly faster (max 1.15x) rather than overlapping the next scene.
"""
import argparse, json, pathlib
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = pathlib.Path(__file__).resolve().parent.parent
SR = 44100

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--voices", required=True)
ap.add_argument("--length", type=float, default=56.5, help="total track length in seconds")
ap.add_argument("--config", default="audio/voiceover.json")
ap.add_argument("--out", default="audio/voiceover.wav")
a = ap.parse_args()

cfg = json.loads((ROOT / a.config).read_text())
tts = Kokoro(a.model, a.voices)

def say(text, speed):
    pcm, sr = tts.create(text, voice=cfg["voice"], speed=speed, lang="en-us")
    # trim leading/trailing silence so 'at' is when the voice actually starts
    idx = np.flatnonzero(np.abs(pcm) > 0.01)
    pcm = pcm[max(idx[0] - int(0.02 * sr), 0): idx[-1] + int(0.08 * sr)]
    # resample 24 kHz -> 44.1 kHz (linear interpolation is fine for speech at this ratio)
    n = int(len(pcm) * SR / sr)
    return np.interp(np.linspace(0, len(pcm) - 1, n), np.arange(len(pcm)), pcm).astype(np.float32)

track = np.zeros(int(a.length * SR), np.float32)
cursor = 0.0
timings = []
for ln in cfg["lines"]:
    speed = cfg["speed"]
    clip = say(ln["text"], speed)
    start = max(ln["at"], cursor + 0.25)
    room = ln["by"] - start
    if len(clip) / SR > room:
        speed = min(1.15, speed * (len(clip) / SR) / room)
        clip = say(ln["text"], speed)
    s = int(start * SR)
    track[s:s + len(clip)] += clip[: len(track) - s]
    cursor = start + len(clip) / SR
    timings.append({"t0": round(start, 2), "t1": round(cursor, 2), "text": ln["text"]})
    flag = "  <-- overruns" if cursor > ln["by"] + 0.05 else ""
    print(f"{start:5.2f}-{cursor:5.2f}s  x{speed:.2f}  {ln['text']}{flag}")

track /= max(1e-6, np.abs(track).max()) / 0.89
sf.write(ROOT / a.out, track, SR, subtype="PCM_16")
(ROOT / a.out).with_suffix(".timings.json").write_text(json.dumps(timings, indent=1))
print("wrote", a.out, "and its .timings.json (caption times)")
