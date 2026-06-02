#!/usr/bin/env node
/**
 * Convert an SVG to PNG via headless Chromium (full SVG spec support, including
 * <textPath> which librsvg can't render). Usage:
 *
 *   node scripts/svg-to-png.mjs <svg> <out.png> [width] [height]
 *
 * Width/height in PIXELS (the output size). Aspect ratio comes from the SVG.
 */
import { chromium } from 'playwright'
import { readFileSync, writeFileSync } from 'fs'
import { resolve } from 'path'

const svgPath = process.argv[2]
const outPath = process.argv[3]
const width = parseInt(process.argv[4] || '0', 10)
const height = parseInt(process.argv[5] || '0', 10)

if (!svgPath || !outPath) {
  console.error('Usage: node svg-to-png.mjs <svg> <out.png> [width] [height]')
  process.exit(1)
}

const svg = readFileSync(svgPath, 'utf-8')
// Extract intrinsic width/height/viewBox so we can size the page correctly
const widthMatch = svg.match(/<svg[^>]*\swidth="([^"]+)"/)
const heightMatch = svg.match(/<svg[^>]*\sheight="([^"]+)"/)
const viewBoxMatch = svg.match(/viewBox="([^"]+)"/)

let intrinsicW = 0, intrinsicH = 0
if (viewBoxMatch) {
  const [, , vbW, vbH] = viewBoxMatch[1].split(/\s+/).map(Number)
  intrinsicW = vbW
  intrinsicH = vbH
}

const outW = width || intrinsicW
const outH = height || intrinsicH
if (!outW || !outH) {
  console.error('Could not determine output size — pass width and height.')
  process.exit(2)
}

const browser = await chromium.launch()
const page = await browser.newPage({
  viewport: { width: outW, height: outH },
  deviceScaleFactor: 1,
})

// Mount the SVG full-bleed in an HTML page
const html = `<!doctype html>
<html><head><style>
  html,body{margin:0;padding:0;background:transparent}
  svg{display:block;width:${outW}px;height:${outH}px}
</style></head><body>${svg}</body></html>`

await page.setContent(html, { waitUntil: 'load' })
// Give the browser a beat to layout textPath glyphs
await page.waitForTimeout(500)

// Output type from extension — accept .jpg/.jpeg for print shops that want
// smaller files (JPEG quality 92 is print-grade and 3-5x smaller than PNG).
const isJpeg = /\.(jpg|jpeg)$/i.test(outPath)
const opts = { path: resolve(outPath), omitBackground: false }
if (isJpeg) {
  opts.type = 'jpeg'
  opts.quality = 92
} else {
  opts.type = 'png'
}
await page.screenshot(opts)
await browser.close()
console.log(`Saved: ${outPath} (${outW}x${outH})`)
