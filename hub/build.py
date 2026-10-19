"""Build the Studio Hub: hub/index.html (open from the repo) and hub/artifact.html (the published page).

    python3 hub/build.py            # rebuild pages; make previews/posters/frame strips only where missing
    python3 hub/build.py --media    # also re-encode every preview

Reads hub/catalog.json (videos, styles, prompt files), hub/prompts-raw.json (the chat prompts, verbatim) and each
video's voice-over config, then writes hub/media/<id>.mp4 (small preview), <id>.jpg (poster) and <id>-frames.jpg
(an 8-frame strip). To add a video: add it to catalog.json and run this script.
"""
import json, pathlib, subprocess, sys, html

ROOT = pathlib.Path(__file__).resolve().parent.parent
HUB = ROOT / 'hub'; MEDIA = HUB / 'media'; MEDIA.mkdir(exist_ok=True)
FORCE = '--media' in sys.argv
cat = json.loads((HUB / 'catalog.json').read_text())
prompts = json.loads((HUB / 'prompts-raw.json').read_text())

def run(*a): subprocess.run(a, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

for v in cat['videos']:
    fm = v['formats']; key = '9x16' if '9x16' in fm else '16x9'; src = ROOT / fm[key]
    v['primary'] = key
    # small preview: 960 px on the long side
    out = MEDIA / f"{v['id']}.mp4"
    if FORCE or not out.exists():
        scale = 'scale=-2:960' if key == '9x16' else 'scale=960:-2'
        run('ffmpeg', '-y', '-i', str(src), '-vf', scale, '-c:v', 'libx264', '-crf', '31', '-preset', 'slow', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '80k', '-movflags', '+faststart', str(out))
    poster = MEDIA / f"{v['id']}.jpg"
    if FORCE or not poster.exists():
        run('ffmpeg', '-y', '-ss', str(round(v['dur'] * .42, 2)), '-i', str(src), '-frames:v', '1', '-vf', 'scale=-2:540', '-q:v', '4', str(poster))
    strip = MEDIA / f"{v['id']}-frames.jpg"
    if FORCE or not strip.exists():
        fps = 8 / v['dur']
        run('ffmpeg', '-y', '-i', str(src), '-vf', f"fps={fps:.5f},scale=-2:200,tile=8x1", '-frames:v', '1', '-q:v', '5', str(strip))
    v['bytes'] = out.stat().st_size
    # the narration lines with their real timings when the voice-over was generated
    if v.get('vo'):
        cfg = json.loads((ROOT / v['vo']).read_text())
        tim = ROOT / v['vo'].replace('.json', '.timings.json')
        lines = json.loads(tim.read_text()) if tim.exists() else [{'t0': l['at'], 't1': l['by'], 'text': l['text']} for l in cfg['lines']]
        v['voice'] = cfg.get('voice'); v['script'] = lines
    elif v.get('lines'):
        v['script'] = [{'t0': None, 't1': None, 'text': t, 'voice': vo} for vo, t in v['lines']]
    # how many commits touched the page: a rough count of design rounds
    page = v.get('page')
    if page and (ROOT / page).exists():
        r = subprocess.run(['git', 'log', '--oneline', '--', page], cwd=ROOT, capture_output=True, text=True)
        v['commits'] = len(r.stdout.strip().splitlines())

for d in cat['docs']:
    p = ROOT / d['path']; d['text'] = p.read_text() if p.exists() else ''

frames = sum(v['dur'] * 30 * len(v['formats']) for v in cat['videos'])
cat['stats'] = {'videos': len(cat['videos']), 'renders': sum(len(v['formats']) for v in cat['videos']),
                'seconds': sum(v['dur'] for v in cat['videos']), 'frames': int(frames),
                'prompts': sum(1 for p in prompts if p['kind'] != 'answer'), 'answers': sum(1 for p in prompts if p['kind'] == 'answer')}
# briefs that came through the Studio queue are shown with the chat prompts
for v in cat['videos']:
    if v.get('brief'):
        bid = 'q-' + v['id']; prompts.append({'id': bid, 't': v['brief']['t'], 'kind': 'brief', 'text': v['brief']['text']})
        if bid not in v['prompts']: v['prompts'].insert(0, bid)
prompts.sort(key=lambda p: p['t'])
cat['prompts'] = prompts

data = json.dumps(cat, ensure_ascii=False).replace('</', '<\\/')
tpl = (HUB / 'template.html').read_text()
page = tpl.replace('/*__DATA__*/null', data)
(HUB / 'artifact.html').write_text(page)
# the repo copy is a full document so it opens straight from disk
(HUB / 'index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>' + page + '</body></html>')
print(f"built hub: {cat['stats']}, media {sum(f.stat().st_size for f in MEDIA.iterdir()) / 1e6:.1f} MB")
