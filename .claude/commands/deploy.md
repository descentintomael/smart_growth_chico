# Deploy to GitHub Pages

Deploy the application to GitHub Pages with pre-flight checks.

## Pre-Deployment Checks

1. **Verify clean working directory**:
   ```zsh
   git status
   ```
   - Warn if uncommitted changes exist
   - Suggest committing or stashing

2. **Run type checking**:
   ```zsh
   npx tsc --noEmit
   ```
   - Abort if TypeScript errors found

3. **Run tests**:
   ```zsh
   npm run test -- --run
   ```
   - Abort if tests fail

4. **Run linting**:
   ```zsh
   npm run lint
   ```
   - Warn on lint issues (don't abort)

## Build & Deploy

5. **Build production bundle**:
   ```zsh
   npm run build
   ```
   - Verify build succeeds
   - Check bundle size (warn if > 2MB)

6. **Preview locally** (optional):
   ```zsh
   npm run preview
   ```
   - Quick manual verification

7. **Deploy to GitHub Pages**:
   ```zsh
   npm run deploy
   ```
   - Uses gh-pages package
   - Pushes to gh-pages branch

## Post-Deployment

8. **Verify deployment**:
   - Check GitHub Pages URL is accessible
   - Verify map loads correctly
   - Test on mobile viewport

9. **Report deployment status**:
   - Deployment URL
   - Build size
   - Time to deploy
   - Any warnings encountered

## GitHub Pages Configuration

Ensure `vite.config.ts` has correct base path:
```typescript
export default defineConfig({
  base: '/smart_growth_visualizer/',
  // ...
})
```

Repository settings should have:
- Pages source: gh-pages branch
- Custom domain (if applicable)
