# Touch & Interaction Reference

## Touch Target Sizes
- **Apple HIG**: minimum 44×44pt (~58×58px on 1.5x screens)
- **Material Design**: minimum 48×48dp
- **Recommended**: 44px height minimum, 48px preferred
- **Common mistake**: icon buttons with `p-1` (too small) → use `p-2` or `p-3`

## Tailwind Classes for Touch Targets
```css
/* Minimum */
h-11 w-11  /* 44px */

/* Comfortable */
h-12 w-12  /* 48px */
py-3 px-4  /* for text buttons */
```

## Gesture Conflicts
- Horizontal swipe lists can conflict with page scroll → use explicit swipe handles
- Pull-to-refresh: don't implement custom unless native app
- Long press: not intuitive on web → use explicit buttons instead

## Interactive Feedback
- All tappable elements need visual feedback: `active:scale-95`, `active:opacity-70`
- Hover states don't exist on touch — don't rely on them for discoverability
- Loading states must appear within 200ms of tap

## Spacing Between Targets
- Minimum 8px between adjacent tap targets (Apple HIG)
- Prefer 12px+ for comfort

## Scroll Behavior
- `scroll-smooth` for anchor links
- `-webkit-overflow-scrolling: touch` for momentum scroll (legacy, but add for safety)
- Avoid `overflow: hidden` on scroll containers — use `overflow-y: auto`

## iOS-specific
- Disable tap highlight: `-webkit-tap-highlight-color: transparent`
- Prevent text selection on long press: `user-select: none` on buttons
- Input zoom prevention: `font-size: 16px` on inputs (prevents iOS zoom on focus)
