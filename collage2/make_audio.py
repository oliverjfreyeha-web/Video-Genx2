"""Score + sound design for collage spot #2 ("First Reply Wins"), on the same cue sheet as collage2.html.

    python collage2/make_audio.py --model kokoro-v1.0.onnx --voices voices-v1.0.bin

Writes collage2/mouth.json ({"cat": [...], "house": [...]} mouth openness per 1/12 s) and collage2/audio_mix.wav
(48 kHz stereo, unmastered). Mastering to -14 LUFS / -1 dBTP is done with ffmpeg afterwards. All sound is synthesised.
"""
import argparse, json, pathlib
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = pathlib.Path(__file__).resolve().parent
SR, DUR = 48000, 10.0
N = int(SR * DUR)
CUE = dict(slap=0, newLead=.333, ring1=.667, ring2=1.0, hello=.9, comp=1.333, clock=2.0, snip1=2.667, snip2=3.0,
           ours=3.333, oursLine=3.5, stamp=4.0, yes=4.667, rattle=5.333, pop=6.0, wins=7.333, rip=8.0, land=8.667)
BPM = 90; BEAT = 60 / BPM; BAR = 4 * BEAT
ap = argparse.ArgumentParser(); ap.add_argument('--model'); ap.add_argument('--voices'); a = ap.parse_args()
rng = np.random.default_rng(5)
L = np.zeros(N); R = np.zeros(N)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)


def add(sig, t, g=1., pan=0.):
    s = int(t * SR)
    if s >= N or s < 0: return
    sig = sig[: N - s]
    L[s:s + len(sig)] += sig * g * (1 - pan)
    R[s:s + len(sig)] += sig * g * (1 + pan)


def env(n, at, dec): x = np.arange(n) / SR; return np.minimum(1, x / at) * np.exp(-x * dec)
def noise(n): return rng.standard_normal(n)
def bp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x))


# ---------- voices: the cat (the lead) and our house; each drives its own mouth ----------
tts = Kokoro(a.model, a.voices)
def say(text, voice, speed=1.0):
    pcm, sr = tts.create(text, voice=voice, speed=speed, lang='en-us')
    idx = np.flatnonzero(np.abs(pcm) > .01); pcm = pcm[idx[0]: idx[-1] + int(.05 * sr)]
    n = int(len(pcm) * SR / sr); pcm = np.interp(np.linspace(0, len(pcm) - 1, n), np.arange(len(pcm)), pcm)
    return pcm / np.abs(pcm).max()
tracks = {'cat': np.zeros(N), 'house': np.zeros(N), 'vo': np.zeros(N)}
for who, text, t, v, sp in [('cat', 'Hello? Anyone?', CUE['hello'], 'af_bella', 1.05), ('house', 'Hi! Free at ten?', CUE['oursLine'] + .05, 'am_michael', 1.08),
                            ('cat', 'Yes!', CUE['yes'] + .05, 'af_bella', 1.0), ('vo', 'Elevate Home Ads.', CUE['land'] + .1, 'af_heart', 1.0)]:
    pcm = say(text, v, sp); s = int(t * SR); tracks[who][s:s + len(pcm)] += pcm[: N - s]
mouth = {}
for who in ('cat', 'house'):
    m = []
    for k in range(int(DUR * 12)):
        seg = tracks[who][int(k / 12 * SR): int((k + 1) / 12 * SR)]
        rms = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0
        m.append(0 if rms < .05 else (2 if rms > .2 else 1))
    mouth[who] = m
(ROOT / 'mouth.json').write_text(json.dumps(mouth))
for who in tracks: add(tracks[who], 0, .5)
print('VO end', np.flatnonzero(np.abs(tracks['vo']) > .02)[-1] / SR)

# ---------- music: boom-bap at 90 BPM, Cm9 – F13, drums out for the lid rattle, back on the POP ----------
def kick():
    n = int(.35 * SR); x = np.arange(n) / SR; f = 50 + 110 * np.exp(-x * 35)
    return np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9))
def snare():
    n = int(.3 * SR); x = np.arange(n) / SR
    return (bp(noise(n), 1200, 9000) * .8 + np.sin(2 * np.pi * 185 * x) * .5) * np.exp(-x * 16)
def hat(o=False):
    n = int((.18 if o else .05) * SR); return bp(noise(n), 6000, 16000) * np.exp(-np.arange(n) / SR * (14 if o else 70))
def rhodes(m, d):
    n = int(d * SR); x = np.arange(n) / SR; f = hz(m)
    mod = np.sin(2 * np.pi * f * x) * 1.6 * np.exp(-x * 4)
    return (np.sin(2 * np.pi * f * x + mod) + .3 * np.sin(2 * np.pi * 2 * f * x)) * env(n, .005, 1.8) * (1 + .15 * np.sin(2 * np.pi * 5 * x))
CH = [(36, [51, 55, 58, 62]), (41, [51, 57, 62, 67])]   # Cm9, F13
drums = lambda t: not (CUE['rattle'] <= t < CUE['pop']) and t < CUE['land'] + 1.0
t = 0.0; bar = 0
while t < DUR:
    root, notes = CH[bar % 2]
    for off, g in ((0, .035), (2.5 * BEAT, .025)):
        if t + off < DUR - .2:
            for j, m in enumerate(notes): add(rhodes(m, 2.2), t + off + j * .012, g, (j - 1.5) * .3)
    for b, iv, d in ((0, 0, .9), (1.5, 7, .4), (2, 12, .5), (3, 10, .6), (3.5, 7, .3)):
        tb = t + b * BEAT
        if tb < DUR - .3:
            n = int(d * SR); x = np.arange(n) / SR
            add(np.tanh(1.8 * np.sin(2 * np.pi * hz(root + iv - 12) * x)) * env(n, .008, 3.5), tb, .07)
    for b in range(4):
        tb = t + b * BEAT
        if drums(tb):
            if b == 0: add(kick(), tb, .25)
            if b == 2: add(kick(), tb + .5 * BEAT, .21)
            if b in (1, 3): add(snare(), tb + .015, .13, -.1)
            for e in (0, 1): add(hat(b == 3 and e == 1), tb + e * BEAT * .58, .035 if e else .05, .3)
    t += BAR; bar += 1
add(kick(), CUE['pop'], .35); add(snare(), CUE['pop'], .15)

# ---------- foley on the cue sheet ----------
def slapfx(g=1.):
    n = int(.25 * SR); x = np.arange(n) / SR
    return (bp(noise(n), 300, 6000) * np.exp(-x * 38) * 1.2 + np.sin(2 * np.pi * 90 * x) * np.exp(-x * 25)) * g
def rustle(d=.35):
    n = int(d * SR); e = np.abs(np.sin(np.linspace(0, np.pi, n))) * (.5 + .5 * np.abs(bp(noise(n), 2, 30)))
    return bp(noise(n), 1500, 9000) * e * .5
def snip():
    n = int(.12 * SR); x = np.arange(n) / SR
    return (np.sin(2 * np.pi * 3300 * x) + .6 * np.sin(2 * np.pi * 5200 * x)) * np.exp(-x * 60) * .5 + bp(noise(n), 4000, 12000) * np.exp(-x * 90) * .5
def bell(d=.55):          # old telephone bell: two detuned partials with a fast tremolo
    n = int(d * SR); x = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1180 * x) + .7 * np.sin(2 * np.pi * 1640 * x)) * (.55 + .45 * np.sign(np.sin(2 * np.pi * 22 * x))) * env(n, .002, 3) * .5
def snore(d=.7):
    n = int(d * SR); x = np.arange(n) / SR
    return bp(noise(n), 80, 600) * np.sin(np.pi * x / d) ** 2 * (1 + .6 * np.sin(2 * np.pi * 28 * x)) * .7
def tick():
    n = int(.03 * SR); return bp(noise(n), 2000, 7000) * np.exp(-np.arange(n) / SR * 200)
def pop():
    n = int(.35 * SR); x = np.arange(n) / SR; f = 900 * np.exp(-x * 9) + 180
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9) + bp(noise(n), 2000, 8000) * np.exp(-x * 60) * .4
def whoosh(d=.6, lo=300, hi=3000):
    n = int(d * SR); return bp(noise(n), lo, hi) * np.sin(np.linspace(0, np.pi, n)) ** 2
def rip(d=.65):          # tearing paper: noise with fast irregular amplitude bursts
    n = int(d * SR); x = np.arange(n) / SR
    am = np.clip(bp(noise(n), 20, 120) * 4, 0, 1)
    return bp(noise(n), 900, 7000) * am * np.minimum(1, x / .03) * np.exp(-x * 1.5)
add(slapfx(1.1), CUE['slap']); add(slapfx(.85), CUE['newLead'])
add(bell(), CUE['ring1'], .55, .3); add(bell(), CUE['ring2'], .55, .35)
for i in range(3): add(slapfx(.6), CUE['comp'] + i * .167, 1, .3); add(snore(), CUE['comp'] + .5 + i * .3, .35, .4)
add(slapfx(.7), CUE['clock'])
for k in range(8): add(tick(), CUE['clock'] + .05 + k / 12, .5, .5)
add(snip(), CUE['snip1']); add(snip(), CUE['snip1'] + .085); add(snip(), CUE['snip2']); add(rustle(.45), CUE['snip2'] + .05, .5, .4)
add(slapfx(1.0), CUE['ours'], 1, .3); add(slapfx(.6), CUE['oursLine'], 1, .2); add(slapfx(.9), CUE['stamp'], 1, .2)
add(slapfx(.7), CUE['yes'], 1, -.3)
for i in range(8): add(rustle(.08), CUE['rattle'] + i / 12, .3, -.3)
add(pop(), CUE['pop'], .9, -.2); add(whoosh(1.0, 200, 2500), CUE['pop'] + .05, .5, -.1)
for i in range(4): add(whoosh(.18, 800, 5000), CUE['pop'] + .2 + i * .17, .25, .2)
for i in range(5): add(np.sin(2 * np.pi * 2400 * np.arange(int(.08 * SR)) / SR) * np.exp(-np.arange(int(.08 * SR)) / SR * 40) * .4, CUE['pop'] + .06 + i * .06, .5, -.2)   # coin clinks
add(slapfx(.6), CUE['pop'] + .5, 1, .4)
add(slapfx(1.0), CUE['wins'])
add(rip(), CUE['rip'], 1.0); add(rustle(.5), CUE['rip'] + .3, .6)
add(kick(), CUE['land'], .35); add(slapfx(.6), CUE['land'], .9)
for tk in (.17, .33, .5): add(slapfx(.5), CUE['land'] + tk, 1)
cr = np.zeros(N); idx = rng.integers(0, N, 1400); cr[idx] = rng.standard_normal(1400) * (rng.random(1400) ** 3) * 2
cr = np.convolve(cr, np.exp(-np.arange(60) / 8), 'same'); hiss = bp(noise(N), 3000, 12000) * .012
add(cr * .25 + hiss, 0, .5)
fade = np.ones(N); fade[-int(.35 * SR):] = np.linspace(1, 0, int(.35 * SR)) ** 1.5
mix = np.stack([L, R], 1) * fade[:, None]
mix /= np.abs(mix).max() / .9
sf.write(ROOT / 'audio_mix.wav', mix.astype(np.float32), SR, subtype='FLOAT')
print('wrote audio_mix.wav and mouth.json')
