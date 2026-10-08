# Explainer video prompt — reusable template

Copy everything inside the box below into a new Claude Code session, fill in the `{{…}}` fields, and send it.
It reproduces the full pipeline from this project: an animated explainer page, a narrated 16:9 MP4 with music,
a hosted web page, and a 9:16 reel — in the "Prism / Midnight" liquid-glass style that we arrived at.

Only `{{TOPIC}}` is required. Every other field has a default in brackets.

---

```text
Make an animated explainer video about: {{TOPIC}}
Audience: {{AUDIENCE — default: small-business owners who are new to the topic}}
Key steps or points to cover (optional — otherwise choose 6–8 yourself): {{STEPS}}
Example numbers to use on screen (optional — otherwise invent plausible ones and label them as examples): {{NUMBERS}}
Length: {{LENGTH — default: under a minute; 5–7 s per scene}}
Palette: {{PALETTE — midnight (default) | prism | ocean | berry | citrus | describe your own}}
Narrator voice: {{VOICE — default: Kokoro af_heart (warm US female); e.g. am_michael, bf_emma, bm_george}}
Music mood: {{MUSIC — default: warm, optimistic, 92 BPM}}
Outputs: {{OUTPUTS — default: all of: interactive HTML page, 16:9 1080p MP4, hosted web page, 9:16 reel}}
Branding: original style only — do not imitate any real company's brand, logo or look.

## Start from the starter kit
Clone https://github.com/oliverjfreyeha-web/Video-Genx2 (branch claude/inspiring-brahmagupta-1d5gg5) and reuse it:
- google-ads-ecommerce-explainer.html — the page, player, palettes and render mode to adapt (replace the scenes, keep the engine)
- design/DESIGN.md — the design system to follow (update it for the new topic)
- scripts/render-video.js, scripts/make_voiceover.py, scripts/make_music.py, scripts/mix-audio.sh, scripts/embed-audio.py
- scripts/reel/* — the 9:16 reel builder
- audio/voiceover.json — the narration format (one timed line per scene)
If the repo isn't reachable, build the same thing from the spec below.

## The page (one self-contained HTML file)
- A 16:9 stage sized in container units (cqw) so the page and the 1920×1080 render match exactly.
- Scenes: a title card, 6–8 steps, an end card that recaps the steps as a loop. One short headline per scene with a single
  key word in gradient text; short on-screen labels only, no long text blocks.
- Player: play/pause (button + space bar), restart, sound on/off, a progress bar with clickable chapter segments
  (title, each scene, end card), a time readout. Works at phone width with no horizontal scroll.
- One timeline for everything: seek(t) pauses every animation and sets its currentTime — scene animations from the scene
  clock, background animations (Web Animations with id 'g') from the global clock. Playback, pausing, chapter jumps and the
  MP4 render all call the same seek(), so they produce identical frames. Expose window.__seek and window.__duration
  when the URL has ?render.
- Embed the final soundtrack as base64 MP3 and play it from the Play button; while it plays, the audio's currentTime IS
  the clock. MP3, not AAC: some Chromium builds can't decode AAC. Fall back to an internal clock if audio can't play.

## Visual style ("Prism", liquid glass)
- A drifting field of 5 soft colour blobs behind everything; per-scene palettes blend over ~0.9 s at each scene change.
- Content sits on frosted glass: translucent white gradient, backdrop-filter blur(1.4cqw) saturate(1.9), a 1px rim that
  fades white → aqua → pink (mask-composite), a specular sheen that sweeps once as a panel lands, soft shadow.
- Never nest glass, and never animate opacity/filter/mask on an ancestor of glass (it becomes a backdrop root and the blur
  stops sampling the colour field). Scene entrances animate transform only; panels fade themselves.
- No orange anywhere; yellow only for sparks/confetti (yellow blobs turn muddy). Losing values are greyed or struck
  through, never red.
- Type: Unbounded 600 for headlines and big numbers, Figtree for body, Martian Mono uppercase for labels (Google Fonts).
- Custom line-drawn icons and product drawings in glossy gradient orbs — no emoji.
- Optional "premium finish" (used on booked-jobs-explainer.html): Geist 500–600 with tight tracking (-0.04em) for
  headlines and numbers, accent words in Instrument Serif italic with the gradient, Geist Mono labels; a softer field
  palette (--f1…--f5, mist tones) separate from the accent hues; hairline white glass rims and long low shadows; flat
  orbs and dots (no glossy highlights); one warm coral (--c6) only for losses/leaks; no confetti; ink-coloured CTA pills;
  headline words rise out of a clip-path mask; each scene settles from scale 1.04 to 1 over its whole duration (a slow
  camera move that doubles as the entrance); a static soft-light film grain and a light vignette as top layers.
- All colours are CSS tokens (--base, --ink, --ink-2, --c1…--c6, glass tints, --grad, --grad-text). Ship palettes:
  midnight (navy #090A1C; pink #FF2E93, violet #8B5CFF, blue #3D6BFF, aqua #00E1FF, mint #00F5A0; white text, light
  lavender captions so they read on bright glass), prism (light lavender base, pink/violet/blue/cyan/mint),
  ocean (#E6F5FA; teal, blue, deep blue, cyan, lime), berry, citrus. Switch with <html data-palette> or ?palette=.

## Motion (Emil Kowalski's rules — run the improve-animations skill on the result)
- Easing tokens: --ease-out cubic-bezier(0.23,1,0.32,1) for entrances; --ease-in-out cubic-bezier(0.77,0,0.175,1)
  for lines/paths; linear for constant motion. Never ease-in; never scale from 0 (use .92–.97).
- Headline words rise in one by one with a light blur; glass lands with translateY + scale(.96) + blur clearing.
- Give every scene one signature motion, e.g. radar ping, beams with travelling data packets into a glossy orb, cards
  fanning out with a spinning gradient rim, a cursor click with ripple, liquid filling glass tubes, an orb burst with
  sparks, a dot riding a line chart (offset-path), confetti on the final result.
- Numbers count up from the timeline (not timers), in fixed-width boxes so nothing shifts.
- 0.3 s crossfade between scenes with a slight blur on the outgoing scene.
- Only animate transform/opacity (typing via clip-path steps, progress bar via scaleX, glow via a pseudo-element's opacity).
- prefers-reduced-motion: no drift, loops or bursts; panels fade in place; data still fills; captions/values shown.
- Buttons scale to .97 on press (160 ms ease-out).

## Narration and music
- Write one narration line per scene (≈2.2 words/second), stored as JSON with "at" (earliest start) and "by" (must end).
- Voice: Kokoro (open-weight TTS, runs locally): pip install kokoro-onnx soundfile numpy; download kokoro-v1.0.onnx and
  voices-v1.0.bin from https://github.com/thewh1teagle/kokoro-onnx/releases (model-files-v1.0). Trim silence, fit each
  line inside its scene window (speed up at most 1.15×, otherwise start earlier or shorten the line).
  Build the track at Kokoro's native 24 kHz and resample once with ffmpeg soxr (linear interpolation sounds metallic);
  speed 0.95 reads clearer. Clearest Kokoro voices: af_heart, then af_bella; the male voices (am_michael, am_fenrir,
  am_puck) are rated lower. In the mix: high-pass 90 Hz, -2 dB at 250 Hz, +2.5 dB at 3.5 kHz, de-ess, gentle compression.
- Music: compose an original bed procedurally (numpy): pad chords, round bass, plucked arpeggio with echo, soft kick and
  shaker; pad alone under the title card, drums out for the end card. Check the spectrum — keep bass/kick from dominating.
- Mix with ffmpeg: voice +gain to ≈-16 LUFS (fixed gain — loudnorm's look-ahead truncates the last seconds), music
  -12 dB with sidechaincompress ducking under the voice, alimiter at 0.89. Verify duration and loudness afterwards.

## Rendering
- 16:9: Playwright + headless Chromium at 1920×1080, preload every font weight, seek frame by frame at 30 fps, pipe JPEG
  frames into ffmpeg libx264 (crf 17, preset slow, profile high, level 4.0, yuv420p, +faststart), then mix audio in.
  Level 4.0 matters: level 5.0 files won't open in some phone/in-app players.
- Hosted page: publish the page as a claude.ai Artifact with the MP4 below it; re-encode a ≤15 MB copy (crf 24) for it.
  Downloads are blocked inside artifacts, so show the video instead of a download link.
- 9:16 reel (1080×1920, ≤60–90 s): a compositor page with a version/step tracker, a big title per section, the 16:9
  clip in a glass frame, word-by-word captions for every spoken line (most viewers are muted), key content clear of the
  platform's top/bottom UI. Render the same way and mix narration + music.

## Process and checks
- Commit and push after each milestone.
- After every visual change, render stills of every scene and look at them before rendering the full video; fix overlaps,
  unreadable text, clipped elements and off-palette colours. Inspect contact sheets as JPEG (palette PNGs band).
- After a render, pull frames from the MP4 and check duration, codec level and loudness with ffprobe/ebur128.
- Test the page in Chromium: play, pause holds the frame, chapter jumps, mute, end card + replay, reduced motion, 390 px width.
- Tell me plainly what you could not verify (you can't listen to audio — say so and ask me to check).
```

---

## Links — repos, skills and tools used in this project

**This project (the starter kit)**
- Repo: https://github.com/oliverjfreyeha-web/Video-Genx2 — branch `claude/inspiring-brahmagupta-1d5gg5`
- Live page (Midnight, with the MP4): https://claude.ai/artifact/E58JN35CeuKkTw5DaKMCZr

**Skills**
- `improve-animations` by Emil Kowalski — https://github.com/emilkowalski/skills
  (installed with `npx skills add https://github.com/emilkowalski/skills --skill improve-animations`)
- `skills` CLI used to install it (Vercel) — https://github.com/vercel-labs/skills
- Emil Kowalski's animation writing the skill is based on — https://emilkowal.ski
- Claude Code's built-in `artifact-design` skill — used to publish the hosted page as a claude.ai Artifact

**Open-source tools in the pipeline**
- Playwright (headless Chromium, frame-by-frame rendering) — https://github.com/microsoft/playwright
- FFmpeg (encoding, mixing, ducking, loudness) — https://github.com/FFmpeg/FFmpeg
- kokoro-onnx (local text-to-speech) — https://github.com/thewh1teagle/kokoro-onnx
- Kokoro-82M voice model — https://huggingface.co/hexgrad/Kokoro-82M
- NumPy + soundfile (procedural music, audio editing) — https://github.com/numpy/numpy · https://github.com/bastibe/python-soundfile

**Fonts (Google Fonts)**
- Unbounded — https://fonts.google.com/specimen/Unbounded
- Figtree — https://fonts.google.com/specimen/Figtree
- Martian Mono — https://fonts.google.com/specimen/Martian+Mono
- Earlier "Ledger" style: Instrument Serif, Geist, Geist Mono — https://fonts.google.com/specimen/Instrument+Serif · https://fonts.google.com/specimen/Geist

**Looked at, not used in the final pipeline**
- Open Design — https://github.com/nexu-io/open-design — the source of two ideas we kept: a written DESIGN.md style
  guide and rendering video frame by frame in a headless browser.
- OpenCut — https://github.com/OpenCut-app/OpenCut — open-source video editor (a CapCut alternative, not access to
  CapCut's tools); mid-rewrite, classic version at https://github.com/opencut-app/opencut-classic.
- Higgsfield (connected account) — tried for the voice-over; its file host was blocked in this environment, and it has
  no music model, so Kokoro and the procedural music replaced it.
