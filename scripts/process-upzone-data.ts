/**
 * Process upzone scenario data for the Smart Growth Visualizer
 *
 * This script:
 * 1. Loads the source GeoJSON from the research data directory
 * 2. Computes an adoption_priority field for each parcel
 * 3. Reduces coordinate precision to save file size
 * 4. Writes the processed data to public/data/
 * 5. Copies the summary JSON to public/data/
 */

import { readFileSync, writeFileSync, copyFileSync } from 'fs'
import { join } from 'path'

// Source paths
const RESEARCH_DIR =
  '/Users/seantodd/Library/Mobile Documents/iCloud~md~obsidian/Documents/Smart Growth Advocates/research-code/census-api/findings/upzone-scenario'
const SOURCE_GEOJSON = join(RESEARCH_DIR, 'Chico_UpzoneScenario.geojson')
const SOURCE_SUMMARY = join(RESEARCH_DIR, 'upzone-scenario-summary.json')

// Output paths
const OUTPUT_DIR = join(process.cwd(), 'public', 'data')
const OUTPUT_GEOJSON = join(OUTPUT_DIR, 'upzone-scenario.geojson')
const OUTPUT_SUMMARY = join(OUTPUT_DIR, 'upzone-scenario-summary.json')

interface UpzoneProperties {
  APN: string
  upzone_elig: 0 | 1
  upzone_tier: number
  sc_fiscal: number
  sc_util: number
  sc_infra: number
  sc_loc: number
  delta_sg_index: number
  [key: string]: unknown
}

interface Feature {
  type: 'Feature'
  properties: UpzoneProperties
  geometry: {
    type: string
    coordinates: number[][][] | number[][][][]
  }
}

interface FeatureCollection {
  type: 'FeatureCollection'
  name?: string
  crs?: unknown
  features: Feature[]
}

/**
 * Compute adoption priority for a parcel
 * Lower value = higher priority (adopted first)
 *
 * Priority is based on:
 * - Tier (1 is highest priority, multiplied by 1000 to ensure tier ordering)
 * - Suitability scores (higher score = adopted sooner within same tier)
 * - For non-eligible parcels, return Infinity
 */
function computeAdoptionPriority(props: UpzoneProperties): number {
  if (props.upzone_elig === 0) {
    return Infinity
  }

  // Average of suitability scores (excluding sc_zone which is always 0 for R1)
  const suitabilityScore =
    (props.sc_fiscal + props.sc_util + props.sc_infra + props.sc_loc) / 4

  // Lower priority value = adopted first
  // Tier 1 parcels range: 1000 - 100 = 900 to 1000 - 0 = 1000
  // Tier 2 parcels range: 2000 - 100 = 1900 to 2000 - 0 = 2000
  // etc.
  return props.upzone_tier * 1000 - suitabilityScore
}

/**
 * Round coordinates to 6 decimal places (~0.1m precision)
 * This significantly reduces file size
 */
function roundCoordinates(
  coords: number[] | number[][] | number[][][] | number[][][][]
): number[] | number[][] | number[][][] | number[][][][] {
  if (typeof coords[0] === 'number') {
    // Base case: [lng, lat, alt?]
    return (coords as number[]).map((c, i) =>
      i < 2 ? Math.round(c * 1e6) / 1e6 : c
    )
  }
  // Recursive case: nested arrays
  return (coords as (number[] | number[][] | number[][][])[]).map((c) =>
    roundCoordinates(c)
  ) as number[][] | number[][][] | number[][][][]
}

function main() {
  console.log('Loading source GeoJSON...')
  const sourceData = JSON.parse(
    readFileSync(SOURCE_GEOJSON, 'utf-8')
  ) as FeatureCollection

  console.log(`Processing ${sourceData.features.length} features...`)

  let eligibleCount = 0
  let minPriority = Infinity
  let maxPriority = -Infinity

  // Process each feature
  const processedFeatures = sourceData.features.map((feature) => {
    const priority = computeAdoptionPriority(feature.properties)

    if (feature.properties.upzone_elig === 1) {
      eligibleCount++
      if (priority < minPriority) minPriority = priority
      if (priority > maxPriority) maxPriority = priority
    }

    return {
      type: 'Feature' as const,
      properties: {
        ...feature.properties,
        adoption_priority: priority === Infinity ? null : priority,
      },
      geometry: {
        type: feature.geometry.type,
        coordinates: roundCoordinates(feature.geometry.coordinates),
      },
    }
  })

  // Sort by adoption_priority so the list is pre-sorted for efficient slicing
  processedFeatures.sort((a, b) => {
    const aPriority = a.properties.adoption_priority ?? Infinity
    const bPriority = b.properties.adoption_priority ?? Infinity
    return aPriority - bPriority
  })

  // Create output FeatureCollection (without CRS property - not needed for web)
  const outputData: FeatureCollection = {
    type: 'FeatureCollection',
    features: processedFeatures,
  }

  console.log(`Writing processed GeoJSON to ${OUTPUT_GEOJSON}...`)
  writeFileSync(OUTPUT_GEOJSON, JSON.stringify(outputData))

  console.log(`Copying summary JSON to ${OUTPUT_SUMMARY}...`)
  copyFileSync(SOURCE_SUMMARY, OUTPUT_SUMMARY)

  // Stats
  const originalSize = readFileSync(SOURCE_GEOJSON).length
  const outputSize = readFileSync(OUTPUT_GEOJSON).length

  console.log('\n=== Processing Complete ===')
  console.log(`Total features: ${processedFeatures.length}`)
  console.log(`Eligible parcels: ${eligibleCount}`)
  console.log(
    `Priority range: ${minPriority.toFixed(2)} - ${maxPriority.toFixed(2)}`
  )
  console.log(
    `Original size: ${(originalSize / 1e6).toFixed(2)} MB`
  )
  console.log(`Output size: ${(outputSize / 1e6).toFixed(2)} MB`)
  console.log(
    `Size reduction: ${(((originalSize - outputSize) / originalSize) * 100).toFixed(1)}%`
  )
}

main()
