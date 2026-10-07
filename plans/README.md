# Animation plans — `google-ads-ecommerce-explainer.html`

| # | Title | Severity | Status |
|---|---|---|---|
| 001 | Consolidate easing into shared tokens | LOW | DONE |
| 002 | Replace the half-scale bouncy `pop` with a subtle scale-in | HIGH | DONE |
| 003 | Crossfade between scenes instead of hard-cutting | MEDIUM | DONE |
| 004 | Honour prefers-reduced-motion across the explainer | MEDIUM | DONE |

**Order**: 001 → 002 → 003 → 004 (002–004 use the `--ease-out` token from 001; 004 overrides `sceneOut` from 003).

Not yet planned from the audit: compositor-only typing/glow/progress bar (#5), `text-decoration` snap in `dim` (#6), and the missed opportunities (count-up numbers, funnel flow, button press feedback).
