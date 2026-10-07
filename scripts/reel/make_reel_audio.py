"""Build the reel's voice track and caption timings.

First half: new narration (Kokoro, same voice as the explainer) over the version-by-version progression.
Second half: the explainer's own narration, cut from audio/voiceover.wav at the same times as the Ocean clips.

    python scripts/reel/make_reel_audio.py --model kokoro-v1.0.onnx --voices voices-v1.0.bin
      -> renders/reel/reel-vo.wav, renders/reel/reel-data.js (caption timings for reel.html)
"""
import argparse, json, pathlib
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "renders/reel"
SR = 44100
LENGTH = 61.1

# (reel start, must end by, text)
NEW_LINES = [
    (0.3, 2.45, "One explainer. Five makeovers."),
    (2.8, 6.9, "It started as a simple animated draft."),
    (7.3, 11.4, "An animation audit smoothed every move."),
    (11.8, 15.9, "Then a print-style redesign."),
    (16.3, 20.4, "Then liquid glass, in bright color."),
    (20.8, 24.9, "Then Midnight. Dark, and neon."),
    (25.1, 26.45, "And now, Ocean."),
]
# (reel start, explainer video start, duration) — must match the Ocean clips in reel.html
CUTS = [(26.5, 7.5, 6), (32.5, 13.5, 6), (38.5, 26.5, 6), (44.5, 32.5, 6), (50.5, 44.5, 7), (57.5, 51.5, 3.6)]

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--voices", required=True)
a = ap.parse_args()
OUT.mkdir(parents=True, exist_ok=True)
tts = Kokoro(a.model, a.voices)
voice = json.loads((ROOT / "audio/voiceover.json").read_text())

def say(text, speed=1.0):
    pcm, sr = tts.create(text, voice=voice["voice"], speed=speed, lang="en-us")
    idx = np.flatnonzero(np.abs(pcm) > 0.01)
    pcm = pcm[max(idx[0] - int(0.02 * sr), 0): idx[-1] + int(0.08 * sr)]
    n = int(len(pcm) * SR / sr)
    return np.interp(np.linspace(0, len(pcm) - 1, n), np.arange(len(pcm)), pcm).astype(np.float32)

track = np.zeros(int(LENGTH * SR), np.float32)
caps = []
for start, by, text in NEW_LINES:
    clip = say(text)
    if len(clip) / SR > by - start:
        clip = say(text, min(1.2, (len(clip) / SR) / (by - start)))
    s = int(start * SR)
    track[s:s + len(clip)] += clip * 0.89 / max(1e-6, np.abs(clip).max())
    caps.append({"t0": start, "t1": start + len(clip) / SR, "text": text})
    print(f"{start:5.2f}-{start + len(clip) / SR:5.2f}  {text}")

vo, sr = sf.read(ROOT / "audio/voiceover.wav", dtype="float32")
lines = [l["text"] for l in voice["lines"]]
for reel_t, vid_t, dur in CUTS:
    seg = vo[int(vid_t * sr): int((vid_t + dur) * sr)]
    s = int(reel_t * SR)
    track[s:s + len(seg)] += seg[: len(track) - s]
    # caption = the explainer line whose speech falls inside this cut
    idx = np.flatnonzero(np.abs(seg) > 0.02)
    t0, t1 = reel_t + idx[0] / sr, reel_t + idx[-1] / sr
    text = next(l["text"] for l in voice["lines"] if vid_t - 0.2 <= l["at"] < vid_t + dur)
    caps.append({"t0": round(t0, 2), "t1": round(t1, 2), "text": text})
    print(f"{t0:5.2f}-{t1:5.2f}  {text}")

sf.write(OUT / "reel-vo.wav", track, SR, subtype="PCM_16")
(OUT / "reel-data.js").write_text("window.REEL_CAPTIONS = " + json.dumps(caps, indent=1) + ";\n")
print("wrote renders/reel/reel-vo.wav and reel-data.js")
