# Performance Perception Reference

## Perceived Performance Rules (Doherty Threshold)
- **< 100ms**: Instant (no feedback needed)
- **100-300ms**: Fast (optional subtle feedback)
- **300ms-1s**: Noticeable — show loading indicator
- **> 1s**: Show progress bar or skeleton
- **> 10s**: Show progress + ETA + cancel option

## Loading States
```tsx
// Skeleton (preferred for content)
<div className="animate-pulse bg-muted rounded h-4 w-3/4" />

// Spinner (for actions)
<Loader2 className="animate-spin" />

// Button loading state
<Button disabled={isLoading}>
  {isLoading ? <Loader2 className="animate-spin mr-2 h-4 w-4" /> : null}
  {isLoading ? "Chargement..." : "Envoyer"}
</Button>
```

## Error States
- Network error: "Impossible de charger. Vérifiez votre connexion." + retry button
- Server error: "Une erreur est survenue. Réessayez dans quelques instants." + retry
- Empty state: illustration + message + CTA
- 404: friendly message + home link

## Optimistic UI
For frequent user actions (like, follow, toggle), update UI immediately and revert on error.
Better UX than waiting for server confirmation.

## React Query Patterns
```tsx
// Skeleton on first load, stale data + spinner on refetch
const { data, isLoading, isFetching } = useQuery(...)

if (isLoading) return <Skeleton />
return (
  <div>
    {isFetching && <SmallSpinner />}
    {data && <Content data={data} />}
  </div>
)
```

## Image Optimization
- Use `loading="lazy"` on below-fold images
- Specify width/height to prevent layout shift (CLS)
- WebP format preferred
- `object-fit: cover` for consistent image display

## Bundle Size (React/Vite)
- Warn at > 500KB chunk (Vite default)
- Use dynamic imports for large pages: `const Page = lazy(() => import('./Page'))`
- Tree shake icon libraries: import individually, not entire pack
