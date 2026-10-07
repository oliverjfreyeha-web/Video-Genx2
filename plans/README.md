# Animation plans — `google-ads-ecommerce-explainer.html`

| # | Title | Severity | Status |
|---|---|---|---|
| 001 | Consolidate easing into shared tokens | LOW | DONE |
| 002 | Replace the half-scale bouncy `pop` with a subtle scale-in | HIGH | DONE |
| 003 | Crossfade between scenes instead of hard-cutting | MEDIUM | DONE |
| 004 | Honour prefers-reduced-motion across the explainer | MEDIUM | DONE |
| 005 | Move typing, glow pulse and progress bar onto transform/opacity | LOW | DONE |
| 006 | Sweep the strike-through instead of snapping it on | LOW | DONE |

**Order**: 001 → 002 → 003 → 004 → 005 → 006 (later plans use the `--ease-out` token from 001; 004's reduced-motion block is extended by 005 and 006).

Not yet planned: the missed opportunities from the audit (count-up numbers, funnel flow, button press feedback).
