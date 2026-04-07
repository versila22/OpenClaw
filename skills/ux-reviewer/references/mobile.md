# Mobile Responsiveness Reference

## Breakpoints (Tailwind defaults)
- `sm`: 640px — large phones landscape
- `md`: 768px — tablets / small laptops  
- `lg`: 1024px — laptops
- `xl`: 1280px — desktops

## Key Rules

### Viewport
- Never use `width: 100vw` without `overflow-x: hidden` on a parent — causes horizontal scroll on iOS
- Use `min-h-screen` not `height: 100vh` — iOS Safari bottom bar eats viewport
- `env(safe-area-inset-bottom)` for iPhone notch/home indicator

### Layout
- Sidebars must be hidden on mobile (`hidden md:block` or overlay)
- Fixed sidebars add margin to main: `ml-0 md:ml-64` 
- Tables need `overflow-x-auto` wrapper
- Cards should stack vertically: `flex-col md:flex-row`
- Grid: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`

### Images & Media
- Always `max-w-full h-auto` on images
- Background images: `bg-cover bg-center`

### Dialogs/Modals
- Width: `w-[95vw] max-w-lg` — fills mobile, bounded on desktop
- Height: `max-h-[85vh] overflow-y-auto` — scrollable content
- On mobile: consider full-screen sheets instead of centered dialogs

### Common Issues
| Issue | Fix |
|-------|-----|
| Horizontal scroll | `overflow-x: hidden` on body/root |
| Sidebar covers content | Overlay + backdrop on mobile |
| Dialog too wide | `w-[95vw]` |
| Dialog too tall | `max-h-[85vh] overflow-y-auto` |
| Fixed element under nav bar | `pb-safe` or `padding-bottom: env(safe-area-inset-bottom)` |
| Text too small | `text-base` minimum on mobile (16px) |
