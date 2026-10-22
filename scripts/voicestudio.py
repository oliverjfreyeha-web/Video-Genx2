"""VoiceStudio client for the video pipeline: Oliver's cloned voice, as 24 kHz mono float32 clips.

VoiceStudio (github.com/debpalash/VoiceStudio) runs on the laptop (the setup script starts it in Docker on
127.0.0.1:3900). This talks to its OpenAI-compatible POST /v1/audio/speech and asks for `pcm`
(raw 24 kHz int16 mono), the same rate Kokoro uses, so make_voiceover.py lays out lines the same way.

Settings come from the environment, falling back to founder-os/.env next to this repo:
    VOICESTUDIO_URL      default http://127.0.0.1:3900
    VOICESTUDIO_API_KEY  the key the setup script generated (OMNIVOICE_API_KEY inside the container)
    VOICESTUDIO_ENGINE   voxcpm2 (default), cosyvoice or pockettts
    VOICESTUDIO_VOICE    the voice profile name or id of Oliver's clone (default "Oliver")

Licensing guard: only engines whose weights allow commercial use are accepted. The default OmniVoice engine
(and the OpenAI aliases like tts-1, which map to whatever engine is active) is CC-BY-NC, so it is refused.
Voice cloning is for Oliver's own voice only, with his consent clip on file in VoiceStudio.

Synthesised clips are cached in .voice-cache/ (keyed by engine, voice, text and speed), because the cloned
voice runs on the CPU and re-timing a script would otherwise re-synthesise every line.

    python scripts/voicestudio.py "A quick test line."     # checks the server and writes voicestudio-test.wav
"""
import hashlib
import json
import os
import pathlib
import urllib.error
import urllib.parse
import urllib.request

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
SR = 24000
COMMERCIAL_ENGINES = ("voxcpm2", "cosyvoice", "pockettts")


class VoiceStudioError(RuntimeError):
    pass


def _env(key, default=""):
    """os.environ first, then founder-os/.env (FOUNDER_OS_ROOT, else the sibling checkout)."""
    if os.environ.get(key):
        return os.environ[key].strip()
    env_file = pathlib.Path(os.environ.get("FOUNDER_OS_ROOT") or ROOT.parent / "founder-os") / ".env"
    try:
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            k, sep, v = line.partition("=")
            if sep and k.strip() == key and v.strip():
                return v.strip().strip('"').strip("'")
    except OSError:
        pass
    return default


class Client:
    def __init__(self, url=None, key=None, engine=None, voice=None, cache=True):
        self.url = (url or _env("VOICESTUDIO_URL", "http://127.0.0.1:3900")).rstrip("/")
        self.key = key if key is not None else _env("VOICESTUDIO_API_KEY")
        self.engine = (engine or _env("VOICESTUDIO_ENGINE", "voxcpm2")).strip().lower()
        self.voice = voice or _env("VOICESTUDIO_VOICE", "Oliver")
        self.cache = ROOT / ".voice-cache" if cache else None
        if self.engine not in COMMERCIAL_ENGINES:
            raise VoiceStudioError(
                f"engine {self.engine!r} is not allowed: use one of {', '.join(COMMERCIAL_ENGINES)}. "
                "OmniVoice (and the tts-1 aliases) are non-commercial, so they can't voice courses or ads.")
        host = urllib.parse.urlparse(self.url).hostname or ""
        # a local server must not go through an HTTP(S)_PROXY that may be set for the internet
        handlers = [urllib.request.ProxyHandler({})] if host in ("127.0.0.1", "localhost", "::1") else []
        self._open = urllib.request.build_opener(*handlers).open

    def _request(self, path, body=None, timeout=30):
        headers = {"Content-Type": "application/json"}
        if self.key:
            headers["Authorization"] = f"Bearer {self.key}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.url + path, data=data, headers=headers, method="POST" if data else "GET")
        try:
            with self._open(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read() or b"{}").get("error", {}).get("message") or e.reason
            except (ValueError, AttributeError):
                msg = e.reason
            if e.code == 401:
                msg = f"{msg} (check VOICESTUDIO_API_KEY)"
            raise VoiceStudioError(f"{path} returned {e.code}: {msg}") from None
        except (urllib.error.URLError, OSError) as e:
            raise VoiceStudioError(f"not answering at {self.url} ({getattr(e, 'reason', e)}). "
                                   "Start it with: docker start voicestudio") from None

    def check(self):
        """Fail early, with a readable reason, if the server, the key, the engine or the voice is wrong."""
        models = json.loads(self._request("/v1/models"))
        ids = {m.get("id") for m in models.get("data", [])}
        if ids and self.engine not in ids:
            raise VoiceStudioError(f"engine {self.engine!r} isn't installed in VoiceStudio (it has: {', '.join(sorted(i for i in ids if i))}). "
                                   "Install it under Settings > Engines.")
        try:
            voices = json.loads(self._request("/v1/audio/voices"))
        except VoiceStudioError:
            return  # older servers have no voice list; speak() will report a bad voice
        names = set()
        for v in voices.get("voices", voices.get("data", [])) if isinstance(voices, dict) else voices:
            if isinstance(v, dict):
                names.update(str(v.get(k, "")).casefold() for k in ("id", "name", "voice_id"))
        if names and self.voice.casefold() not in names:
            raise VoiceStudioError(f"no voice profile called {self.voice!r}. Clone Oliver's voice in VoiceStudio "
                                   "(with the consent clip) and name the profile that, or set VOICESTUDIO_VOICE.")

    def speak(self, text, speed=1.0):
        """One line of narration -> float32 mono at 24 kHz."""
        speed = round(float(speed), 3)
        tag = hashlib.sha256(json.dumps([self.engine, self.voice, text, speed]).encode()).hexdigest()[:24]
        hit = self.cache / f"{tag}.npy" if self.cache else None
        if hit and hit.exists():
            return np.load(hit)
        raw = self._request("/v1/audio/speech", {
            "model": self.engine, "input": text, "voice": self.voice,
            "response_format": "pcm", "speed": speed, "language": "en",
        }, timeout=900)
        if len(raw) < 2:
            raise VoiceStudioError(f"empty audio for: {text[:60]!r}")
        pcm = np.frombuffer(raw[: len(raw) // 2 * 2], "<i2").astype(np.float32) / 32768.0
        if hit:
            hit.parent.mkdir(exist_ok=True)
            np.save(hit, pcm)
        return pcm


if __name__ == "__main__":
    import sys
    import soundfile as sf
    try:
        c = Client(cache=False)
        c.check()
        pcm = c.speak(" ".join(sys.argv[1:]) or "This is a quick test of the cloned voice.")
    except VoiceStudioError as e:
        sys.exit(f"VoiceStudio: {e}")
    sf.write(ROOT / "voicestudio-test.wav", pcm, SR)
    print(f"ok: {len(pcm) / SR:.1f}s from {c.engine} as {c.voice!r} -> voicestudio-test.wav")
