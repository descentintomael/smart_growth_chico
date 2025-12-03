import type { LayerConfig } from '@/types'

export const LAYER_CONFIGS: LayerConfig[] = [
  {
    id: 'smart-growth-index',
    name: 'Smart Growth Index',
    description: 'Parcel-level smart growth value scores',
    dataUrl: `${import.meta.env.BASE_URL}data/smart-growth-index.geojson`,
    type: 'polygon',
    defaultVisible: true,
    group: 'planning',
    choropleth: {
      property: 'sg_index',
      scale: ['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60', '#1a9850'],
      domain: [0, 100],
      mode: 'equidistant',
      steps: 6,
      legendTitle: 'Smart Growth Index',
      formatValue: (v) => v.toFixed(0),
    },
    popup: {
      title: 'Parcel {APN}',
      fields: [
        { label: 'Smart Growth Index', property: 'sg_index', format: (v) => (v as number).toFixed(1) },
        { label: 'Tier', property: 'sg_tier' },
        { label: 'Fiscal Score', property: 'sc_fiscal', format: (v) => (v as number).toFixed(0) },
        { label: 'Utilization Score', property: 'sc_util', format: (v) => (v as number).toFixed(0) },
        { label: 'Infrastructure Score', property: 'sc_infra', format: (v) => (v as number).toFixed(0) },
        { label: 'Tax/Acre', property: 'tax_acre', format: (v) => `$${(v as number).toLocaleString()}` },
      ],
    },
  },
]

export function getLayerConfig(layerId: string): LayerConfig | undefined {
  return LAYER_CONFIGS.find((config) => config.id === layerId)
}

export function getLayersByGroup(group: LayerConfig['group']): LayerConfig[] {
  return LAYER_CONFIGS.filter((config) => config.group === group)
}
