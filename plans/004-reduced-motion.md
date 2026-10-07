# 004 — Honour prefers-reduced-motion across the explainer

- **Status**: DONE
- **Commit**: f07a6f1
- **Severity**: MEDIUM
- **Category**: Accessibility
- **Estimated scope**: 1 file (`google-ads-ecommerce-explainer.html`), ~8 lines CSS

## Problem

The only reduced-motion rule (`:157`) covers the typing effect. Every slide-up (`.up`), scale-in (`.pop`), and the infinite glow pulses (`.camp.hl :77`, `.ad.you :92`) still run.

```css
/* :157 — current */
@media (prefers-reduced-motion: reduce){.typed{width:19ch}}
```

## Target

Fewer and gentler, not zero: keep opacity fades, the line draws and bar growth (they carry the explanation); drop translate/scale movement, looping pulses and the blinking caret. The highlight stays as a static border + ring so the emphasis isn't lost.

```css
@media (prefers-reduced-motion: reduce){
  @keyframes up{from{opacity:0}to{opacity:1}}
  @keyframes pop{from{opacity:0}to{opacity:1}}
  @keyframes sceneOut{to{opacity:0}}
  .camp.hl,.ad.you{animation:pop .5s var(--ease-out) var(--d) both;border-color:var(--blue);box-shadow:0 0 0 .6cqw var(--glow)}
  .typed{animation:none;width:19ch;border-right-color:transparent}
}
```

Redefining `@keyframes` inside the media query swaps every `.up`/`.pop` user in one place without touching their delays.

## Boundaries

- Do NOT remove `grow`, `draw`, `area`, `fade` or `dim`.

## Verification

- **Mechanical**: in Playwright with `reducedMotion: 'reduce'`, `.ad.you` computed `animationName` is `pop` only (no `hl`).
- **Feel check**: DevTools Rendering → emulate reduced motion: cards fade in place with no movement, no pulsing, search text shown in full, charts still build.
