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
      scale: ['#a50026', '#d73027', '#f46d43', '#fdae61', '#a6d96a', '#1a9850', '#006837'],
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
  {
    id: 'upzone-scenario',
    name: 'Upzone Scenario',
    description: 'What-if scenario for R1 to R2/R3 upzoning',
    dataUrl: `${import.meta.env.BASE_URL}data/upzone-scenario.geojson`,
    type: 'polygon',
    defaultVisible: false,
    group: 'planning',
    // Note: choropleth styling is handled dynamically in UpzoneScenarioLayer
    popup: {
      title: 'Parcel {APN}',
      fields: [
        { label: 'Current Zone', property: 'cur_zone' },
        { label: 'Upzone To', property: 'upzone_to', format: (v) => (v as string) || 'N/A' },
        {
          label: 'Eligible',
          property: 'upzone_elig',
          format: (v) => ((v as number) === 1 ? 'Yes' : 'No'),
        },
        { label: 'Priority Tier', property: 'upzone_tier', format: (v) => ((v as number) === 0 ? 'N/A' : String(v)) },
        { label: 'Current SG Index', property: 'cur_sg_index', format: (v) => (v as number).toFixed(1) },
        { label: 'Projected SG Index', property: 'proj_sg_index', format: (v) => (v as number).toFixed(1) },
        {
          label: 'SG Index Change',
          property: 'delta_sg_index',
          format: (v) => {
            const num = v as number
            return num >= 0 ? `+${num.toFixed(1)}` : num.toFixed(1)
          },
        },
        { label: 'New Units', property: 'delta_units', format: (v) => `+${(v as number).toLocaleString()}` },
        {
          label: 'Tax Change',
          property: 'delta_tax_total',
          format: (v) => {
            const num = v as number
            return num >= 0 ? `+$${num.toLocaleString()}` : `-$${Math.abs(num).toLocaleString()}`
          },
        },
      ],
    },
  },
  {
    id: 'commercial-viability',
    name: 'Commercial Viability',
    description: 'Business viability analysis for opportunity sites',
    dataUrl: `${import.meta.env.BASE_URL}data/commercial-viability.geojson`,
    type: 'polygon',
    defaultVisible: false,
    group: 'planning',
    // Note: choropleth styling is handled dynamically in CommercialViabilityLayer
    popup: {
      title: '{site_name}',
      fields: [
        {
          label: 'Site Acres',
          property: 'site_acres',
          format: (v) => `${(v as number).toFixed(1)} acres`,
        },
        { label: 'Current Viable Businesses', property: 'cur_biz_cnt' },
        { label: 'Viable at 100% Adoption', property: 'biz_100_cnt' },
        {
          label: 'New Businesses Enabled',
          property: 'new_biz_cnt',
          format: (v) => `+${v}`,
        },
        {
          label: 'Population (1 mi)',
          property: 'cur_pop_1mi',
          format: (v) => (v as number).toLocaleString(),
        },
      ],
    },
  },
  {
    id: 'parking-retrofit',
    name: 'Parking Retrofit',
    description: 'Convert parking lots to mixed-use housing (Hartford model)',
    dataUrl: `${import.meta.env.BASE_URL}data/parking-retrofit.geojson`,
    type: 'polygon',
    defaultVisible: false,
    group: 'retrofit',
    // Note: choropleth styling handled dynamically in RetrofitLayer
    popup: {
      title: 'Parking Lot {APN}',
      fields: [
        {
          label: 'Size',
          property: 'acres',
          format: (v) => `${(v as number).toFixed(2)} acres`,
        },
        { label: 'Potential Units', property: 'pot_units' },
        { label: 'Potential Residents', property: 'pot_resid' },
        {
          label: 'Forgone Tax Revenue',
          property: 'forgn_tax',
          format: (v) => `$${Math.round(v as number).toLocaleString()}`,
        },
      ],
    },
  },
  {
    id: 'vacant-infill',
    name: 'Vacant Infill',
    description: 'Develop vacant parcels (South Bend model)',
    dataUrl: `${import.meta.env.BASE_URL}data/vacant-infill.geojson`,
    type: 'polygon',
    defaultVisible: false,
    group: 'retrofit',
    // Note: choropleth styling handled dynamically in RetrofitLayer
    popup: {
      title: 'Vacant Parcel {APN}',
      fields: [
        {
          label: 'Size',
          property: 'acres',
          format: (v) => `${(v as number).toFixed(2)} acres`,
        },
        { label: 'Size Category', property: 'size_cat' },
        { label: 'Zoning', property: 'Zoning' },
        { label: 'Potential Units', property: 'pot_units' },
        { label: 'Potential Residents', property: 'pot_resid' },
        {
          label: 'Tax Increase',
          property: 'tax_incr',
          format: (v) => `+$${Math.round(v as number).toLocaleString()}`,
        },
      ],
    },
  },
  {
    id: 'commercial-retrofit',
    name: 'Commercial Retrofit',
    description: 'Retrofit underutilized commercial corridors (Boston model)',
    dataUrl: `${import.meta.env.BASE_URL}data/commercial-retrofit.geojson`,
    type: 'polygon',
    defaultVisible: false,
    group: 'retrofit',
    // Note: choropleth styling handled dynamically in RetrofitLayer
    popup: {
      title: 'Commercial Parcel {APN}',
      fields: [
        {
          label: 'Size',
          property: 'acres',
          format: (v) => `${(v as number).toFixed(2)} acres`,
        },
        { label: 'Land Use', property: 'land_use' },
        { label: 'Priority', property: 'priority' },
        {
          label: 'Building Coverage',
          property: 'bldg_cov',
          format: (v) => `${(v as number).toFixed(1)}%`,
        },
        { label: 'Potential Units', property: 'pot_units' },
        { label: 'Potential Residents', property: 'pot_resid' },
        {
          label: 'Tax Increase',
          property: 'tax_incr',
          format: (v) => `+$${Math.round(v as number).toLocaleString()}`,
        },
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
