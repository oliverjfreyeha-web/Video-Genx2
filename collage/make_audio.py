"""Score + sound design for the 10 s collage spot, locked to the same cue sheet as collage.html.

    python collage/make_audio.py --model kokoro-v1.0.onnx --voices voices-v1.0.bin

Writes collage/mouth.json (mouth openness per 1/12 s from the voice), collage/audio_mix.wav (48 kHz stereo, unmastered).
Mastering to -14 LUFS / -1 dBTP is done with ffmpeg (see collage/README.md). Everything is synthesised here.
"""
import argparse, json, pathlib
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = pathlib.Path(__file__).resolve().parent
SR, DUR = 48000, 10.0
N = int(SR * DUR)
CUE = dict(slap=0, sixty=.333, voice1=.70, rain=.667, twoJobs=2.0, snip1=2.667, snip2=3.0, s1=3.333, s2=4.0, s3=4.667,
           rattle=5.333, pop=6.0, more=7.333, flip=8.0, land=8.667)
BPM = 90; BEAT = 60 / BPM; BAR = 4 * BEAT
ap = argparse.ArgumentParser(); ap.add_argument('--model'); ap.add_argument('--voices'); a = ap.parse_args()
rng = np.random.default_rng(3)
L = np.zeros(N); R = np.zeros(N)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)


def add(sig, t, g=1., pan=0.):
    s = int(t * SR)
    if s >= N: return
    sig = sig[: N - s]
    L[s:s + len(sig)] += sig * g * (1 - pan) * .7071 * 1.414 / 2 * 2
    R[s:s + len(sig)] += sig * g * (1 + pan) * .7071 * 1.414 / 2 * 2


def env(n, at, dec): x = np.arange(n) / SR; return np.minimum(1, x / at) * np.exp(-x * dec)
def noise(n): return rng.standard_normal(n)
def bp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x))


# ---------- voice (the house head talks; its door-mouth flaps from this) ----------
tts = Kokoro(a.model, a.voices)
def say(text, t, voice='am_michael', speed=1.08, g=1.0):
    pcm, sr = tts.create(text, voice=voice, speed=speed, lang='en-us')
    idx = np.flatnonzero(np.abs(pcm) > .01); pcm = pcm[idx[0]: idx[-1] + int(.05 * sr)]
    n = int(len(pcm) * SR / sr); pcm = np.interp(np.linspace(0, len(pcm) - 1, n), np.arange(len(pcm)), pcm)
    pcm /= np.abs(pcm).max(); return pcm, t
voice = np.zeros(N)
for text, t, v, sp in [('Sixty leads...', CUE['voice1'], 'am_michael', 1.0), ('Two jobs?!', CUE['twoJobs'] + .06, 'am_michael', 1.0),
                       ('Elevate Home Ads.', CUE['land'] + .05, 'af_heart', 1.0)]:
    pcm, t0 = say(text, t, v, sp); s = int(t0 * SR); voice[s:s + len(pcm)] += pcm[: N - s]
# mouth: openness per 1/12 s for the house's lines only (before the flip)
mouth = []
for k in range(int(DUR * 12)):
    seg = voice[int(k / 12 * SR): int((k + 1) / 12 * SR)]
    rms = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0
    mouth.append(0 if rms < .05 or k / 12 > CUE['flip'] else (2 if rms > .2 else 1))
(ROOT / 'mouth.json').write_text(json.dumps(mouth))
add(voice, 0, .9)

# ---------- music: jazzy boom-bap, 90 BPM, Dm9 – G13, drums out for the anticipation, back on the POP ----------
def kick():
    n = int(.35 * SR); x = np.arange(n) / SR; f = 50 + 110 * np.exp(-x * 35)
    return np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9))
def snare():
    n = int(.3 * SR); x = np.arange(n) / SR
    return (bp(noise(n), 1200, 9000) * .8 + np.sin(2 * np.pi * 190 * x) * .5) * np.exp(-x * 16)
def hat(o=False):
    n = int((.18 if o else .05) * SR); return bp(noise(n), 6000, 16000) * np.exp(-np.arange(n) / SR * (14 if o else 70))
def rhodes(m, d):
    n = int(d * SR); x = np.arange(n) / SR; f = hz(m)
    mod = np.sin(2 * np.pi * f * x) * 1.6 * np.exp(-x * 4)
    return (np.sin(2 * np.pi * f * x + mod) + .3 * np.sin(2 * np.pi * 2 * f * x)) * env(n, .005, 1.8) * (1 + .15 * np.sin(2 * np.pi * 5 * x))
CH = [(38, [53, 57, 60, 64]), (43, [53, 59, 64, 69])]   # Dm9, G13 voicings
drums = lambda t: not (CUE['rattle'] <= t < CUE['pop']) and t < CUE['land'] + 1.0
t = 0.0; bar = 0
while t < DUR:
    root, notes = CH[bar % 2]
    for off, g in ((0, .07), (2.5 * BEAT, .05)):
        if t + off < DUR - .2:
            for j, m in enumerate(notes): add(rhodes(m, 2.2), t + off + j * .012, g, (j - 1.5) * .3)
    for b, iv, d in ((0, 0, .9), (1.5, 7, .4), (2, 12, .5), (3, 10, .6), (3.5, 7, .3)):   # upright-ish bass
        tb = t + b * BEAT
        if tb < DUR - .3:
            n = int(d * SR); x = np.arange(n) / SR
            add(np.tanh(1.8 * np.sin(2 * np.pi * hz(root + iv - 12) * x)) * env(n, .008, 3.5), tb, .14)
    for b in range(4):
        tb = t + b * BEAT
        if drums(tb):
            if b in (0,): add(kick(), tb, .5)
            if b == 2: add(kick(), tb + .5 * BEAT, .42)
            if b in (1, 3): add(snare(), tb + .015, .26, -.1)
            for e in (0, 1): add(hat(b == 3 and e == 1), tb + e * BEAT * .58, .07 if e else .1, .3)
    t += BAR; bar += 1
add(kick(), CUE['pop'], .7); add(snare(), CUE['pop'], .3)   # downbeat back in on the hero hit

# ---------- foley, on the cue sheet ----------
def slapfx(g=1.):
    n = int(.25 * SR); x = np.arange(n) / SR
    return (bp(noise(n), 300, 6000) * np.exp(-x * 38) * 1.2 + np.sin(2 * np.pi * 90 * x) * np.exp(-x * 25)) * g
def rustle(d=.35):
    n = int(d * SR); e = np.abs(np.sin(np.linspace(0, np.pi, n))) * (.5 + .5 * np.abs(bp(noise(n), 2, 30)))
    return bp(noise(n), 1500, 9000) * e * .5
def snip():
    n = int(.12 * SR); x = np.arange(n) / SR
    return (np.sin(2 * np.pi * 3300 * x) + .6 * np.sin(2 * np.pi * 5200 * x)) * np.exp(-x * 60) * .5 + bp(noise(n), 4000, 12000) * np.exp(-x * 90) * .5
def pop():
    n = int(.35 * SR); x = np.arange(n) / SR; f = 900 * np.exp(-x * 9) + 180
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9) + bp(noise(n), 2000, 8000) * np.exp(-x * 60) * .4
def whoosh(d=.6, lo=300, hi=3000):
    n = int(d * SR); return bp(noise(n), lo, hi) * np.sin(np.linspace(0, np.pi, n)) ** 2
add(slapfx(1.1), CUE['slap']); add(slapfx(.8), CUE['sixty']); add(slapfx(.95), CUE['twoJobs'])
for i in range(14): add(rustle(.18), CUE['rain'] + i * .083, .25, (i % 5 - 2) * .2)
add(snip(), CUE['snip1']); add(snip(), CUE['snip1'] + .085); add(snip(), CUE['snip2']); add(rustle(.4), CUE['snip2'] + .05, .5, -.4)
for k, tk in enumerate((CUE['s1'], CUE['s2'], CUE['s3'])): add(slapfx(.85), tk, 1, -.3 + k * .1); add(rustle(.2), tk - .16, .35)
for i in range(8): add(rustle(.08), CUE['rattle'] + i / 12, .3)          # lid rattle
add(pop(), CUE['pop'], .9); add(whoosh(1.0, 200, 2500), CUE['pop'] + .05, .5, .1)   # comic pop + rocket
for i in range(4): add(whoosh(.18, 800, 5000), CUE['pop'] + .2 + i * .17, .25, .4)   # wing flaps
add(slapfx(.6), CUE['pop'] + .5); add(slapfx(.6), CUE['pop'] + .62)
add(slapfx(1.0), CUE['more']); add(slapfx(.6), CUE['more'] + .25)
add(whoosh(.7, 150, 4000), CUE['flip'], .9); add(rustle(.6), CUE['flip'] + .05, .8)
add(kick(), CUE['land'], .55); add(slapfx(.6), CUE['land'], .9)
for tk in (.08, .25, .42): add(slapfx(.55), CUE['land'] + tk, 1)
# vinyl crackle bed throughout
cr = np.zeros(N); idx = rng.integers(0, N, 1400); cr[idx] = rng.standard_normal(1400) * (rng.random(1400) ** 3) * 2
cr = np.convolve(cr, np.exp(-np.arange(60) / 8), 'same'); hiss = bp(noise(N), 3000, 12000) * .012
add(cr * .25 + hiss, 0, 1)
# soft end: everything fades out over the last 0.4 s except a final crackle tail
fade = np.ones(N); fade[-int(.4 * SR):] = np.linspace(1, 0, int(.4 * SR)) ** 1.5
mix = np.stack([L, R], 1) * fade[:, None]
mix /= np.abs(mix).max() / .9
sf.write(ROOT / 'audio_mix.wav', mix.astype(np.float32), SR, subtype='FLOAT')
print('wrote audio_mix.wav and mouth.json')
