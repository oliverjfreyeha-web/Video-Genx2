# 006 — Sweep the strike-through instead of snapping it on

- **Status**: DONE
- **Commit**: 5be5bfb
- **Severity**: LOW
- **Category**: Physicality
- **Estimated scope**: 1 file (`google-ads-ecommerce-explainer.html`), ~6 lines CSS + 1 class in HTML

## Problem

`text-decoration` is discrete, so it flips on halfway through the 0.6s dim instead of animating:

```css
/* :126-127 — current */
.row.cut{animation:up .6s var(--ease-out) var(--d) both, dim .6s ease var(--c) forwards}
@keyframes dim{to{opacity:.35;text-decoration:line-through}}
```

## Target

```css
@keyframes dim{to{opacity:.35}}
.kw{position:relative}
.kw::after{content:"";position:absolute;left:0;right:0;top:52%;height:.2cqw;background:currentColor;transform:scaleX(0);
  transform-origin:left;animation:strike .4s var(--ease-out) var(--c) forwards}
@keyframes strike{to{transform:scaleX(1)}}
```
HTML: `<span class="kw">"free shoes"</span>`. Reduced motion: redefine `strike` as an opacity fade with `transform:none` at both ends.

## Verification

- **Feel check**: at 10% playback the line draws left-to-right across "free shoes" while the row dims; with reduced motion it fades in whole.
