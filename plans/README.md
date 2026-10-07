# Animation plans — `google-ads-ecommerce-explainer.html`

| # | Title | Severity | Status |
|---|---|---|---|
| 001 | Consolidate easing into shared tokens | LOW | DONE |
| 002 | Replace the half-scale bouncy `pop` with a subtle scale-in | HIGH | DONE |

**Order**: 001 → 002 (002 uses the `--ease-out` token added by 001).

Not yet planned from the audit: scene crossfade (hard cut leaves ~0.5s near-blank), `prefers-reduced-motion` coverage, compositor-only typing/glow/progress, `text-decoration` snap in `dim`.
