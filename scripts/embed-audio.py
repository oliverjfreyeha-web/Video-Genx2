"""Embed the final soundtrack into google-ads-ecommerce-explainer.html so the page stays one self-contained file.

    python3 scripts/embed-audio.py [video.mp4] [page.html]

Extracts the mixed audio from the MP4, re-encodes it as 128 kbps MP3 (every browser decodes MP3; some open-source Chromium builds lack AAC) and writes it, base64-encoded,
into <script id="soundtrack">. Re-run after scripts/mix-audio.sh.
"""
import base64, pathlib, re, subprocess, sys, tempfile

root = pathlib.Path(__file__).resolve().parent.parent
src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root / "renders/google-ads-explainer-1080p.mp4"
page = root / (sys.argv[2] if len(sys.argv) > 2 else "google-ads-ecommerce-explainer.html")
with tempfile.TemporaryDirectory() as d:
    mp3 = pathlib.Path(d) / "soundtrack.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn", "-c:a", "libmp3lame", "-b:a", "128k", str(mp3)], check=True)
    b64 = base64.b64encode(mp3.read_bytes()).decode()
html = page.read_text()
html, n = re.subn(r'(<script id="soundtrack" type="text/plain">)[^<]*(</script>)', lambda m: m.group(1) + b64 + m.group(2), html)
assert n == 1, "soundtrack tag not found"
page.write_text(html)
print(f"embedded {len(b64) / 1e6:.2f} MB of base64 audio into {page.name}")
