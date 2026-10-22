"""Generate the voice-over track from audio/voiceover.json, with Kokoro (open-weight TTS, runs locally)
or with Oliver's cloned voice in VoiceStudio.

    pip install kokoro-onnx soundfile numpy
    # model files: github.com/thewh1teagle/kokoro-onnx/releases (model-files-v1.0)
    python scripts/make_voiceover.py --model kokoro-v1.0.onnx --voices voices-v1.0.bin

    # Oliver's cloned voice (VoiceStudio running locally; see voicestudio.py)
    python scripts/make_voiceover.py --engine voicestudio --config ... --out ...

Writes audio/voiceover.wav (44.1 kHz mono, full video length) and prints where each line lands.
Lines are laid out at 24 kHz (Kokoro's native rate, and the rate VoiceStudio's pcm output uses) and the
whole track is resampled once with ffmpeg's soxr (band-limited), which avoids the metallic aliasing a plain
linear interpolation adds to the voice.
A line too long for its window is re-synthesised slightly faster (max 1.15x) rather than overlapping the next
scene; with VoiceStudio, if the engine doesn't honour the speed, the clip is time-stretched with ffmpeg's atempo
(same 1.15x cap).
"""
import argparse, json, pathlib, subprocess, sys, tempfile
import numpy as np
import soundfile as sf

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

ap = argparse.ArgumentParser()
ap.add_argument("--engine", choices=["kokoro", "voicestudio"], default="kokoro")
ap.add_argument("--model", help="Kokoro model file (kokoro engine)")
ap.add_argument("--voices", help="Kokoro voices file (kokoro engine)")
ap.add_argument("--length", type=float, help="total track length in seconds (default: the config's length, else 56.5)")
ap.add_argument("--config", default="audio/voiceover.json")
ap.add_argument("--out", default="audio/voiceover.wav")
ap.add_argument("--voice", help="override the voice: a Kokoro voice (e.g. af_heart) or a VoiceStudio profile name")
ap.add_argument("--vs-engine", help="VoiceStudio engine: voxcpm2, cosyvoice or pockettts (default VOICESTUDIO_ENGINE, else voxcpm2)")
a = ap.parse_args()

cfg = json.loads((ROOT / a.config).read_text())
length = a.length or cfg.get("length") or 56.5
SR = 24000

if a.engine == "kokoro":
    if not (a.model and a.voices):
        ap.error("the kokoro engine needs --model and --voices")
    from kokoro_onnx import Kokoro
    voice = a.voice or cfg["voice"]
    tts = Kokoro(a.model, a.voices)

    def synth(text, speed):
        pcm, sr = tts.create(text, voice=voice, speed=speed, lang="en-us")
        assert sr == SR
        return pcm
else:
    import voicestudio
    try:
        vs = voicestudio.Client(engine=a.vs_engine, voice=a.voice)
        vs.check()
    except voicestudio.VoiceStudioError as e:
        sys.exit(f"VoiceStudio: {e}")
    voice = f"{vs.voice} ({vs.engine}, VoiceStudio)"

    def synth(text, speed):
        try:
            return vs.speak(text, speed)
        except voicestudio.VoiceStudioError as e:
            sys.exit(f"VoiceStudio: {e}")


def stretch(pcm, factor):
    """Speed a clip up by `factor` without changing pitch (ffmpeg atempo)."""
    with tempfile.TemporaryDirectory() as d:
        src, dst = pathlib.Path(d) / "in.wav", pathlib.Path(d) / "out.wav"
        sf.write(src, pcm, SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", f"atempo={factor:.4f}",
                        "-c:a", "pcm_f32le", str(dst)], check=True)
        out, _ = sf.read(dst, dtype="float32")
    return out

def say(text, speed):
    pcm = np.asarray(synth(text, speed), np.float32)
    # trim leading/trailing silence so 'at' is when the voice actually starts
    idx = np.flatnonzero(np.abs(pcm) > 0.01)
    pcm = pcm[max(idx[0] - int(0.02 * SR), 0): idx[-1] + int(0.08 * SR)].astype(np.float32)
    # 5 ms fades so trimmed edges never click
    f = np.linspace(0, 1, int(0.005 * SR), dtype=np.float32)
    pcm[: len(f)] *= f; pcm[-len(f):] *= f[::-1]
    return pcm

track = np.zeros(int(length * SR), np.float32)
cursor = 0.0
timings = []
for ln in cfg["lines"]:
    speed = cfg["speed"]
    clip = say(ln["text"], speed)
    start = max(ln["at"], cursor + 0.25)
    room = ln["by"] - start
    if len(clip) / SR > room:
        first = len(clip)
        speed = min(1.15, speed * (len(clip) / SR) / room)
        clip = say(ln["text"], speed)
        # VoiceStudio engines may ignore `speed`: make up the rest with a time-stretch, keeping the 1.15x total cap
        # (Kokoro is left as it always was, so existing voice-overs regenerate identically)
        factor = min(1.15 * len(clip) / first, (len(clip) / SR) / room)
        if a.engine == "voicestudio" and factor > 1.01:
            clip = stretch(clip, factor)
    s = int(start * SR)
    track[s:s + len(clip)] += clip[: len(track) - s]
    cursor = start + len(clip) / SR
    timings.append({"t0": round(start, 2), "t1": round(cursor, 2), "text": ln["text"]})
    flag = "  <-- overruns" if cursor > ln["by"] + 0.05 else ""
    print(f"{start:5.2f}-{cursor:5.2f}s  x{speed:.2f}  {ln['text']}{flag}")

track /= max(1e-6, np.abs(track).max()) / 0.89
with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
    sf.write(tmp.name, track, SR, subtype="FLOAT")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp.name, "-af", "aresample=44100:resampler=soxr:precision=28",
                    "-c:a", "pcm_s16le", str(ROOT / a.out)], check=True)
(ROOT / a.out).with_suffix(".timings.json").write_text(json.dumps(timings, indent=1))
print("wrote", a.out, f"({voice}) and its .timings.json (caption times)")
