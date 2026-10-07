# 002 — Replace the half-scale bouncy `pop` with a subtle scale-in

- **Status**: DONE
- **Commit**: 37b3e5d
- **Severity**: HIGH
- **Category**: Physicality & origin / Easing
- **Estimated scope**: 1 file (`google-ads-ecommerce-explainer.html`), 4 lines of CSS
- **Depends on**: 001 (`--ease-out` token)

## Problem

`.pop` scales elements from 50% with an overshoot curve. It is used on large cards (browser mockup at 56% stage width `:167`, hub `:186`, campaign cards, search results), so they balloon in and wobble:

```css
/* google-ads-ecommerce-explainer.html — current */
:43  .pop{animation:pop .55s cubic-bezier(.3,1.5,.5,1) var(--d,0s) both}
:47  @keyframes pop{from{opacity:0;transform:scale(.5)}to{opacity:1;transform:scale(1)}}
:77  .camp.hl{animation:pop .55s cubic-bezier(.3,1.5,.5,1) var(--d) both, hl 1.2s ease var(--h) infinite alternate}
:92  .ad.you{...;animation:pop .55s cubic-bezier(.3,1.5,.5,1) var(--d) both, hl 1s ease 4s infinite alternate}
```

## Target

```css
.pop{animation:pop .5s var(--ease-out) var(--d,0s) both}
@keyframes pop{from{opacity:0;transform:scale(.92)}to{opacity:1;transform:scale(1)}}
.camp.hl{animation:pop .5s var(--ease-out) var(--d) both, hl 1.2s ease var(--h) infinite alternate}
.ad.you{...;animation:pop .5s var(--ease-out) var(--d) both, hl 1s ease 4s infinite alternate}
```

Scale start 0.92 sits in the AUDIT range (0.9–0.97); `--ease-out` is `cubic-bezier(0.23, 1, 0.32, 1)`.

## Steps

1. Edit line 43 and keyframes line 47 as in Target.
2. Edit the `pop` part of lines 77 and 92; leave the `hl` part untouched.

## Boundaries

- Do NOT change `transform-origin` (center is correct for these standalone cards).
- Do NOT change delays (`--d`) or markup.

## Verification

- **Mechanical**: `grep -n "1.5,.5,1\|scale(.5)" google-ads-ecommerce-explainer.html` returns nothing.
- **Feel check**: at 10% playback, scene 1 browser and scene 2 hub grow ~8% while fading in, with no overshoot past full size; the "Your ad" glow still starts at 4s.
- **Done when**: no element scales below 0.92 and none overshoots.
