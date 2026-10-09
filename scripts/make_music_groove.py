"""Compose a second, original music bed: an upbeat electric-piano groove (108 BPM, F major).

    python scripts/make_music_groove.py --length 57.5 --outro 51.5 --out audio/music-groove.wav

Electric-piano chords (FM-style), syncopated round bass, four-on-the-floor soft kick, claps on 2 and 4,
swung hi-hats, and a short marimba hook every two bars. Chords alone under the title card, drums out
for the end card. Royalty-free: everything is synthesised here.
"""
import argparse, pathlib
import numpy as np
import soundfile as sf

ROOT = pathlib.Path(__file__).resolve().parent.parent
SR = 44100
ap = argparse.ArgumentParser()
ap.add_argument("--length", type=float, default=57.5)
ap.add_argument("--intro", type=float, default=2.5, help="drums enter here")
ap.add_argument("--outro", type=float, default=51.5, help="drums drop out here")
ap.add_argument("--bpm", type=float, default=108)
ap.add_argument("--transpose", type=int, default=0, help="shift every note by this many semitones")
ap.add_argument("--out", default="audio/music-groove.wav")
a = ap.parse_args()

N = int(a.length * SR)
BPM = a.bpm
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(11)
hz = lambda m: 440.0 * 2 ** ((m + a.transpose - 69) / 12)
L = np.zeros(N); R = np.zeros(N)

def add(sig, start, gain=1.0, pan=0.0):
    s = int(start * SR)
    if s < 0: sig, s = sig[-s:], 0
    if s >= N: return
    e = min(N, s + len(sig))
    L[s:e] += sig[: e - s] * gain * (1 - pan) * .7071
    R[s:e] += sig[: e - s] * gain * (1 + pan) * .7071

def env(n, a_, d):
    x = np.arange(n) / SR
    return np.minimum(1, x / a_) * np.exp(-x * d)

# I – vi – IV – V-ish with colour: Fmaj7, Dm9, Bbmaj7, C6/9 (one bar each)
CHORDS = [(41, [57, 60, 64, 65]), (38, [57, 60, 62, 65]), (46, [58, 62, 65, 69]), (48, [55, 60, 62, 64])]
chord_at = lambda t: CHORDS[int(t // BAR) % 4]

def epiano(f, dur):
    n = int(dur * SR); x = np.arange(n) / SR
    mod = np.sin(2 * np.pi * f * 14 * x) * 1.2 * np.exp(-x * 9)          # bell-ish attack
    car = np.sin(2 * np.pi * f * x + mod) + .25 * np.sin(2 * np.pi * f * 2 * x)
    return car * env(n, .004, 1.6)

# electric piano: chord stabs on 1 and the "and" of 2, all the way through
t = 0.0
while t < a.length - 0.5:
    _, notes = chord_at(t)
    for off, g in ((0, .08), (1.5 * BEAT, .06), (3 * BEAT, .05)):
        for j, m in enumerate(notes):
            add(epiano(hz(m), 1.4), t + off + j * .008, g, (j - 1.5) * .25)
    t += BAR

drums_on = lambda t: a.intro <= t < a.outro

# bass: syncopated pattern on root and fifth
pat = [(0, 0, .45), (.75, 0, .2), (1.5, 7, .3), (2.5, 0, .35), (3.25, 12, .2), (3.5, 7, .25)]
t = a.intro
while t < a.outro:
    root, _ = chord_at(t)
    for b, iv, d in pat:
        n = int(d * BEAT * SR * 1.8); x = np.arange(n) / SR
        f = hz(root + iv - 12)
        s = np.tanh(1.6 * (np.sin(2 * np.pi * f * x) + .3 * np.sin(4 * np.pi * f * x))) * env(n, .006, 4)
        add(s, t + b * BEAT, .09)
    t += BAR

def kick():
    n = int(.3 * SR); x = np.arange(n) / SR
    f = 48 + 90 * np.exp(-x * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 11)

def clap():
    n = int(.18 * SR); x = np.arange(n) / SR
    w = np.diff(rng.standard_normal(n + 1)) * .5
    bursts = sum(np.exp(-np.maximum(0, x - k * .011) * 60) * (x >= k * .011) for k in range(3))
    return w * bursts * np.exp(-x * 14)

def hat(open_=False):
    n = int((.16 if open_ else .05) * SR); x = np.arange(n) / SR
    w = np.diff(np.diff(rng.standard_normal(n + 2)))
    return w * np.exp(-x * (18 if open_ else 70)) * .5

t = a.intro
while t < a.outro - .1:
    for b in range(4):
        add(kick(), t + b * BEAT, .13)
    for b in (1, 3):
        add(clap(), t + b * BEAT, .1, -.1)
    for k in range(8):                      # swung 8ths
        sw = .58 if k % 2 else 0
        add(hat(k == 7), t + (k // 2 + sw) * BEAT, .05 if k % 2 else .035, .35)
    t += BAR

# marimba hook every two bars (after the first 4 bars of groove)
hook = [(0, 72), (.5, 74), (1, 77), (2, 76), (2.5, 74), (3.5, 72)]
t = a.intro + 4 * BAR
while t < a.outro - 2 * BAR:
    for b, m in hook:
        n = int(.5 * SR); x = np.arange(n) / SR
        s = (np.sin(2 * np.pi * hz(m) * x) + .3 * np.sin(2 * np.pi * hz(m) * 3.9 * x) * np.exp(-x * 30)) * env(n, .002, 9)
        add(s, t + b * BEAT, .05, .3)
        add(s, t + b * BEAT + .75 * BEAT, .018, -.3)   # echo
    t += 2 * BAR

tt = np.arange(N) / SR
fade = np.minimum(1, tt / 1.2) * np.minimum(1, np.maximum(0, (a.length - tt) / 3.0))
mix = np.stack([L, R], 1) * fade[:, None]
mix = np.tanh(mix * 1.5) / 1.5
mix /= np.abs(mix).max() / 0.89
sf.write(ROOT / a.out, mix.astype(np.float32), SR, subtype="PCM_16")
print("wrote", a.out, f"{a.length}s @ {BPM} BPM")
