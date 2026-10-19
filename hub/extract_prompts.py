"""Refresh hub/prompts-raw.json from a Claude Code session transcript (your typed prompts and answers, verbatim).

    python3 hub/extract_prompts.py [transcript.jsonl]

Without an argument it reads the largest transcript under ~/.claude/projects/-home-user-Video-Genx2/. Prompts already
in prompts-raw.json are kept (matched by time and text), so running it from a later session only appends.
"""
import json, re, sys, pathlib
HUB = pathlib.Path(__file__).resolve().parent
src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else max((pathlib.Path.home() / '.claude/projects/-home-user-Video-Genx2').glob('*.jsonl'), key=lambda p: p.stat().st_size)
old = json.loads((HUB / 'prompts-raw.json').read_text()) if (HUB / 'prompts-raw.json').exists() else []
seen = {(o['t'], o['text'][:80]) for o in old}
new = []
for line in open(src):
    try: d = json.loads(line)
    except Exception: continue
    if d.get('type') != 'user' or d.get('isMeta') or d.get('isCompactSummary'): continue
    c = d.get('message', {}).get('content'); kind = 'chat'
    if isinstance(c, list):
        tr = [x for x in c if isinstance(x, dict) and x.get('type') == 'tool_result']
        if tr:
            t = tr[0].get('content'); t = t if isinstance(t, str) else ' '.join(y.get('text', '') for y in (t or []) if isinstance(y, dict))
            if t.startswith(('The user answered', 'User has answered', 'Your questions have been answered')): new.append({'t': d['timestamp'][:16], 'kind': 'answer', 'text': t.split('. You can now continue')[0]})
            continue
        txt = '\n'.join(x.get('text', '') for x in c if isinstance(x, dict) and x.get('type') == 'text')
    else: txt = c or ''
    s = re.sub(r'<system-reminder>.*?</system-reminder>', '', txt.strip(), flags=re.S).strip()
    if not s or s.startswith(('<task-notification', '[Request interrupted', '<local-command', 'Caveat:')): continue
    if s.startswith(('<command-message>', '<command-name>')): kind = 'command'
    new.append({'t': d['timestamp'][:16], 'kind': kind, 'text': s})
merged = old + [n for n in new if (n['t'], n['text'][:80]) not in seen]
merged.sort(key=lambda o: o['t'])
for i, o in enumerate(merged): o['id'] = f'p{i + 1:02d}'
(HUB / 'prompts-raw.json').write_text(json.dumps(merged, indent=1, ensure_ascii=False))
print(f'{len(merged)} prompts ({len(merged) - len(old)} new) from {src.name}')
