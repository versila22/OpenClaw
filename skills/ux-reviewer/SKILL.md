---
name: ux-reviewer
description: Expert UX audit and responsive design review following Apple HIG, Material Design 3, and WCAG 2.2 standards. Use when asked to audit, review, or validate the UX/UI of a web or mobile application — including mobile responsiveness, accessibility, navigation patterns, form ergonomics, touch targets, typography, and visual hierarchy. Triggers on phrases like "audite l'UX", "valide le responsive", "vérifie l'ergonomie", "UX review", "mobile-friendly", "accessibilité", "normes Apple", "HIG".
---

# UX Reviewer

Expert mobile + web UX audit following industry standards: Apple HIG, Material Design 3, WCAG 2.2, and Nielsen's 10 heuristics.

## How to Run an Audit

1. **Capture the app** — take screenshots or use canvas snapshots if available
2. **Read the codebase** — scan layout components, CSS classes, component structure
3. **Apply checklists** — run through the reference files for each dimension
4. **Prioritize findings** — CRITICAL / HIGH / MEDIUM / LOW
5. **Propose fixes** — code-level recommendations matching the existing stack

## Audit Dimensions

For each audit, cover all dimensions in `references/`:

- **Mobile responsiveness** → `references/mobile.md`
- **Touch & interaction** → `references/touch.md`  
- **Typography & spacing** → `references/typography.md`
- **Navigation patterns** → `references/navigation.md`
- **Forms & inputs** → `references/forms.md`
- **Accessibility (WCAG)** → `references/accessibility.md`
- **Visual hierarchy & color** → `references/visual.md`
- **Performance perception** → `references/performance.md`

## Output Format

```markdown
# UX Audit — [App name] — [Date]

## Score: X/10

## Executive Summary
[3-5 lines on overall quality]

## Findings

### 🔴 CRITICAL
- **[Issue title]** — [Location] — [Why it fails standard X] — [Fix]

### 🟠 HIGH
...

### 🟡 MEDIUM
...

### 🟢 GOOD
[What's done well — important for morale and to not regress]

## Recommended Fix Order
1. [Most impactful fix first]
...

## Code Snippets
[Ready-to-apply fixes in the app's stack]
```

## Stack Awareness

Before auditing, identify the stack:
- **React + Tailwind**: focus on responsive classes (sm:/md:/lg:), touch target sizing, overflow handling
- **React Native**: focus on SafeAreaView, FlatList performance, platform-specific patterns
- **Vue/Angular**: same principles, different syntax

## Quick Checks (always run)

```
□ All touch targets ≥ 44×44pt (Apple) / 48×48dp (Material)
□ Text ≥ 16px on mobile (no zoom trigger)
□ No horizontal scroll on mobile (overflow-x: hidden on root)
□ Dialogs/modals ≤ 90vh with internal scroll
□ Navigation reachable with one thumb (bottom nav or hamburger)
□ Loading states on all async operations
□ Error states with actionable messages
□ Empty states with helpful guidance
□ Color contrast ≥ 4.5:1 for body text (WCAG AA)
□ Focus visible on all interactive elements
```
