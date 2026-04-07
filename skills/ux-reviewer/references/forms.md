# Forms & Input Ergonomics Reference

## Input Best Practices

### Labels
- Always visible (not just placeholder) — placeholders disappear on type
- Label above input, not beside (mobile-first)
- Required fields: * marker + legend at form top

### Input Types (mobile keyboard optimization)
| Data | Input type | Keyboard shown |
|------|-----------|----------------|
| Email | `type="email"` | @ key prominent |
| Phone | `type="tel"` | Numeric |
| Number | `type="number"` | Numeric |
| URL | `type="url"` | .com key |
| Search | `type="search"` | Search key |
| Date | `type="date"` | Native picker |
| Password | `type="password"` | Masked |

### Input Sizing
- Min height: 44px (touch target)
- Font size: 16px minimum (prevents iOS zoom)
- Padding: 12px vertical minimum

### Autocomplete
- `autocomplete="email"` / `autocomplete="current-password"` etc.
- Enables browser/password manager autofill
- Critical for accessibility and UX

## Form Validation

### Timing
- Validate on blur (not on every keystroke)
- Show success state after valid blur
- Never clear the field on error

### Error Messages
- Below the field (not tooltip)
- Specific: "L'email doit contenir @" not "Email invalide"
- Color + icon (not just color — accessibility)

### Submit Button
- Disabled state when form is invalid (optional — can be frustrating)
- Loading state during submission
- Error state if submission fails
- Never double-submit: disable after first click

## Mobile Form Layout
```tsx
// Full-width inputs on mobile
<div className="space-y-4">
  <div className="space-y-1">
    <Label htmlFor="email">Email</Label>
    <Input 
      id="email" 
      type="email" 
      autoComplete="email"
      className="w-full h-11 text-base" // 16px min, 44px height
    />
  </div>
</div>
```

## Common Mistakes
- Placeholder as label (disappears, bad accessibility)
- Input too small on mobile (< 16px font → zoom)
- Form in modal that's too tall (scroll inside modal = UX hell)
- No loading state on async submit
- Generic error messages
