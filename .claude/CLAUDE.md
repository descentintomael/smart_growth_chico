# Smart Growth Visualizer

Interactive map visualization for Smart Growth Advocates research data in Chico, CA.

## Project Overview

This application displays voting precincts, opportunity sites, council districts, electoral data, demographics, and infrastructure metrics using OpenStreetMap with Leaflet.

**Stack:** React 18 + Vite + TypeScript + Leaflet + Tailwind CSS
**Hosting:** GitHub Pages

## Architecture

```
src/
├── components/
│   ├── map/           # MapContainer, BaseMap, LayerControl, Legend
│   ├── layers/        # PrecinctsLayer, DistrictsLayer, OpportunitySitesLayer, etc.
│   ├── panels/        # InfoPanel, FilterPanel, DataPanel
│   └── ui/            # Shared UI components
├── hooks/             # useGeoJSON, useLayerVisibility, useChoropleth
├── stores/            # Zustand stores (layer, filter, selection state)
├── lib/               # Utilities (colorScales, dataProcessing, mapUtils)
├── types/             # TypeScript type definitions
└── data/              # Layer configuration, color schemes
```

## Data Sources

Research data is located at:
```
/Users/seantodd/Library/Mobile Documents/iCloud~md~obsidian/Documents/Smart Growth Advocates/
```

| Data | Source Path |
|------|-------------|
| Precincts | `resources/chico-data/gis/precincts/mprec_007_p24_v01.geojson` |
| Voting (O) | `research-code/census-api/local_data/measure_o_processed.csv` |
| Voting (P) | `research-code/census-api/local_data/measure_p_processed.csv` |
| Opportunity Sites | `research-code/census-api/findings/opportunity-sites/opportunity-sites-data.csv` |
| District Mapping | `research-code/census-api/district-tract-mapping.json` |
| Zoning Stats | `research-code/census-api/findings/zoning-density/zoning-density-statistics.csv` |

Processed data for the web app is stored in `public/data/`.

## Coding Conventions

### React/TypeScript
- Use functional components with hooks
- Prefer named exports over default exports
- Use TypeScript strict mode
- Define prop types with interfaces, not type aliases
- Colocate component-specific types in the same file

### Leaflet Patterns
- Use React-Leaflet components where possible
- For performance-critical layers, use native Leaflet with useMap() hook
- Always clean up map listeners in useEffect cleanup functions
- Use GeoJSON key prop to force re-render on data changes

### State Management
- Use Zustand for global state (layer visibility, filters, selection)
- Use React Query (TanStack Query) for GeoJSON data fetching
- Keep component-local state with useState for UI-only state

### Styling
- Use Tailwind CSS utility classes
- Override Leaflet styles in `src/styles/leaflet-overrides.css`
- Use chroma.js for choropleth color scales

## Testing Requirements

- Unit tests for utility functions (lib/) using Vitest
- Component tests for UI components using Testing Library
- E2E tests for map interactions using Playwright
- Data validation tests to ensure GeoJSON integrity

Run tests:
```zsh
npm run test          # Unit tests
npm run test:watch    # Watch mode
npm run test:coverage # Coverage report
npx playwright test   # E2E tests
```

## Deployment

The app deploys to GitHub Pages via GitHub Actions.

Manual deployment:
```zsh
npm run build
npm run deploy
```

The `vite.config.ts` must set the correct `base` path for GitHub Pages.

---

## Command Allowlist

Commands pre-approved for execution without confirmation.

### Development Commands
- `npm run dev` - Start development server
- `npm run build` - Production build
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Auto-fix lint issues
- `npm run format` - Run Prettier
- `npm run test` - Run Vitest tests
- `npm run test:*` - All test variations (watch, coverage, ui)
- `npx vitest *` - Direct Vitest invocation
- `npx playwright test *` - Run Playwright E2E tests
- `npx tsc --noEmit` - Type check without emit
- `npx tsc *` - TypeScript compiler variations
- `npx prettier *` - Prettier formatting
- `npx eslint *` - ESLint checking

### Data Processing Commands
- `npm run data:*` - All data processing scripts
- `python scripts/*.py` - Python data processing
- `python3 scripts/*.py` - Python 3 data processing
- `ogr2ogr *` - GDAL shapefile conversion
- `node scripts/*.ts` - Node script execution
- `npx tsx scripts/*.ts` - TypeScript script execution

### Package Management
- `npm install` - Install dependencies
- `npm install *` - Install specific packages
- `npm uninstall *` - Remove packages
- `npm list *` - List packages
- `npm outdated` - Check outdated packages
- `npm update *` - Update packages
- `npm ci` - Clean install

### Git Commands (Read-Only)
- `git status` - Working tree status
- `git log *` - Commit history
- `git show *` - Show commits/objects
- `git diff *` - Show changes
- `git branch *` - List/manage branches
- `git remote *` - Remote repository info
- `git rev-parse *` - Parse revisions
- `git config --get *` - Read config values

### Git Commands (Local Modifications)
- `git add *` - Stage changes
- `git commit *` - Create commits
- `git checkout *` - Switch branches/restore
- `git fetch *` - Download from remote
- `git pull *` - Fetch and merge
- `git stash *` - Stash changes
- `git reset *` - Reset HEAD
- `git rebase *` - Rebase commits
- `git merge *` - Merge branches
- `git tag *` - Manage tags

### BD Issue Tracking
- `bd *` - All beads commands (init, list, create, update, close, show, ready, dep, sync, info, doctor)

### Deployment Commands
- `npm run deploy` - Deploy to GitHub Pages
- `gh-pages *` - gh-pages CLI
- `gh pr *` - GitHub CLI PR operations (read)
- `gh issue *` - GitHub CLI issue operations (read)
- `gh repo view *` - View repo info

### File Operations (Read-Only)
- `eza *` - Modern ls
- `fd *` - Find files
- `rg *` - Ripgrep search
- `bat *` - View files
- `tree *` - Directory tree
- `wc *` - Word/line count
- `head *` - View file start
- `tail *` - View file end

### Directory Navigation
- `z *` - Zoxide navigation
- `pwd` - Current directory
- `ls *` - List files
- `l *` - ls alias
- `ll *` - ls long format
- `la *` - ls all files

### Utility Commands
- `which *` - Locate commands
- `type *` - Command type
- `echo *` - Print text (for debugging)
- `date` - Current date/time
- `open *` - Open files/URLs
- `jq *` - JSON processing
- `curl * --head` - HTTP headers only
- `curl * -I` - HTTP headers only

---

## Slash Commands

Custom commands available for this project:

- `/data-status` - Check data processing pipeline status
- `/layer-add` - Add a new map layer with all required files
- `/test-map` - Run map-specific tests
- `/deploy` - Deploy to GitHub Pages

---

## Issue Tracking

This project uses BD (Beads) for issue tracking. The `.beads/` directory contains the SQLite database.

```zsh
bd list                    # List all issues
bd ready                   # Show unblocked issues
bd show <id>               # Show issue details
bd create "title" -p <0-4> # Create issue (0=highest priority)
bd update <id> --status in_progress
bd close <id> --reason "description"
```

---

## Map Configuration

**Center:** Chico, CA (39.7285, -121.8375)
**Default Zoom:** 12
**Tile Provider:** OpenStreetMap

### Choropleth Color Scales

| Layer | Scale | Palette |
|-------|-------|---------|
| Voting (Measure O/P) | Divergent | RdYlBu (Red=NO, Blue=YES) |
| Priority Score | Sequential | YlOrRd |
| Utilization % | Sequential | Greens |
| Value per Acre | Sequential | PuBuGn |
| Districts/Zones | Categorical | Set2 |
