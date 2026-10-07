# 001 — Consolidate easing into shared tokens

- **Status**: DONE
- **Commit**: 37b3e5d
- **Severity**: LOW
- **Category**: Cohesion & tokens
- **Estimated scope**: 1 file (`google-ads-ecommerce-explainer.html`), ~10 lines of CSS

## Problem

Easing is hand-typed per rule, mixing CSS `ease` with two different custom curves, and the chart line draw (on-screen movement) uses a generic `ease`:

```css
/* google-ads-ecommerce-explainer.html — current */
:32  .scene.active{display:block;animation:sceneIn .5s ease both}
:42  .up{animation:up .6s cubic-bezier(.2,.8,.2,1) var(--d,0s) both}
:44  .fade{animation:fade .6s ease var(--d,0s) both}
:71  .draw{...;animation:draw 1s ease var(--d,0s) forwards}
:111 .barv{...;animation:grow .9s cubic-bezier(.2,.8,.2,1) var(--d) both}
:122 .row.cut{animation:up .6s ease var(--d) both, dim .6s ease var(--c) forwards}
:131 .graph path.a{...;animation:area .8s ease var(--d) forwards}
```

## Target

Two tokens on the first `:root` block (light theme; dark blocks inherit them):

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);      /* entrances */
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);  /* on-screen movement (line draw) */
```

- Entrances (`sceneIn`, `up`, `fade`, `grow`, `area`, `.row.cut` entrance) → `var(--ease-out)`.
- `.draw` → `var(--ease-in-out)`.
- Color/emphasis changes (`hl` pulse, `dim`) keep `ease` (AUDIT: color change → `ease`).
- Durations unchanged (explanatory content may exceed 300ms).

## Repo conventions to follow

Colors already live as tokens on `:root` (`--blue`, `--line`, …); add the easing tokens in the same block.

## Steps

1. Append the two tokens to the first `:root{...}` block.
2. Replace the easing in each line listed under Problem per the Target mapping.

## Boundaries

- Do NOT change durations, delays, keyframes or markup.
- Do NOT touch the `pop` keyframes (plan 002).
- If lines don't match (drift), STOP and report.

## Verification

- **Mechanical**: `grep -n "cubic-bezier(.2,.8" google-ads-ecommerce-explainer.html` returns nothing; `grep -c "var(--ease-" ...` ≥ 8.
- **Feel check**: play scenes 5–7 in DevTools Animations at 10%: bars and headings decelerate hard into place; the revenue line accelerates then settles (ease-in-out), not a linear-ish crawl.
- **Done when**: every entrance uses a token and no bare custom curve remains except via tokens.
