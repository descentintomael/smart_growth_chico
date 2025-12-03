import { useState, useEffect, useRef } from 'react'
import type { FeatureCollection, Geometry, GeoJsonProperties } from 'geojson'

interface UseGeoJSONResult<T extends GeoJsonProperties> {
  data: FeatureCollection<Geometry, T> | null
  loading: boolean
  error: Error | null
}

// Simple in-memory cache for GeoJSON data
const cache = new Map<string, FeatureCollection<Geometry, GeoJsonProperties>>()

/**
 * Hook to fetch and cache GeoJSON data
 * @param url - URL to fetch GeoJSON from
 * @param enabled - Whether to fetch (default: true)
 */
export function useGeoJSON<T extends GeoJsonProperties = GeoJsonProperties>(
  url: string,
  enabled = true
): UseGeoJSONResult<T> {
  const [data, setData] = useState<FeatureCollection<Geometry, T> | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    if (!enabled || !url) {
      return
    }

    // Check cache first
    const cached = cache.get(url)
    if (cached) {
      setData(cached as FeatureCollection<Geometry, T>)
      setLoading(false)
      setError(null)
      return
    }

    // Abort any pending request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    const controller = new AbortController()
    abortControllerRef.current = controller

    setLoading(true)
    setError(null)

    fetch(url, { signal: controller.signal })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Failed to fetch ${url}: ${response.status} ${response.statusText}`)
        }
        return response.json()
      })
      .then((geojson: FeatureCollection<Geometry, T>) => {
        // Validate it's a FeatureCollection
        if (geojson.type !== 'FeatureCollection' || !Array.isArray(geojson.features)) {
          throw new Error('Invalid GeoJSON: expected FeatureCollection')
        }

        // Cache the result
        cache.set(url, geojson)

        setData(geojson)
        setLoading(false)
      })
      .catch(err => {
        if (err.name === 'AbortError') {
          return // Ignore abort errors
        }
        setError(err instanceof Error ? err : new Error(String(err)))
        setLoading(false)
      })

    return () => {
      controller.abort()
    }
  }, [url, enabled])

  return { data, loading, error }
}

/**
 * Clear the GeoJSON cache
 * Useful for testing or when data has been updated
 */
export function clearGeoJSONCache(): void {
  cache.clear()
}

/**
 * Prefetch GeoJSON data into cache
 * @param url - URL to prefetch
 */
export async function prefetchGeoJSON(url: string): Promise<void> {
  if (cache.has(url)) {
    return
  }

  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Failed to prefetch ${url}: ${response.status}`)
  }

  const geojson = await response.json()
  cache.set(url, geojson)
}
