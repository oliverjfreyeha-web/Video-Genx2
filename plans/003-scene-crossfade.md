# 003 — Crossfade between scenes instead of hard-cutting

- **Status**: DONE
- **Commit**: f07a6f1
- **Severity**: MEDIUM
- **Category**: Missed opportunities / Cohesion
- **Estimated scope**: 1 file (`google-ads-ecommerce-explainer.html`), ~10 lines CSS + JS

## Problem

`show()` removes `.active` from every scene, so the outgoing scene is `display:none` instantly while the incoming one fades in from 0 and its children enter on delays. Result: ~0.5s near-blank stage at each of the 7 scene changes.

```css
/* :32 — current */
.scene.active{display:block;animation:sceneIn .5s var(--ease-out) both}
```
```js
/* :310 — current */
function show(i) {
  scenes.forEach(s => s.classList.remove('active'));
  void stage.offsetWidth; // restart CSS animations
  scenes[i].classList.add('active');
  cur = i;
}
```

## Target

```css
.scene.active{display:block;z-index:1;animation:sceneIn .5s var(--ease-out) both}
.scene.leaving{display:block;z-index:0;pointer-events:none;animation:sceneOut .3s var(--ease-out) forwards}
@keyframes sceneOut{to{opacity:0;filter:blur(2px)}}
```
```js
function show(i) {
  const prev = scenes[cur];
  scenes.forEach(s => s.classList.remove('active', 'leaving'));
  if (prev && prev !== scenes[i]) prev.classList.add('leaving');
  void stage.offsetWidth; // restart CSS animations
  scenes[i].classList.add('active');
  cur = i;
}
scenes.forEach(s => s.addEventListener('animationend', e => {
  if (e.target === s && e.animationName === 'sceneOut') s.classList.remove('leaving');
}));
```

`animationend` (not `setTimeout`) so the existing `.stage.paused` rule freezes the crossfade mid-way. `blur(2px)` masks the double exposure of the two headings.

## Boundaries

- Do NOT change scene durations or the rAF timeline.
- Only one scene may be `.leaving` at a time (rapid chapter clicks).

## Verification

- **Feel check**: pause right after a scene change: the old scene is visible, blurred and fading under the new heading. Rapid-click chapter ticks: never more than two scenes visible. Pause mid-crossfade: it holds; resume: it finishes.
- **Done when**: no scene change shows an empty stage.

## Also fixed while verifying

`.wire path` (`:74`) set `stroke-dasharray:1.5 1`, which out-ranked `.draw`'s `stroke-dasharray:1`, so the scene-2 connector lines showed as dashes from frame 0 instead of drawing in. Removed the dasharray from `.wire path`.
