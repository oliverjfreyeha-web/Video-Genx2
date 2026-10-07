# DESIGN.md — "Prism"

Bright, optimistic motion graphics: frosted **liquid-glass** panels floating over a slowly drifting field of vivid colour. Every scene in `google-ads-ecommerce-explainer.html` follows these rules. (Supersedes the earlier "Ledger" paper style.)

## Principles

1. **Colour lives in the background, clarity lives on glass.** A mesh of soft colour blobs moves behind everything; content sits on translucent glass that blurs and brightens what's behind it.
2. **No orange.** The palette runs pink → violet → blue → cyan → mint, with lemon as a spark.
3. **Gradients carry emphasis.** The key word of each headline, the "start here" choices and the winning numbers use the spectrum gradient instead of a single accent colour.
4. **Glass is never nested.** A glass panel's children are plain (solid-ish white or transparent) so the frosted effect samples the colour field, not another panel.
5. **Every scene has one signature motion** (radar ping, beams into an orb, fanned cards, a click, liquid filling, a burst, a riding dot) on top of the shared entrance language.

## Colour

| Token | Value | Use |
|---|---|---|
| `--base` | `#EEF0FF` | Field behind the blobs |
| `--ink` | `#14123A` | Headlines, numbers |
| `--ink-2` | `#4B4A72` | Captions, labels |
| `--pink` | `#FF4FB3` | Spectrum start, warm highlights |
| `--violet` | `#7B5CFF` | Primary brand hue |
| `--blue` | `#2E7BFF` | Data, links |
| `--cyan` | `#16D0F0` | Data, glow |
| `--mint` | `#22E3A0` | Positive results |
| `--lemon` | `#FFE14D` | Sparks, confetti only |
| `--grad` | pink → violet → blue → cyan | Gradient text, pills, liquid |

Losing values are greyed and struck through, never red or orange.

## Glass recipe

```css
background: linear-gradient(135deg, rgba(255,255,255,.62), rgba(255,255,255,.22));
backdrop-filter: blur(1.4cqw) saturate(1.9);
box-shadow: inset 0 1px 0 rgba(255,255,255,.95), 0 1.4cqw 3.4cqw rgba(48,30,140,.16);
/* ::after — 1px rim: white top-left fading to cyan/pink bottom-right (mask-composite) */
/* ::before — a specular sheen that sweeps across once as the panel lands */
```
Never put glass inside an element whose `opacity`, `filter` or `mask` animates — that makes it a backdrop root and the blur stops sampling the colour field.

## Type

| Role | Face | Size | Notes |
|---|---|---|---|
| Headline | Unbounded 600 | `4.2cqw`, line-height 1.05, `-0.02em` | Words rise in one by one; key word in gradient |
| Big numerals | Unbounded 600 | `3.6–7cqw` | Tabular, fixed-width boxes for count-ups |
| Body / names | Figtree 500–700 | `1.5–2.1cqw` | |
| Labels / data | Martian Mono 400–500 | `1–1.2cqw`, UPPERCASE, `.06em` | Chapter bar, axes, pills |

## Layout

- 16:9 stage, all sizes in `cqw` so the page and the 1920×1080 render match.
- Chapter bar: a glass pill across the top (4% inset). Headline top-left at 14%.
- Content between 30% and 92%; glass radius `1.4–1.8cqw`, pills fully rounded.

## Motion

- Entrances: `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)`; glass lands with opacity, `translateY(2.5cqw)`, `scale(.96)` and a `.6cqw` blur clearing.
- Paths and lines: `--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)`; loops (flow, spin, drift) are linear or ease-in-out alternates.
- Background blobs drift on 14–23 s loops and change colour at each scene change (0.9 s blend).
- Everything is seekable: scene animations are positioned from the scene clock, background animations from the global clock, so live playback and the MP4 render are frame-identical.
- Reduced motion: no drift, no loops, no bursts; panels fade in place; data still fills.
