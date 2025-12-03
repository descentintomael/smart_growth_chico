import { MapContainer as LeafletMapContainer, TileLayer, ZoomControl } from 'react-leaflet'
import { useLayerStore } from '@/stores/layerStore'
import { LAYER_CONFIGS } from '@/data/layerConfig'
import { useGeoJSON } from '@/hooks/useGeoJSON'
import { GeoJSONLayer } from './GeoJSONLayer'

// Chico, CA coordinates
const CHICO_CENTER: [number, number] = [39.7285, -121.8375]
const DEFAULT_ZOOM = 12

/**
 * Renders a layer if it's visible and data is available
 */
function LayerRenderer({ layerId }: { layerId: string }) {
  const config = LAYER_CONFIGS.find(c => c.id === layerId)
  const visibleLayers = useLayerStore(state => state.visibleLayers)
  const layerOpacity = useLayerStore(state => state.layerOpacity)

  const isVisible = visibleLayers.has(layerId)
  const opacity = layerOpacity[layerId] ?? 1

  const { data, loading, error } = useGeoJSON(
    config?.dataUrl ?? '',
    isVisible && !!config
  )

  if (!config || !isVisible || loading || error || !data) {
    return null
  }

  return <GeoJSONLayer config={config} data={data} opacity={opacity} />
}

export function MapContainer() {
  return (
    <LeafletMapContainer
      center={CHICO_CENTER}
      zoom={DEFAULT_ZOOM}
      zoomControl={false}
      className="h-full w-full"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        subdomains="abcd"
        maxZoom={20}
      />

      {/* Render all configured layers */}
      {LAYER_CONFIGS.map(config => (
        <LayerRenderer key={config.id} layerId={config.id} />
      ))}

      <ZoomControl position="bottomright" />
    </LeafletMapContainer>
  )
}
