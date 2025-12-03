# Check Data Processing Status

Check the status of all data files needed for the map visualization.

## Tasks

1. **List all GeoJSON files** in `public/data/` directory
   - Show file sizes and last modified dates
   - Use `eza -la --time-style=relative` for readable output

2. **Validate each GeoJSON file** has required properties:
   - `precincts-voting.geojson`: Precinct, percent_yes_o, percent_yes_p
   - `council-districts.geojson`: district_number, name
   - `opportunity-sites.geojson`: site_id, name, priority_score, acres, potential_units
   - `parks.geojson`: name, type
   - `zoning.geojson`: zone, utilization_pct

3. **Check source data freshness** by comparing modification times:
   - Source: `/Users/seantodd/Library/Mobile Documents/iCloud~md~obsidian/Documents/Smart Growth Advocates/`
   - Compare `research-code/census-api/local_data/` CSVs with processed GeoJSON

4. **Report missing or stale data files**:
   - List any expected files that don't exist
   - Flag files older than source data
   - Suggest `npm run data:*` commands to regenerate

5. **Summarize data readiness**:
   - Total features per layer
   - Any validation errors found
   - Recommended actions
