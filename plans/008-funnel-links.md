# 008 — Connect the funnel steps with flowing links

- **Status**: DONE
- **Commit**: 46f5a5e
- **Severity**: LOW
- **Category**: Missed opportunities
- **Estimated scope**: 1 file, ~8 lines CSS + 2 elements

## Problem

Scene 5's three funnel cards (`.f1` top 25%, `.f2` top 47%, `.f3` top 69%, all centred at x = 46%) float unconnected, so "clicks become sales" isn't shown as a flow.

## Target

```html
<div class="flow fade" style="top:38%;--d:1.6s;--fd:1.6s;--c:var(--blue)"><i></i><i></i></div>
<div class="flow fade" style="top:60%;--d:2.5s;--fd:2.5s;--c:var(--yellow)"><i></i><i></i></div>
```
```css
.flow{position:absolute;left:46%;width:.3cqw;height:9%;margin-left:-.15cqw;background:var(--line);border-radius:99px}
.flow i{...;width:1cqw;height:1cqw;border-radius:50%;background:var(--c);opacity:0;animation:flow 1.2s linear var(--fd) infinite}
.flow i+i{animation-delay:calc(var(--fd) + .6s)}
@keyframes flow{0%{opacity:0;transform:translateY(0)}20%,80%{opacity:1}100%{opacity:0;transform:translateY(4cqw)}}
```
Links appear as the lower card lands. `linear` because it is constant motion. Reduced motion: `.flow i{display:none}` (the static connector stays).

## Verification

- Dots drift down each gap in the colour of the step they leave; pausing freezes them.
