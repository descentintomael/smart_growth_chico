import type { LayerConfig } from '@/types'

export const LAYER_CONFIGS: LayerConfig[] = [
  {
    id: 'precincts-measure-o',
    name: 'Measure O Voting',
    description: 'Precinct-level voting results for Measure O',
    dataUrl: `${import.meta.env.BASE_URL}data/precincts-voting.geojson`,
    type: 'polygon',
    defaultVisible: true,
    group: 'voting',
    choropleth: {
      property: 'percent_yes_o',
      scale: ['#d73027', '#4575b4'],
      domain: [0, 100],
      mode: 'equidistant',
      steps: 7,
      legendTitle: 'Measure O - % YES',
      formatValue: (v) => `${v.toFixed(1)}%`,
    },
    popup: {
      title: 'Precinct {PRECINCT}',
      fields: [
        { label: 'YES', property: 'percent_yes_o', format: (v) => `${(v as number).toFixed(1)}%` },
        { label: 'NO', property: 'percent_no_o', format: (v) => `${(v as number).toFixed(1)}%` },
        { label: 'Total Votes', property: 'total_votes_o' },
      ],
    },
  },
  {
    id: 'precincts-measure-p',
    name: 'Measure P Voting',
    description: 'Precinct-level voting results for Measure P',
    dataUrl: `${import.meta.env.BASE_URL}data/precincts-voting.geojson`,
    type: 'polygon',
    defaultVisible: false,
    group: 'voting',
    choropleth: {
      property: 'percent_yes_p',
      scale: ['#d73027', '#4575b4'],
      domain: [0, 100],
      mode: 'equidistant',
      steps: 7,
      legendTitle: 'Measure P - % YES',
      formatValue: (v) => `${v.toFixed(1)}%`,
    },
    popup: {
      title: 'Precinct {PRECINCT}',
      fields: [
        { label: 'YES', property: 'percent_yes_p', format: (v) => `${(v as number).toFixed(1)}%` },
        { label: 'NO', property: 'percent_no_p', format: (v) => `${(v as number).toFixed(1)}%` },
        { label: 'Total Votes', property: 'total_votes_p' },
      ],
    },
  },
  {
    id: 'opportunity-sites',
    name: 'Opportunity Sites',
    description: 'Prioritized infill development sites',
    dataUrl: `${import.meta.env.BASE_URL}data/opportunity-sites.geojson`,
    type: 'polygon',
    defaultVisible: false,
    group: 'planning',
    choropleth: {
      property: 'priority_score',
      scale: ['#ffffb2', '#bd0026'],
      domain: [0, 100],
      mode: 'quantile',
      steps: 5,
      legendTitle: 'Priority Score',
      formatValue: (v) => v.toFixed(0),
    },
    popup: {
      title: '{name}',
      fields: [
        { label: 'Priority Score', property: 'priority_score' },
        { label: 'Acres', property: 'acres', format: (v) => (v as number).toFixed(1) },
        { label: 'Potential Units', property: 'potential_units', format: (v) => Math.round(v as number).toLocaleString() },
        { label: 'Distance to Downtown', property: 'dist_downtown_mi', format: (v) => `${(v as number).toFixed(1)} mi` },
        { label: 'Zone', property: 'predominant_zone' },
      ],
    },
  },
  {
    id: 'council-districts',
    name: 'Council Districts',
    description: 'City Council district boundaries',
    dataUrl: `${import.meta.env.BASE_URL}data/council-districts.geojson`,
    type: 'polygon',
    defaultVisible: false,
    group: 'demographics',
    style: {
      fillOpacity: 0.2,
      weight: 2,
    },
    popup: {
      title: '{name}',
      fields: [
        { label: 'Council Member', property: 'council_member' },
        { label: 'Term', property: 'term_dates' },
        { label: 'Email', property: 'email' },
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
