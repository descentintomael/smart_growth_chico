import { describe, it, expect } from 'vitest'
import { createColorScale, createDivergentScale, getCategoricalColor, getLegendStops } from './colorScales'

describe('colorScales', () => {
  describe('createColorScale', () => {
    it('returns a function', () => {
      const scale = createColorScale('priority', [0, 100])
      expect(typeof scale).toBe('function')
    })

    it('returns valid hex colors', () => {
      const scale = createColorScale('priority', [0, 100])
      const color = scale(50)
      expect(color).toMatch(/^#[0-9a-f]{6}$/i)
    })

    it('returns different colors for different values', () => {
      const scale = createColorScale('priority', [0, 100])
      const colorLow = scale(10)
      const colorHigh = scale(90)
      expect(colorLow).not.toBe(colorHigh)
    })
  })

  describe('createDivergentScale', () => {
    it('returns a function', () => {
      const scale = createDivergentScale('voting', [0, 100], 50)
      expect(typeof scale).toBe('function')
    })

    it('handles midpoint correctly', () => {
      const scale = createDivergentScale('voting', [0, 100], 50)
      const colorLow = scale(0)
      const colorMid = scale(50)
      const colorHigh = scale(100)

      // All should be valid hex colors
      expect(colorLow).toMatch(/^#[0-9a-f]{6}$/i)
      expect(colorMid).toMatch(/^#[0-9a-f]{6}$/i)
      expect(colorHigh).toMatch(/^#[0-9a-f]{6}$/i)
    })
  })

  describe('getCategoricalColor', () => {
    it('returns valid hex colors', () => {
      const color = getCategoricalColor(0)
      expect(color).toMatch(/^#[0-9a-f]{6}$/i)
    })

    it('wraps around for large indices', () => {
      const color0 = getCategoricalColor(0)
      const color8 = getCategoricalColor(8)
      expect(color0).toBe(color8)
    })

    it('returns different colors for different indices', () => {
      const colors = [0, 1, 2, 3].map(getCategoricalColor)
      const uniqueColors = new Set(colors)
      expect(uniqueColors.size).toBe(4)
    })
  })

  describe('getLegendStops', () => {
    it('returns correct number of stops', () => {
      const stops = getLegendStops('priority', [0, 100], 5)
      expect(stops).toHaveLength(5)
    })

    it('returns stops with value and color properties', () => {
      const stops = getLegendStops('priority', [0, 100], 5)
      stops.forEach(stop => {
        expect(stop).toHaveProperty('value')
        expect(stop).toHaveProperty('color')
        expect(typeof stop.value).toBe('number')
        expect(stop.color).toMatch(/^#[0-9a-f]{6}$/i)
      })
    })

    it('starts and ends at domain boundaries', () => {
      const stops = getLegendStops('priority', [0, 100], 5)
      expect(stops[0]?.value).toBe(0)
      expect(stops[4]?.value).toBe(100)
    })
  })
})
