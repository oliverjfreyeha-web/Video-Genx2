# ASCENTRA lesson video spec

Production rules for ASCENTRA course-module explainers. These are teaching videos for students. They carry no
branding, sales pitch or call to action. The brief builder in the Studio Hub (`hub/index.html`) fills in the lesson
details and points at this file. A brief can hold one lesson or a whole module.

## What a lesson video is
- **One learning objective per video.** Write it as "By the end, you can …". Everything on screen serves it.
- **Structure** (adjust the time split to the length):
  1. **Hook (5–8 s):** the question this lesson answers, or the mistake it prevents. On screen: the lesson title and
     "Module N · Lesson N".
  2. **The idea (15–25%):** the core concept in plain words, with one visual metaphor.
  3. **Walkthrough (40–50%):** the steps, worked example or comparison, one beat per point.
  4. **Common mistake (optional, 10%):** what students usually get wrong and how to spot it.
  5. **Recap (10%):** three short bullets on screen, read aloud.
  6. **Check yourself (5 s):** one question for the student to answer in their head. Hold the frame so they can pause.
  7. **Next (3 s):** "Next: <next lesson title>", if given. No logo sting and no CTA.
- **Pacing:** narration at about 130–150 words a minute, slower than the ads. 8–15 s per scene. At most 7 words of
  on-screen text per beat. Give the student a breath after each key point.
- **Length:** 60–180 s. If a lesson needs more, split it into parts (Part 1 / Part 2).
- **Tone:** a clear, friendly teacher. Concrete examples and real numbers (labelled as examples) over abstractions.
  No hype words.

## Look
- **One look per course:** pick a style from the Studio Hub style library and keep it, its palette and its fonts for
  every lesson in that course, so the course feels like one series. Store the course look in
  `ascentra/<course>/LOOK.md` the first time and reuse it.
- **Good teaching styles:** whiteboard, notebook desk, isometric, split screen (compare/contrast), editorial data
  story (formulas and numbers), product UI demo (software how-tos), papercraft (big-picture overviews).
- A quiet lesson tag (course · module · lesson) in one corner throughout. No ASCENTRA logo animation unless asked.
- **Accessibility:** burned-in captions, at least 4.5:1 contrast for text, no flashing faster than 3 per second, and
  key terms shown on screen the first time they're said.
- Original artwork only. No real brands, logos or identifiable people.

## Build (same pipeline as the Elevate videos)
- **Files:** `ascentra/<course-slug>/<mNN-lNN-slug>.html` plus `-voiceover.json`, `-voiceover.wav`,
  `.timings.json` and `-music.wav`. Renders go in `renders/ascentra/<course-slug>/`.
- **Page:** one self-contained HTML page on `batch2/engine.js`. That gives the deterministic `seek(t)`, the
  `?aspect=16x9` switch, word-by-word captions from the timings, and the player.
- **Format:** **16:9 1920×1080 is the default** (course players). Add 9:16 only when the brief asks for it.
- **Voice:**
  - Generate with `scripts/make_voiceover.py` (Kokoro). The default voice is `af_heart` at speed 0.92; `am_fenrir`
    is the male option.
  - Keep one voice per course.
  - If Oliver records his own narration, time the scenes to his audio instead.
- **Music:** `scripts/make_music.py`, a calm bed at 80–92 BPM, mixed low (the mix script already ducks it under the
  voice).
- **Check:** before rendering, look at stills of every scene in each format. Fix text overflow, overlaps and anything
  off-frame.
- **Render and mix:**
  - Render with `scripts/render-video.js`, then mix with `VO=… MUSIC=… scripts/mix-audio.sh`.
  - Also write a `.srt` caption file from the timings, for course platforms that take separate captions.
- **Hub:** add the lesson to `hub/catalog.json` (lane `ascentra`) and run `python3 hub/build.py` so it shows in the
  Studio Hub library.
- **Deliver:** commit, push, and send the MP4s.

## Batch mode
A brief can list several lessons. Build them in order, keeping one look and one voice across the course. Show stills
of the first lesson for approval before rendering the rest, unless the brief says to go straight through.
