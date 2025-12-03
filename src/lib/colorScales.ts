import chroma from 'chroma-js'

// Predefined color scales for different data types
export const COLOR_SCALES = {
  // Smart Growth Index: Red (Low) to Green (Excellent) - divergent
  smartGrowth: ['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60', '#1a9850'],
  // Voting: Red (NO) to Blue (YES) - divergent
  voting: ['#d73027', '#f7f7f7', '#4575b4'],
  // Priority score: Yellow to Red - sequential
  priority: ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026'],
  // Utilization: Light to dark green - sequential
  utilization: ['#edf8e9', '#bae4b3', '#74c476', '#31a354', '#006d2c'],
  // Value per acre: Purple to Green - sequential
  valuePerAcre: ['#762a83', '#9970ab', '#c2a5cf', '#a6dba0', '#5aae61', '#1b7837'],
  // Categorical colors for districts/zones
  categorical: [
    '#1f77b4',
    '#ff7f0e',
    '#2ca02c',
    '#d62728',
    '#9467bd',
    '#8c564b',
    '#e377c2',
    '#7f7f7f',
  ],
} as const

export type ColorScaleName = keyof typeof COLOR_SCALES

/**
 * Create a choropleth color function for a given scale and domain
 */
export function createColorScale(
  scaleName: ColorScaleName,
  domain: [number, number],
  steps = 5
): (value: number) => string {
  const colors = [...COLOR_SCALES[scaleName]]
  const scale = chroma.scale(colors).domain(domain).mode('lab').classes(steps)

  return (value: number) => scale(value).hex()
}

/**
 * Create a divergent scale centered on a midpoint
 */
export function createDivergentScale(
  scaleName: ColorScaleName,
  domain: [number, number],
  midpoint = 50
): (value: number) => string {
  const colors = [...COLOR_SCALES[scaleName]]
  const scale = chroma.scale(colors).domain([domain[0], midpoint, domain[1]]).mode('lab')

  return (value: number) => scale(value).hex()
}

/**
 * Get a categorical color by index
 */
export function getCategoricalColor(index: number): string {
  const colors = COLOR_SCALES.categorical
  return colors[index % colors.length] ?? colors[0]!
}

/**
 * Generate legend stops for a color scale
 */
export function getLegendStops(
  scaleName: ColorScaleName,
  domain: [number, number],
  steps = 5
): Array<{ value: number; color: string }> {
  const colorFn = createColorScale(scaleName, domain, steps)
  const stepSize = (domain[1] - domain[0]) / (steps - 1)

  return Array.from({ length: steps }, (_, i) => {
    const value = domain[0] + stepSize * i
    return { value, color: colorFn(value) }
  })
}
