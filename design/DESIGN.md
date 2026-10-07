# DESIGN.md — "Ledger"

An original editorial style for short explainer videos: printed-annual-report calm, not app-UI gloss. Every scene in `google-ads-ecommerce-explainer.html` follows these rules.

## Principles

1. **Print, not app.** Flat paper, ink hairlines, no drop shadows, no glows, no gradients, no emoji.
2. **One accent, used once per scene.** Vermilion marks the single thing the viewer should look at. Everything else is ink.
3. **Type does the heavy lifting.** Big serif headlines carry the story; mono labels carry the data.
4. **Left-aligned grid, uneven layouts.** Headline top-left on a fixed baseline; content varies per scene (columns, table, diagram, chart) so scenes don't repeat one card template.
5. **Drawn, not stock.** Products and icons are custom line drawings in one stroke weight.

## Colour

| Token | Value | Use |
|---|---|---|
| `--paper` | `#F2EEE5` | Stage background |
| `--paper-2` | `#E8E2D4` | Inset panels, empty bars |
| `--ink` | `#151412` | Text, strokes, primary bars |
| `--ink-2` | `#6B665C` | Secondary text, captions |
| `--rule` | `rgba(21,20,18,.16)` | Hairlines, grid |
| `--accent` | `#E4572E` | The one highlight per scene |
| `--accent-soft` | `rgba(228,87,46,.12)` | Accent fills (area under a line) |

Losing values are never red: they are drawn as **hatched outlines** or **struck through** in ink.

## Type

| Role | Face | Size (stage-relative) | Notes |
|---|---|---|---|
| Headline | Instrument Serif 400 | `4.8cqw`, line-height 1 | One word in *italic* carries the idea |
| Big numerals | Instrument Serif 400 | `4–7.5cqw` | Tabular via fixed-width boxes |
| Body / names | Geist 500–600 | `1.6–2.2cqw` | |
| Labels / data | Geist Mono 400–500 | `1.1–1.4cqw`, UPPERCASE, `letter-spacing:.08em` | Kickers, axis labels, captions |

## Layout

- Stage is 16:9; all sizes in `cqw` so the HTML and the 1920×1080 render match exactly.
- Outer margin `5%` left/right. Chrome row at `5.4%` from top: series kicker left, `NN / 07 — SECTION` right.
- Headline at `13%` from top, left-aligned. Content lives between `32%` and `90%`.
- Separate things with 1px `--rule` hairlines and whitespace, not boxes. Panels, when needed: 1px ink or rule border, radius `.4cqw`.
- Paper grain overlay: fractal-noise SVG, multiply, ~45% opacity.

## Iconography

- 24×24 line icons, `stroke-width:1.5`, round caps/joins, `fill:none`, colour `currentColor`.
- Product drawings: 64×64, same stroke rules, ink only; the viewer's product gets the accent.

## Motion

- Entrances: `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)`, 0.5–0.6s, `translateY(2.5cqw)` or `scale(.92)` + opacity.
- Lines and paths draw with `--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)`.
- Constant motion (flow dots) is `linear`.
- Scene change: 0.3s crossfade with 2px blur on the outgoing scene; the incoming scene settles from `scale(1.015)` like a slow camera push.
- Reduced motion: opacity only, no movement, no loops; data still builds.
