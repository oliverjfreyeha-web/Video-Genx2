"""Compose the explainer's music bed procedurally (original, royalty-free): warm pad, round bass,
soft plucked arpeggio with echo, light kick and shaker. 92 BPM, D major, I–vi–IV–V in 2-bar chords.

    python scripts/make_music.py --length 56.5   -> audio/music.wav (44.1 kHz stereo)

Arrangement follows the video: pad alone under the title card, rhythm enters with the first scene,
drums drop out for the end card and the pad rings out.
"""
import argparse, pathlib
import numpy as np
import soundfile as sf

ROOT = pathlib.Path(__file__).resolve().parent.parent
SR = 44100
ap = argparse.ArgumentParser()
ap.add_argument("--length", type=float, default=56.5)
ap.add_argument("--outro", type=float, default=51.5, help="when the drums drop out for the end card")
ap.add_argument("--bpm", type=float, default=92)
ap.add_argument("--transpose", type=int, default=0, help="shift every note by this many semitones")
ap.add_argument("--out", default="audio/music.wav")
a = ap.parse_args()

N = int(a.length * SR)
t = np.arange(N) / SR
BPM = a.bpm
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(7)
hz = lambda m: 440.0 * 2 ** ((m + a.transpose - 69) / 12)

# I–vi–IV–V with added 9ths/7ths (MIDI notes); 2 bars each
CHORDS = [
    (50, [62, 66, 69, 73, 76]),   # Dmaj9
    (47, [62, 66, 69, 71, 73]),   # Bm9 (voiced over D)
    (43, [62, 67, 71, 74, 78]),   # Gmaj7(9)
    (45, [61, 64, 69, 71, 76]),   # A6/9
]
chord_at = lambda sec: CHORDS[int(sec // (2 * BAR)) % len(CHORDS)]

L = np.zeros(N); R = np.zeros(N)

def add(sig, start, gain=1.0, pan=0.0):
    s = int(start * SR)
    if s < 0: sig, s = sig[-s:], 0
    if s >= N: return
    e = min(N, s + len(sig))
    L[s:e] += sig[: e - s] * gain * (1 - pan) / 2 * 2 ** 0.5
    R[s:e] += sig[: e - s] * gain * (1 + pan) / 2 * 2 ** 0.5

def tone(f, dur, harm=(1.0,), decay=0.0, attack=0.005, detune=0.0):
    n = int(dur * SR); x = np.arange(n) / SR
    out = sum(h * np.sin(2 * np.pi * f * (i + 1) * x * (1 + detune)) for i, h in enumerate(harm))
    env = np.minimum(1, x / attack) * (np.exp(-decay * x) if decay else 1)
    return out * env

# --- pad: band-limited saw-ish additive voices, slow swells, crossfading chords ---
seg = 2 * BAR
for k in range(int(a.length / seg) + 1):
    root, notes = CHORDS[k % len(CHORDS)]
    dur = seg + 1.6
    n = int(dur * SR); x = np.arange(n) / SR
    env = np.minimum(1, x / 1.2) * np.minimum(1, np.maximum(0, (dur - x) / 1.6))
    for j, m in enumerate(notes):
        for d, pan in ((-0.0025, -0.6), (0.0025, 0.6)):
            f = hz(m - 12) * (1 + d)
            v = sum(np.sin(2 * np.pi * f * h * x + rng.uniform(0, 6.28)) / h ** 1.6 for h in range(1, 7))
            add(v * env * (1 + 0.15 * np.sin(2 * np.pi * 0.17 * x + j)), k * seg - 0.4, 0.035, pan)

intro_end, outro_start = 2.5, a.outro

# --- bass: round sine + a little 2nd harmonic on beats 1 and 3 ---
b = intro_end
while b < outro_start:
    root, _ = chord_at(b)
    for off, dur in ((0, 1.7 * BEAT), (2 * BEAT, 1.7 * BEAT)):
        add(tone(hz(root - 12), dur, (1.0, 0.25), decay=1.2, attack=0.01), b + off, 0.11)
    b += BAR

# --- plucked arpeggio (8ths) with a dotted-8th echo; enters with scene 0 ---
step = BEAT / 2
pat = [0, 2, 4, 1, 3, 2, 4, 1]
i = 0; p = intro_end
while p < outro_start:
    _, notes = chord_at(p)
    m = notes[pat[i % 8]] + 12
    pl = tone(hz(m), 1.2, (1.0, 0.35, 0.12), decay=5.5, attack=0.003)
    pan = 0.35 * np.sin(i * 0.9)
    vel = 0.07 * (1.0 if i % 2 == 0 else 0.72)
    add(pl, p, vel, pan)
    add(pl, p + 0.75 * BEAT, vel * 0.35, -pan)
    add(pl, p + 1.5 * BEAT, vel * 0.14, pan)
    i += 1; p += step

# --- soft kick on 1 and 3 and shaker on the off-beats, from bar 2 of the scenes ---
def kick():
    n = int(0.35 * SR); x = np.arange(n) / SR
    f = 42 + 70 * np.exp(-x * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9)

def shaker():
    n = int(0.09 * SR); x = np.arange(n) / SR
    w = np.diff(rng.standard_normal(n + 1))          # crude high-pass
    return w * np.exp(-x * 45) * np.minimum(1, x / 0.004)

d = intro_end + BAR
while d < outro_start - 0.2:
    for off in (0, 2 * BEAT):
        add(kick(), d + off, 0.16)
    for off in (0.5, 1.5, 2.5, 3.5):
        add(shaker(), d + off * BEAT, 0.035, 0.3)
    d += BAR

# --- master: gentle fades, soft clip, normalise ---
fade = np.minimum(1, t / 1.5) * np.minimum(1, np.maximum(0, (a.length - t) / 3.0))
mix = np.stack([L, R], 1) * fade[:, None]
mix = np.tanh(mix * 1.6) / 1.6
mix /= np.abs(mix).max() / 0.89
sf.write(ROOT / a.out, mix.astype(np.float32), SR, subtype="PCM_16")
print("wrote", a.out, f"{a.length}s")
