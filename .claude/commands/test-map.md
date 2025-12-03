# Run Map-Specific Tests

Run the complete test suite for map functionality and data validation.

## Tasks

1. **Run Vitest unit tests** for map utilities:
   ```zsh
   npm run test -- --run src/lib/
   npm run test -- --run src/hooks/
   ```
   - Color scale calculations
   - GeoJSON data processing
   - Custom hooks

2. **Run component tests**:
   ```zsh
   npm run test -- --run src/components/
   ```
   - Layer rendering
   - Legend display
   - Control panel interactions

3. **Run Playwright E2E tests** for map interactions:
   ```zsh
   npx playwright test tests/e2e/
   ```
   - Map loads at correct center/zoom
   - Layer toggles work
   - Popups display on click
   - Filters update visible features
   - Mobile responsive layout

4. **Validate GeoJSON data files**:
   ```zsh
   npm run data:validate
   ```
   - All required properties exist
   - Geometries are valid
   - Coordinates within Chico bounding box
   - No null/undefined values in key fields

5. **Run type checking**:
   ```zsh
   npx tsc --noEmit
   ```
   - Ensure no TypeScript errors

6. **Generate coverage report**:
   ```zsh
   npm run test:coverage
   ```
   - Target: 80%+ for lib/ and hooks/
   - Report coverage gaps

7. **Summary report**:
   - Total tests: passed/failed
   - Coverage percentage
   - Any data validation issues
   - Recommendations for fixes
