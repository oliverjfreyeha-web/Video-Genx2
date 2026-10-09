# Shared contract for the four series videos (read fully before building)

You are building ONE 38-second animated explainer page for Elevate Home Ads (a marketing service for home-service
businesses), rendered to MP4 in two formats. Repo root: /home/user/Video-Genx2. Work only on your own files:
`series/<name>.html` (and stills/renders named after <name>). Do not edit any other file. Do not commit or push.

## Page contract
- One self-contained HTML file: inline CSS + JS, inline SVG. Google Fonts via <link> is allowed; no other external
  scripts or images (draw everything with SVG/CSS/canvas).
- Two layouts from one page: default 1080×1920 (9:16); `?aspect=16x9` → 1920×1080. Lay the stage out at that exact
  pixel size (absolute positioning in px is fine) and, outside render mode, scale it to fit a centered preview frame.
  Design BOTH layouts properly (different composition, not just scaled): 9:16 stacks vertically, 16:9 uses width.
- ONE CLOCK: a function seek(t) sets every visual property from t alone (seconds). No CSS animations/transitions,
  no setTimeout/rAF-driven state, no randomness without a fixed seed. Everything must be a pure function of t.
- In `?render` mode: add class `render` to body (stage fills the viewport, no controls), then set
  `window.__duration = 38` and `window.__seek = t => seek(t)` AFTER fonts are loaded
  (`await document.fonts.load(...)` for every family/weight you use, then `document.fonts.ready`).
- Outside render mode: a simple player (play/pause button + space bar, progress bar you can click, time readout).
  No audio needed in the page.
- Timeline (seconds): title card 0–2.5 · beat 1 2.5–8.5 · beat 2 8.5–14.5 · beat 3 14.5–20.5 · beat 4 20.5–26.5 ·
  beat 5 26.5–32 · end card 32–38. Narration lines and their exact times are in `series/<name>-voiceover.timings.json`
  (t0/t1/text). Copy that JSON into a <script type="application/json"> in the page.
- Captions: show the narration word by word (chunks of ≤3–4 words, each word appearing at its share of the line's
  character count between t0 and t1). Style them to match your design. Keep them clear of the main visuals.
- End card (32–38): "Elevate Home Ads", the CTA label given below, and the link "oliverelevatehomeads.com".
- Short on-screen labels only (no paragraphs). Mark invented numbers with a small "Example numbers" label.
- Original artwork only: no real company logos (write "Google", "Facebook" as plain text if needed), no copyrighted
  characters, no imitation of any real brand's look.

## Motion bar (Emil Kowalski's rules; see .claude/skills/improve-animations/AUDIT.md)
- Entrances ease-out cubic-bezier(0.23,1,0.32,1) (implement as a JS bezier or a strong cubic); on-screen movement
  ease-in-out cubic-bezier(0.77,0,0.175,1). Never ease-in for entrances. Never scale from 0 (start at 0.9–0.97 with
  opacity 0, or draw on / slide in). Stagger groups by 30–80 ms. Small overshoot is OK for playful moments.
- Every beat has ONE clear signature motion that illustrates the narration line, timed to the words.
- Transitions between beats must be designed (a camera move, wipe, push, page-turn…) not hard cuts to a new page.

## Render + check loop (do this, it's the job)
- Stills: `node scripts/render-video.js --page series/<name>.html --width 1080 --height 1920 --stills 1.2,5,11,17,23,29,35 --prefix <name>t`
  and `node scripts/render-video.js --page series/<name>.html --width 1920 --height 1080 --query aspect=16x9 --stills 1.2,5,11,17,23,29,35 --prefix <name>w`
  (PNGs land in renders/stills/). LOOK at them with the Read tool (make a contact sheet with ffmpeg hstack/vstack,
  scale down, JPEG). Fix overlaps, clipped or unreadable text, empty-looking frames, off-palette colours. Check a
  frame mid-transition too. Iterate until both formats look polished and premium. Fix any "page error" output.
- Full renders (run both in the background in parallel, each takes a while):
  `mkdir -p renders/series && node scripts/render-video.js --page series/<name>.html --width 1080 --height 1920 --out renders/series/<name>-9x16-silent.mp4`
  `node scripts/render-video.js --page series/<name>.html --width 1920 --height 1080 --query aspect=16x9 --out renders/series/<name>-16x9-silent.mp4`
- Mix audio onto each: `VO=series/<name>-voiceover.wav MUSIC=series/<name>-music.wav scripts/mix-audio.sh renders/series/<name>-9x16-silent.mp4 renders/series/<name>-9x16.mp4`
  (same for 16x9). Verify with ffprobe that both are 38.0 s and have audio. Pull 6 frames from each final MP4 and
  look at them.
- Report back: what you built per beat, the final file paths and sizes, anything you couldn't verify.
