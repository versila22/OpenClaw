# Navigation Patterns Reference

## Apple HIG Navigation Patterns

### Tab Bar (Bottom Nav) — Recommended for mobile apps
- 3-5 items maximum
- Always visible (persistent)
- Icons + labels ≤ 3 words
- Active state clearly indicated
- Height: 49pt (iPhone) + safe area

### Navigation Bar (Top)
- Title centered or left-aligned
- Back button on left (← chevron + parent title)
- Actions on right (max 2 icons)
- Avoid custom hamburger menus when bottom nav works

### Sidebar / Drawer
- Left edge swipe to open (iOS standard)
- Overlay with 40-50% opacity backdrop
- Width: 80% of screen max (or 320px)
- Close on backdrop tap or navigation

## Material Design 3

### Navigation Rail (tablet/desktop)
- Left side, 80px wide
- Icons only (collapsed) or icons + labels
- FAB at top optional

### Navigation Drawer
- Standard: persistent on large screens
- Modal: overlay on small screens

## Red Flags
- Hamburger menu as ONLY navigation → hidden discoverability
- Navigation buried in settings
- Back button behavior inconsistent
- Deep navigation (>3 levels) without breadcrumbs
- No way to get to home from any screen

## Bottom Nav (Tailwind/React)
```tsx
// Fixed bottom nav — mobile only
<nav className="fixed bottom-0 left-0 right-0 md:hidden bg-background border-t z-50 
                pb-[env(safe-area-inset-bottom)]">
  <div className="flex items-center justify-around h-14">
    {/* 4 items max */}
  </div>
</nav>
// Add pb-14 to main content to avoid overlap
```
