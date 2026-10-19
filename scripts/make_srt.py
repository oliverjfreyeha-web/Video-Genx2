"""Write an .srt caption file from a voice-over timings file (scripts/make_voiceover.py writes <out>.timings.json).

    python3 scripts/make_srt.py ascentra/reselling/m01-l01-voiceover.timings.json renders/ascentra/reselling/m01-l01.srt

Each narration line becomes cues of at most ~42 characters, timed by their share of the line's characters.
"""
import json, sys

def stamp(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

lines = json.load(open(sys.argv[1])); cues = []
for l in lines:
    words, chunk = l['text'].split(), []
    groups = []
    for w in words:
        if chunk and len(' '.join(chunk + [w])) > 42: groups.append(chunk); chunk = []
        chunk.append(w)
    groups.append(chunk)
    total, acc = len(l['text']), 0
    for g in groups:
        txt = ' '.join(g); t0 = l['t0'] + acc / total * (l['t1'] - l['t0']); acc += len(txt) + 1
        t1 = l['t0'] + min(acc, total) / total * (l['t1'] - l['t0'])
        cues.append((t0, t1 + .15, txt))
with open(sys.argv[2], 'w') as f:
    for i, (a, b, t) in enumerate(cues, 1):
        if i < len(cues): b = min(b, cues[i][0] - .01)   # never overlap the next cue
        f.write(f"{i}\n{stamp(a)} --> {stamp(b)}\n{t}\n\n")
print(f"wrote {sys.argv[2]} ({len(cues)} cues)")
