#!/usr/bin/env npx tsx
/**
 * Process opportunity sites - merge CSV data with GeoJSON geometry
 */

import { readFileSync, writeFileSync } from 'fs'
import { join } from 'path'
import type { FeatureCollection, Feature, Geometry } from 'geojson'

// Source paths
const SOURCE_DIR = '/Users/seantodd/Library/Mobile Documents/iCloud~md~obsidian/Documents/Smart Growth Advocates'
const CSV_FILE = join(SOURCE_DIR, 'research-code/census-api/findings/opportunity-sites/opportunity-sites-data.csv')
const GEOJSON_FILE = join(process.cwd(), 'public', 'data', 'opportunity-sites.geojson')

interface CsvRow {
  site_id: number
  name: string
  type: string
  acres: number
  dist_downtown_mi: number
  predominant_zone: string
  parks_5min: boolean
  parks_10min: boolean
  infra_age: string
  potential_units: number
  priority_score: number
}

interface SiteProperties {
  site_id: number
  name: string
  type: string
  acres: number
  dist_downtown_mi: number
  predominant_zone: string
  parks_5min: boolean
  parks_10min: boolean
  infra_age: string
  potential_units: number
  priority_score: number
}

function parseCsv(content: string): CsvRow[] {
  const lines = content.trim().split('\n')
  const headers = lines[0].split(',')

  return lines.slice(1).map(line => {
    const values = line.split(',')
    const row: Record<string, unknown> = {}

    headers.forEach((header, index) => {
      const value = values[index]
      // Parse numbers and booleans
      if (header === 'site_id' || header === 'priority_score') {
        row[header] = parseInt(value, 10)
      } else if (header === 'acres' || header === 'dist_downtown_mi' || header === 'potential_units') {
        row[header] = parseFloat(value)
      } else if (header === 'parks_5min' || header === 'parks_10min') {
        row[header] = value === 'True'
      } else {
        row[header] = value
      }
    })

    return row as CsvRow
  })
}

function main() {
  console.log('📊 Processing Opportunity Sites')
  console.log('=' .repeat(50))

  // Read CSV data
  console.log('\n📂 Reading CSV data...')
  const csvContent = readFileSync(CSV_FILE, 'utf-8')
  const csvData = parseCsv(csvContent)
  console.log(`   Found ${csvData.length} sites in CSV`)

  // Create lookup by name
  const dataByName = new Map<string, CsvRow>()
  for (const row of csvData) {
    dataByName.set(row.name, row)
  }

  // Read existing GeoJSON
  console.log('\n📂 Reading GeoJSON...')
  const geojson = JSON.parse(readFileSync(GEOJSON_FILE, 'utf-8')) as FeatureCollection

  console.log(`   Found ${geojson.features.length} features`)

  // Merge properties
  console.log('\n🔀 Merging properties...')
  let matched = 0
  let unmatched = 0

  const enhancedFeatures: Feature<Geometry, SiteProperties>[] = geojson.features.map(feature => {
    const originalName = feature.properties?.Name as string
    const csvRow = dataByName.get(originalName)

    if (csvRow) {
      matched++
      return {
        type: 'Feature' as const,
        geometry: feature.geometry,
        properties: {
          site_id: csvRow.site_id,
          name: csvRow.name,
          type: csvRow.type,
          acres: csvRow.acres,
          dist_downtown_mi: csvRow.dist_downtown_mi,
          predominant_zone: csvRow.predominant_zone,
          parks_5min: csvRow.parks_5min,
          parks_10min: csvRow.parks_10min,
          infra_age: csvRow.infra_age,
          potential_units: csvRow.potential_units,
          priority_score: csvRow.priority_score,
        },
      }
    } else {
      unmatched++
      console.log(`   ⚠️  No match for: ${originalName}`)
      // Return with default properties
      return {
        type: 'Feature' as const,
        geometry: feature.geometry,
        properties: {
          site_id: parseInt(feature.properties?.Number_ID || '0', 10),
          name: originalName,
          type: feature.properties?.Type || 'Unknown',
          acres: feature.properties?.Acres || 0,
          dist_downtown_mi: 0,
          predominant_zone: 'Unknown',
          parks_5min: false,
          parks_10min: false,
          infra_age: 'Unknown',
          potential_units: 0,
          priority_score: 50,
        },
      }
    }
  })

  console.log(`   ✅ Matched: ${matched}`)
  console.log(`   ⚠️  Unmatched: ${unmatched}`)

  // Write enhanced GeoJSON
  const enhanced: FeatureCollection<Geometry, SiteProperties> = {
    type: 'FeatureCollection',
    features: enhancedFeatures,
  }

  writeFileSync(GEOJSON_FILE, JSON.stringify(enhanced, null, 2))

  const fileSizeKB = (readFileSync(GEOJSON_FILE).length / 1024).toFixed(1)
  console.log(`\n✅ Updated: ${GEOJSON_FILE}`)
  console.log(`   Size: ${fileSizeKB} KB`)

  // Show sample
  const sample = enhanced.features[0]?.properties
  if (sample) {
    console.log('\n📋 Sample properties:')
    console.log(`   Name: ${sample.name}`)
    console.log(`   Priority Score: ${sample.priority_score}`)
    console.log(`   Potential Units: ${sample.potential_units.toLocaleString()}`)
  }

  console.log('\n✨ Processing complete!')
}

main()
