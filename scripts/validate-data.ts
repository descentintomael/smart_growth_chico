import { readFileSync, existsSync, readdirSync, statSync } from 'fs'
import { join } from 'path'

const DATA_DIR = join(process.cwd(), 'public', 'data')

interface ValidationResult {
  file: string
  exists: boolean
  valid: boolean
  featureCount?: number
  errors: string[]
  warnings: string[]
}

const REQUIRED_PROPERTIES: Record<string, string[]> = {
  'precincts-voting.geojson': ['PRECINCT', 'percent_yes_o', 'percent_yes_p'],
  'council-districts.geojson': ['district_number'],
  'opportunity-sites.geojson': ['site_id', 'name', 'priority_score', 'acres'],
  'parks.geojson': ['name'],
}

function validateGeoJSON(filePath: string, requiredProps: string[]): ValidationResult {
  const fileName = filePath.split('/').pop() ?? filePath
  const result: ValidationResult = {
    file: fileName,
    exists: false,
    valid: false,
    errors: [],
    warnings: [],
  }

  if (!existsSync(filePath)) {
    result.errors.push('File does not exist')
    return result
  }

  result.exists = true

  try {
    const content = readFileSync(filePath, 'utf-8')
    const geojson = JSON.parse(content)

    if (geojson.type !== 'FeatureCollection') {
      result.errors.push(`Expected FeatureCollection, got ${geojson.type}`)
      return result
    }

    if (!Array.isArray(geojson.features)) {
      result.errors.push('Missing features array')
      return result
    }

    result.featureCount = geojson.features.length

    if (result.featureCount === 0) {
      result.warnings.push('GeoJSON has no features')
    }

    // Check required properties on first feature
    if (result.featureCount !== undefined && result.featureCount > 0) {
      const firstFeature = geojson.features[0]
      const properties = firstFeature.properties ?? {}

      for (const prop of requiredProps) {
        if (!(prop in properties)) {
          result.errors.push(`Missing required property: ${prop}`)
        }
      }
    }

    result.valid = result.errors.length === 0
  } catch (error) {
    result.errors.push(`Parse error: ${error instanceof Error ? error.message : String(error)}`)
  }

  return result
}

function main() {
  console.log('\\n📁 Validating GeoJSON data files...\\n')

  if (!existsSync(DATA_DIR)) {
    console.log(`❌ Data directory does not exist: ${DATA_DIR}`)
    console.log('   Run data processing scripts to generate files.\\n')
    process.exit(1)
  }

  const files = readdirSync(DATA_DIR).filter((f) => f.endsWith('.geojson'))

  if (files.length === 0) {
    console.log('⚠️  No GeoJSON files found in public/data/')
    console.log('   Run data processing scripts to generate files.\\n')
    process.exit(0)
  }

  const results: ValidationResult[] = []

  // Validate expected files
  for (const [fileName, requiredProps] of Object.entries(REQUIRED_PROPERTIES)) {
    const filePath = join(DATA_DIR, fileName)
    results.push(validateGeoJSON(filePath, requiredProps))
  }

  // Check for any extra files
  for (const file of files) {
    if (!(file in REQUIRED_PROPERTIES)) {
      const filePath = join(DATA_DIR, file)
      const stats = statSync(filePath)
      console.log(`📄 ${file} (${(stats.size / 1024).toFixed(1)} KB) - extra file`)
    }
  }

  // Print results
  let hasErrors = false
  for (const result of results) {
    const icon = result.valid ? '✅' : result.exists ? '⚠️' : '❌'
    const status = result.valid
      ? `valid (${result.featureCount} features)`
      : result.errors.join(', ')

    console.log(`${icon} ${result.file}: ${status}`)

    for (const warning of result.warnings) {
      console.log(`   ⚠️  ${warning}`)
    }

    if (!result.valid) hasErrors = true
  }

  console.log('')

  if (hasErrors) {
    console.log('❌ Validation failed. Fix errors before building.\\n')
    process.exit(1)
  } else {
    console.log('✅ All data files validated successfully.\\n')
  }
}

main()
