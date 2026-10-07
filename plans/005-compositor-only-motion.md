# 005 — Move typing, glow pulse and progress bar onto transform/opacity

- **Status**: DONE
- **Commit**: 5be5bfb
- **Severity**: LOW
- **Category**: Performance
- **Estimated scope**: 1 file (`google-ads-ecommerce-explainer.html`), ~20 lines CSS/HTML/JS

## Problem

Three animations change layout or paint properties:

```css
/* :81-82 — glow pulses box-shadow + border-color forever (repaint every frame) */
.camp.hl{animation:pop .5s var(--ease-out) var(--d) both, hl 1.2s ease var(--h) infinite alternate}
@keyframes hl{to{box-shadow:0 0 0 .6cqw var(--glow);border-color:var(--blue)}}
/* :96 — same pulse on the "Your ad" card */
.ad.you{border:2px solid var(--blue);animation:pop .5s var(--ease-out) var(--d) both, hl 1s ease 4s infinite alternate}
/* :86-89 — typing animates width (layout per step), caret blinks border-color */
.typed{...;overflow:hidden;width:0;border-right:.3cqw solid var(--blue);animation:type 1.8s steps(19) .6s forwards, caret .6s step-end infinite}
@keyframes type{to{width:19ch}}
/* :155 + :333 — progress fill width set every rAF frame */
.fill{...;width:0}
fill.style.width = (t / total * 100) + '%';
```

## Target

- **Glow**: a `::after` ring (border + `box-shadow:0 0 0 .6cqw var(--glow)`) that only animates `opacity` 0→1 (`hl 1.2s ease var(--h) infinite alternate`; on `.ad.you` `inset:-2px`, no border, `--h:4s`, `1s`). Cards keep only the `pop` entrance.
- **Typing**: wrap in `<span class="q">`; `.typed` reveals with `clip-path: inset(0 100% 0 0)` → `inset(0 0 0 0)` in `steps(19)`; a separate `.caret` bar moves `translateX(0 → 19ch)` in the same `steps(19)` timing and blinks via `opacity`.
- **Progress**: `.fill{inset:0;transform:scaleX(0);transform-origin:left}`; JS sets `` fill.style.transform = `scaleX(${t / total})` ``.
- Reduced motion: ring shown static (`animation:none;opacity:1`), typing shown in full (`clip-path:none`), caret hidden.

## Boundaries

- Do NOT change timings or delays. Text must stay exactly 19 characters for `steps(19)`/`19ch` to line up.

## Verification

- **Mechanical**: `getComputedStyle(el,'::after').animationName === 'hl'` on `.camp.hl` and `.ad.you`; `#fill` computed transform is a `matrix(x,0,0,1,0,0)`.
- **Feel check**: the caret steps right with each letter and sits after "shoes" when done; the highlight ring breathes as before; the progress bar fills smoothly.
