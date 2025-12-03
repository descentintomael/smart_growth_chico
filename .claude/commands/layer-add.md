# Add a New Map Layer

Help add a new layer to the map visualization with all required files and configuration.

## Required Argument

Provide the layer name as an argument, e.g., `/layer-add annexation`

## Tasks

1. **Create the layer component** in `src/components/layers/`:
   - Name: `{LayerName}Layer.tsx`
   - Use the existing layer pattern from `PrecinctsLayer.tsx`
   - Include GeoJSON loading with React Query
   - Add hover and click event handlers
   - Implement styling (choropleth or static)

2. **Add layer configuration** to `src/data/layerConfig.ts`:
   ```typescript
   {
     id: 'layer-id',
     name: 'Display Name',
     description: 'Layer description',
     dataUrl: '/data/layer-name.geojson',
     type: 'polygon' | 'line' | 'point',
     defaultVisible: false,
     group: 'boundaries' | 'voting' | 'planning' | 'infrastructure',
     // choropleth config if needed
     // popup config
     // style config
   }
   ```

3. **Update the LayerControl component**:
   - Import the new layer component
   - Add toggle switch in appropriate group
   - Handle visibility state

4. **Create data processing script** (if source data needs transformation):
   - Add script to `scripts/` directory
   - Update `package.json` with npm script
   - Document source data location

5. **Add TypeScript types** for layer properties:
   - Define feature properties interface in `src/types/`
   - Export and use in layer component

6. **Create unit tests**:
   - Add `{LayerName}Layer.test.tsx` to `tests/unit/`
   - Test rendering, click handlers, style generation

7. **Update documentation**:
   - Add layer to the table in `CLAUDE.md`
   - Document choropleth colors if applicable
