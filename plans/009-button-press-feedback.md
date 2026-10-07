# 009 — Press feedback on the player buttons

- **Status**: DONE
- **Commit**: 46f5a5e
- **Severity**: LOW
- **Category**: Physicality
- **Estimated scope**: 1 file, 2 lines CSS

## Problem

`.bigplay` (`:159`) and `.btn` (play/pause, restart, `:164`) give no physical response when pressed.

## Target

```css
.btn,.bigplay{transition:transform 160ms var(--ease-out)}
.btn:active,.bigplay:active{transform:scale(.97)}
```
`--ease-out` is `cubic-bezier(0.23, 1, 0.32, 1)`. Kept under reduced motion: it is a 3% feedback cue, not movement. No hover motion added.

## Verification

- Holding the mouse down on a button gives computed `matrix(0.97, 0, 0, 0.97, 0, 0)`; it springs back on release.
