# Accessibility Reference (WCAG 2.2)

## Contrast Ratios
| Level | Normal text | Large text (18pt/14pt bold) |
|-------|-------------|----------------------------|
| AA (minimum) | 4.5:1 | 3:1 |
| AAA (enhanced) | 7:1 | 4.5:1 |

Tools: https://webaim.org/resources/contrastchecker/

## Focus Management
- All interactive elements must have visible focus ring
- Never `outline: none` without a custom focus style
- Tailwind: `focus-visible:ring-2 focus-visible:ring-primary`
- Dialogs: focus must move to dialog on open, return on close
- Tab order must be logical (matches visual order)

## ARIA
- Use semantic HTML first (button, nav, main, aside, header)
- `aria-label` when icon-only buttons
- `aria-live="polite"` for dynamic content (toast notifications, errors)
- `aria-expanded` on hamburger/accordion toggles
- `role="dialog"` + `aria-modal="true"` on modals

## Screen Reader
- Images: `alt=""` (empty) for decorative, descriptive for informative
- Icons: `aria-hidden="true"` when beside visible text
- Form errors: `aria-describedby` linking input to error message

## Motion
- `prefers-reduced-motion` media query for animations
```css
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important; }
}
```

## Common Tailwind Accessibility Patterns
```tsx
// Icon button with label
<button aria-label="Fermer" className="focus-visible:ring-2">
  <X aria-hidden="true" />
</button>

// Skip nav link
<a href="#main" className="sr-only focus:not-sr-only">Aller au contenu</a>

// Error with aria
<Input aria-describedby="email-error" aria-invalid={!!error} />
<p id="email-error" className="text-destructive text-sm">{error}</p>
```
