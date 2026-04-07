# Visual Hierarchy & Color Reference

## Typography Scale (Mobile)
| Element | Size | Weight | Line height |
|---------|------|--------|-------------|
| H1 | 28-32px | 700 | 1.2 |
| H2 | 22-24px | 600 | 1.3 |
| H3 | 18-20px | 600 | 1.4 |
| Body | 16px | 400 | 1.5 |
| Secondary | 14px | 400 | 1.5 |
| Caption | 12px | 400 | 1.4 |

Never use < 12px. Prefer 16px for body on mobile.

## Spacing System (8px base)
- 4px (tight), 8px, 12px, 16px, 24px, 32px, 48px, 64px
- Use consistent scale — don't mix 10px and 12px arbitrarily
- Tailwind: p-1(4px), p-2(8px), p-3(12px), p-4(16px), p-6(24px), p-8(32px)

## Color Usage
- Primary: CTAs, active states, key info
- Destructive: delete, error, critical alerts
- Warning: caution, approaching limits
- Success: confirmation, completion
- Muted/secondary: supporting text, disabled states
- Background hierarchy: bg-background > bg-card > bg-muted

## Visual Hierarchy Rules
1. One primary action per screen (most prominent button)
2. Secondary actions visually subordinate (outline/ghost variant)
3. Destructive actions always require confirmation
4. Related items grouped (card or section)
5. Important info above the fold

## Dark Theme Specifics
- Avoid pure white (#fff) on dark — use `zinc-100` or `slate-100`
- Shadows less effective on dark → use borders instead
- Colored text on dark: prefer pastel/muted variants
- Card elevation: subtle border, not shadow

## Status Indicators
| Status | Color | Icon |
|--------|-------|------|
| Success | green | ✓ CheckCircle |
| Warning | amber/yellow | ⚠ AlertTriangle |
| Error | red | ✗ XCircle |
| Info | blue | ℹ Info |
| Loading | neutral | ⟳ Loader2 (spin) |

Always use icon + color (never color alone — colorblind users).

## Red Flags
- Too many primary buttons on one screen
- Text on busy background without overlay
- Icons without labels (unless universally recognized)
- Inconsistent spacing
- Centered body text > 2 lines (hard to read)
