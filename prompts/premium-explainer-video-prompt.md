# Premium explainer video prompt — reusable template

This is the full prompt behind the latest videos (the Elevate Home Ads booked-jobs explainer: Pearl Ocean premium finish,
clearer voice, groove music, call-to-action end card, 9:16 reel), with the topic taken out.
Copy everything inside the box into a new Claude Code session, fill in the `{{…}}` fields, and send it.
Only `{{TOPIC}}` is required; every other field has a default.

---

```text
Make a premium animated explainer video about: {{TOPIC}}
Audience: {{AUDIENCE — default: owners of small service businesses who are new to the topic}}
The problem it solves / the one idea to land: {{CORE MESSAGE — optional; otherwise derive it from the topic}}
Key steps or points (optional — otherwise choose 6–8 yourself): {{STEPS}}
Example numbers to show on screen (optional — otherwise invent plausible ones and label them "Example numbers"): {{NUMBERS}}
Business name for the title and end card (optional): {{BUSINESS NAME}}
Call to action + link for the end card (optional): {{CTA — e.g. "Book a call" + yoursite.com}}
Length: {{LENGTH — default: about 55–60 s; 5–7 s per scene}}
Palette: {{PALETTE — default: Pearl Ocean (light); or midnight | prism | berry | citrus | describe your own}}
Narrator voice: {{VOICE — default: the clearest available (Kokoro af_heart); also render a male alternate (am_fenrir)}}
Music mood: {{MUSIC — default: upbeat, warm electric-piano groove, 108 BPM}}
Outputs: {{OUTPUTS — default: all of: interactive HTML page, 16:9 1080p MP4, male-voice MP4 alternate, hosted web page, 9:16 reel}}
Branding: an original style. Don't imitate any real company's brand, logo or look (and don't copy my own brand's style);
use my business name and link only where I gave them.

## Start from the starter kit
Clone https://github.com/oliverjfreyeha-web/Video-Genx2 (branch claude/inspiring-brahmagupta-1d5gg5) and reuse it:
- booked-jobs-explainer.html — the engine, player, premium finish and end card to adapt (replace the scenes, keep the engine)
- design/DESIGN.md — the base design system; the premium finish below overrides its type and colour choices
- scripts/render-video.js (--page/--out/--stills/--prefix), scripts/make_voiceover.py (--voice/--length/--config/--out),
  scripts/make_music_groove.py (--length/--intro/--outro/--out), scripts/mix-audio.sh (VO=… MUSIC=…), scripts/embed-audio.py
- scripts/reel/build-video-reel.js + reel-video.html + booked-jobs-reel.json (copy the JSON for the new topic)
- audio/booked-jobs-voiceover.json — the narration format (one timed line per scene)
If the repo isn't reachable, build the same thing from the spec below.

## The page (one self-contained HTML file)
- A 16:9 stage sized in container units (cqw) so the page and the 1920×1080 render match exactly.
- Timeline: a 2.5 s title card, 6–8 scenes, a 6 s end card. Scene 0 states the problem with a number; the middle scenes
  are the steps; one scene shows the result as a chart with before/after KPI tiles; the last scene shows the whole thing
  as one loop/system. One short headline per scene, with one or two accent words; short labels only, no text blocks.
- A glass chapter bar on top: business name · short tagline, progress dashes, "03 / 07 · Chapter name".
- End card: monogram + business name, a two-line headline ("Same X.<br><em>More Y.</em>" style), one sentence, then
  the CTA label and the link in a dark pill with a round gradient arrow. The intro card uses the same layout with a
  PLAY button.
- Player: play/pause (button + space bar), restart, sound on/off, a progress bar with clickable chapter segments
  (title, each scene, end card), a time readout. Works at phone width with no horizontal scroll.
- One timeline for everything: seek(t) pauses every animation and sets its currentTime: scene animations from the
  scene clock, background animations (Web Animations with id 'g') from the global clock. Playback, pausing, chapter
  jumps and the MP4 render all call the same seek(), so they produce identical frames. Expose window.__seek and
  window.__duration when the URL has ?render.
- Embed the final soundtrack as base64 MP3 and play it from the Play button; while it plays, the audio's currentTime IS
  the clock. MP3, not AAC (some Chromium builds can't decode AAC). Fall back to an internal clock if audio can't play.

## Visual style: liquid glass with a premium finish
- Background: a drifting field of 5 very soft colour blobs on a pale pearl base; the blob colours (--f1…--f5, mist tones)
  are separate from the accent colours and rotate per scene, blending over ~0.9 s. Pearl Ocean: base #EDF3F5,
  ink #0B2233, secondary ink #4A6272; field #7CCFD3 #94B9F2 #C6E5EE #6FAAE6 #A9E0D5; accents teal #0D9488,
  blue #2563EB, deep blue #1E40AF, sky #0284C7, teal #14B8A6; one warm coral #E8705E used ONLY for losses/leaks;
  gradient #0E8F86 → #1D5FD8. No lime, yellow or orange blobs (they turn muddy). All colours are CSS tokens.
- Type (Google Fonts): Geist 500–600 for headlines and numbers with tight tracking (-0.04 to -0.05em) and tabular
  figures; the accent words in Instrument Serif italic (≈1.15em) filled with the gradient (pad the italic so the
  overhang isn't clipped); Geist Mono uppercase, letter-spaced labels.
- Glass panels: white 74% → 40% gradient, backdrop-filter blur(1.6cqw) saturate(1.4), a 1px white hairline rim
  (mask-composite), a soft sheen that sweeps once as a panel lands, long low shadows tinted with the ink colour.
- Flat elements: flat gradient orbs with a thin white ring (no glossy highlights), flat dots, line-drawn icons, no emoji,
  no confetti. Dark ink pills for the CTA and play button.
- Finish layers on top of everything: a light vignette and a static film grain (grey SVG noise in soft-light, ~50%).
- Never nest glass, and never animate opacity/filter/mask/blend on an ancestor of glass (it becomes a backdrop root and
  the blur stops sampling the colour field). Scene motion is transform only; panels fade themselves.

## Motion (Emil Kowalski's rules — run the improve-animations skill on the result)
- Easing tokens: --ease-out cubic-bezier(0.23,1,0.32,1) for entrances; --ease-in-out cubic-bezier(0.77,0,0.175,1) for
  lines/paths; linear for constant motion. Never ease-in; never scale from 0.
- Camera: each scene settles from scale(1.04) translateY(.6cqw) to rest over its whole duration
  (cubic-bezier(.12,.75,.3,1)), which doubles as the entrance. 0.3 s crossfade with a slight blur on the outgoing scene.
- Headlines: words rise one by one out of a clip-path mask (translateY 115% + 3° tilt → rest, 60 ms stagger).
- Glass panels land with translateY + scale(.96) + blur clearing, staggered.
- One signature motion per scene, e.g. a grid of dots where most go dark and a few light up; a leaky bucket with
  drops falling in and coral drops leaking out; a funnel of liquid-filled bars with coral drips at each gap; a phone
  conversation with a timer ring drawing round; scored rows with meters and a card flying into a calendar slot; a
  pulse travelling a timeline that lights each touchpoint; a dot riding a line chart (offset-path) with an area fade;
  an orbit with a satellite around the hub.
- Numbers count up from the timeline (not timers) in fixed-width boxes; before/after values struck through in coral.
- prefers-reduced-motion: no drift, loops or flights; panels fade in place; data and values still show.
- Buttons scale to .97 on press (160 ms ease-out).

## Narration
- One line per scene (≈2.2 words/second), stored as JSON with "at" (earliest start) and "by" (must end). The first line
  hooks with the problem as a question; the last line repeats the promise and says the CTA with the business name.
- Voice: Kokoro (open-weight TTS, runs locally): pip install kokoro-onnx soundfile numpy; kokoro-v1.0.onnx +
  voices-v1.0.bin from https://github.com/thewh1teagle/kokoro-onnx/releases (model-files-v1.0).
- Clarity: speed 0.95; trim silence with 5 ms fades; build the track at Kokoro's native 24 kHz and resample once with
  ffmpeg soxr (linear interpolation sounds metallic). Fit each line in its window (speed up at most 1.15×, otherwise
  shorten the line). Clearest voices: af_heart, then af_bella; the male voices (am_fenrir, am_michael, am_puck) are
  rated lower, so render a male alternate rather than making it the default unless I ask.
- Write a timings JSON next to the WAV (start/end/text per line) for the reel's captions.

## Music and mix
- Compose an original bed procedurally (numpy), e.g. 108 BPM in F major (Fmaj7, Dm9, Bbmaj7, C6/9): FM electric-piano
  chord stabs, a syncopated round bass, soft four-on-the-floor kick, claps on 2 and 4, swung hats, a short marimba hook
  every two bars. Chords alone under the title card, drums out for the end card, fade at the end. Keep the kick and bass
  gentle; check the spectrum.
- Mix with ffmpeg: voice chain = high-pass 90 Hz, -2 dB at 250 Hz, +2.5 dB at 3.5 kHz, de-esser, gentle compression,
  fixed gain to ≈-16 LUFS (no loudnorm: its look-ahead truncates the last seconds); music -12 dB, cut 2 kHz a little,
  sidechaincompress ducking under the voice; alimiter at 0.89. Verify duration and loudness afterwards.

## Rendering and outputs
- 16:9: Playwright + headless Chromium at 1920×1080; load every font face before frame 0; seek frame by frame at 30 fps;
  pipe JPEG frames into ffmpeg libx264 (crf 17, preset slow, profile high, level 4.0, yuv420p, +faststart); then mix the
  audio in. Level 4.0 matters: level 5.0 files won't open in some phone/in-app players. Mix the male alternate onto the
  same silent render.
- Embed the soundtrack into the page (scripts/embed-audio.py).
- Hosted page: publish the page as a private claude.ai Artifact with the MP4 below the player; re-encode a ≤15 MB copy
  (crf 24) for it. Downloads are blocked inside artifacts, so show the video instead of a download link.
- 9:16 reel (1080×1920): the same palette, fonts, glass, grain and vignette; a glass bar with the business name and a
  tagline; a row of step chips (current one in solid ink); a kicker + big title per section with the serif-italic accent;
  the 16:9 video in a glass frame; word-by-word captions for every spoken line (most viewers are muted); the CTA label
  and link in a dark pill with an arrow for the end card; a progress bar with times. Reuse the 16:9 soundtrack.

## Process and checks
- Commit and push after each milestone.
- Before the full render, render stills of every scene plus a transition frame and look at them as a JPEG contact sheet;
  fix overlaps, clipped text, unreadable labels, seams in gradients and off-palette colours.
- After a render, check duration, codec level and loudness with ffprobe/ebur128, and look at reel stills before the full reel.
- Test the page in Chromium: play, pause holds the frame, chapter jumps, mute, end card + replay, reduced motion, 390 px width.
- Tell me plainly what you could not verify (you can't listen to audio: say so and ask me to check both voices).
- Send me the files at the end: the 16:9 MP4, the male-voice MP4, the 9:16 reel and the hosted page link.
```

---

## Links: repos, skills and tools used

- Starter kit repo: https://github.com/oliverjfreyeha-web/Video-Genx2 (branch `claude/inspiring-brahmagupta-1d5gg5`)
- `improve-animations` skill by Emil Kowalski: https://github.com/emilkowalski/skills
  (`npx skills add https://github.com/emilkowalski/skills --skill improve-animations`); skills CLI: https://github.com/vercel-labs/skills
- Claude Code's built-in `artifact-design` skill, for the hosted page
- Playwright: https://github.com/microsoft/playwright · FFmpeg: https://github.com/FFmpeg/FFmpeg
- kokoro-onnx: https://github.com/thewh1teagle/kokoro-onnx · Kokoro-82M: https://huggingface.co/hexgrad/Kokoro-82M
- NumPy: https://github.com/numpy/numpy · soundfile: https://github.com/bastibe/python-soundfile
- Fonts: Geist / Geist Mono https://fonts.google.com/specimen/Geist · Instrument Serif https://fonts.google.com/specimen/Instrument+Serif
- The earlier, louder "Prism / Midnight" version of this prompt: prompts/explainer-video-prompt.md
