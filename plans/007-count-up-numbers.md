# 007 — Count up the funnel and ROAS numbers

- **Status**: DONE
- **Commit**: 46f5a5e
- **Severity**: LOW
- **Category**: Missed opportunities
- **Estimated scope**: 1 file (`google-ads-ecommerce-explainer.html`), ~15 lines JS/CSS + attributes on 5 elements

## Problem

Funnel values (`10,000`, `400`, `16`, scene 5 at `:240-242`) and ROAS inputs (`$4,000`, `$1,000`, scene 6 at `:250`, `:252`) pop in already final, so the drop-off from 10,000 to 16 doesn't land.

## Target

- Mark each number `<span class="count" data-to="10000" data-at=".7" [data-pre="$"] style="--w:6ch">`; `data-at` = seconds into the scene, just after its card enters (`.7`, `1.6`, `2.5` funnel; `.6`, `1.2` ROAS).
- Drive values from the **timeline `t`** inside `render()` (not a CSS or independent timer), so pause, chapter jumps and the 0.3s crossfade stay in sync: `p = clamp((t - sceneStart - at) / 0.9)`, eased `1 - (1 - p)^3` (ease-out), formatted with `toLocaleString('en-US')`.
- `.count{display:inline-block;font-variant-numeric:tabular-nums;min-width:var(--w);text-align:var(--al,right)}` so growing digits don't shift neighbouring cards (`--al:center` in the ROAS cards).
- Reduced motion: show final values immediately (`p = 1`).

## Verification

- Pause mid-count: value holds across 1.5s. Jump to scene 5 again: counts restart from 0. Reduced motion: final values from the first frame.
