#!/usr/bin/env npx tsx
/**
 * Copy and merge voting GeoJSON files from source data directory
 * Merges Measure O and Measure P voting data into a single GeoJSON file
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs'
import { join } from 'path'
import type { FeatureCollection, Feature, Geometry } from 'geojson'

// Source data directory (iCloud/Obsidian)
const SOURCE_DIR = '/Users/seantodd/Library/Mobile Documents/iCloud~md~obsidian/Documents/Smart Growth Advocates/research-code/census-api/local_data'

// Target directory
const TARGET_DIR = join(process.cwd(), 'public', 'data')

// Source files
const MEASURE_O_FILE = join(SOURCE_DIR, 'measure_o_geodata_latlon.geojson')
const MEASURE_P_FILE = join(SOURCE_DIR, 'measure_p_geodata_latlon.geojson')

// Output file
const OUTPUT_FILE = join(TARGET_DIR, 'precincts-voting.geojson')

interface SourceProperties {
  PRECINCT: string
  COUNTY: string
  Precinct: number
  Registered_Voters: number
  NO_Total: number
  YES_Total: number
  Total_Votes: number
  Percent_NO: number
  Percent_YES: number
  PRECINCT_5DIGIT: string
}

interface MergedProperties {
  PRECINCT: string
  COUNTY: string
  registered_voters: number
  // Measure O
  percent_yes_o: number
  percent_no_o: number
  total_votes_o: number
  yes_total_o: number
  no_total_o: number
  // Measure P
  percent_yes_p: number
  percent_no_p: number
  total_votes_p: number
  yes_total_p: number
  no_total_p: number
}

function main() {
  console.log('📊 Smart Growth Visualizer - Data Processing')
  console.log('=' .repeat(50))

  // Ensure target directory exists
  if (!existsSync(TARGET_DIR)) {
    mkdirSync(TARGET_DIR, { recursive: true })
    console.log(`✅ Created directory: ${TARGET_DIR}`)
  }

  // Check source files exist
  if (!existsSync(MEASURE_O_FILE)) {
    console.error(`❌ Source file not found: ${MEASURE_O_FILE}`)
    process.exit(1)
  }
  if (!existsSync(MEASURE_P_FILE)) {
    console.error(`❌ Source file not found: ${MEASURE_P_FILE}`)
    process.exit(1)
  }

  console.log('\n📂 Reading source files...')

  // Read source GeoJSON files
  const measureO = JSON.parse(readFileSync(MEASURE_O_FILE, 'utf-8')) as FeatureCollection<Geometry, SourceProperties>
  const measureP = JSON.parse(readFileSync(MEASURE_P_FILE, 'utf-8')) as FeatureCollection<Geometry, SourceProperties>

  console.log(`   Measure O: ${measureO.features.length} features`)
  console.log(`   Measure P: ${measureP.features.length} features`)

  // Create lookup map for Measure P by precinct
  const measurePMap = new Map<string, SourceProperties>()
  for (const feature of measureP.features) {
    measurePMap.set(feature.properties.PRECINCT, feature.properties)
  }

  console.log('\n🔀 Merging voting data...')

  // Merge: use Measure O geometry, combine properties from both
  const mergedFeatures: Feature<Geometry, MergedProperties>[] = measureO.features.map(feature => {
    const oProps = feature.properties
    const pProps = measurePMap.get(oProps.PRECINCT)

    const mergedProps: MergedProperties = {
      PRECINCT: oProps.PRECINCT,
      COUNTY: oProps.COUNTY,
      registered_voters: oProps.Registered_Voters,
      // Measure O
      percent_yes_o: oProps.Percent_YES,
      percent_no_o: oProps.Percent_NO,
      total_votes_o: oProps.Total_Votes,
      yes_total_o: oProps.YES_Total,
      no_total_o: oProps.NO_Total,
      // Measure P (use 0 if not found)
      percent_yes_p: pProps?.Percent_YES ?? 0,
      percent_no_p: pProps?.Percent_NO ?? 0,
      total_votes_p: pProps?.Total_Votes ?? 0,
      yes_total_p: pProps?.YES_Total ?? 0,
      no_total_p: pProps?.NO_Total ?? 0,
    }

    return {
      type: 'Feature' as const,
      geometry: feature.geometry,
      properties: mergedProps,
    }
  })

  // Create merged FeatureCollection
  const merged: FeatureCollection<Geometry, MergedProperties> = {
    type: 'FeatureCollection',
    features: mergedFeatures,
  }

  // Write output
  writeFileSync(OUTPUT_FILE, JSON.stringify(merged, null, 2))

  const fileSizeKB = (readFileSync(OUTPUT_FILE).length / 1024).toFixed(1)
  console.log(`\n✅ Created: ${OUTPUT_FILE}`)
  console.log(`   Features: ${merged.features.length}`)
  console.log(`   Size: ${fileSizeKB} KB`)

  // Print sample of merged properties
  console.log('\n📋 Sample merged properties:')
  const sample = merged.features[0]?.properties
  if (sample) {
    console.log(`   Precinct: ${sample.PRECINCT}`)
    console.log(`   Measure O: ${sample.percent_yes_o.toFixed(1)}% YES, ${sample.percent_no_o.toFixed(1)}% NO`)
    console.log(`   Measure P: ${sample.percent_yes_p.toFixed(1)}% YES, ${sample.percent_no_p.toFixed(1)}% NO`)
  }

  console.log('\n✨ Data processing complete!')
}

main()
