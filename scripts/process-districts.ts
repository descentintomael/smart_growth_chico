#!/usr/bin/env npx tsx
/**
 * Process council districts - normalize property names
 */

import { readFileSync, writeFileSync } from 'fs'
import { join } from 'path'
import type { FeatureCollection, Feature, Geometry } from 'geojson'

const GEOJSON_FILE = join(process.cwd(), 'public', 'data', 'council-districts.geojson')

interface SourceProperties {
  DISTRICT: string
  NAME: string
  COUNCILMEM: string
  TermDate: string
  Email: string
}

interface NormalizedProperties {
  district_number: number
  name: string
  council_member: string
  term_dates: string
  email: string
}

function main() {
  console.log('📊 Processing Council Districts')
  console.log('=' .repeat(50))

  // Read GeoJSON
  console.log('\n📂 Reading GeoJSON...')
  const geojson = JSON.parse(readFileSync(GEOJSON_FILE, 'utf-8')) as FeatureCollection<Geometry, SourceProperties>
  console.log(`   Found ${geojson.features.length} districts`)

  // Normalize properties
  console.log('\n🔀 Normalizing properties...')
  const normalizedFeatures: Feature<Geometry, NormalizedProperties>[] = geojson.features.map(feature => {
    const props = feature.properties
    return {
      type: 'Feature' as const,
      geometry: feature.geometry,
      properties: {
        district_number: parseInt(props.DISTRICT, 10),
        name: props.NAME,
        council_member: props.COUNCILMEM,
        term_dates: props.TermDate,
        email: props.Email,
      },
    }
  })

  // Sort by district number
  normalizedFeatures.sort((a, b) => a.properties.district_number - b.properties.district_number)

  // Write normalized GeoJSON
  const normalized: FeatureCollection<Geometry, NormalizedProperties> = {
    type: 'FeatureCollection',
    features: normalizedFeatures,
  }

  writeFileSync(GEOJSON_FILE, JSON.stringify(normalized, null, 2))

  const fileSizeKB = (readFileSync(GEOJSON_FILE).length / 1024).toFixed(1)
  console.log(`\n✅ Updated: ${GEOJSON_FILE}`)
  console.log(`   Size: ${fileSizeKB} KB`)

  // List districts
  console.log('\n📋 Districts:')
  for (const feature of normalized.features) {
    const { district_number, name, council_member } = feature.properties
    console.log(`   ${district_number}. ${name} - ${council_member}`)
  }

  console.log('\n✨ Processing complete!')
}

main()
