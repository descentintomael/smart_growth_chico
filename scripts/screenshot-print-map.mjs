#!/usr/bin/env node
/**
 * One-shot screenshot of the /print/district-6 page using Playwright.
 *
 * The page renders the print canvas at its real print dimensions (PRINT_WIDTH ×
 * PRINT_HEIGHT) but visually scales it down via CSS transform for browser viewing.
 * We undo that transform before capture so the screenshot reflects true poster
 * proportions.
 *
 * Headless Chromium doesn't reliably composite WebGL into page.screenshot output,
 * so we draw the header/footer text onto an in-page 2D canvas and stamp the
 * WebGL map canvas onto it, then export via toDataURL.
 *
 * Usage: node scripts/screenshot-print-map.mjs [port] [outfile]
 */
import { chromium } from 'playwright'
import { resolve } from 'path'
import { writeFileSync } from 'fs'

const port = process.argv[2] || '5175'
const outfile = resolve(process.argv[3] || 'tmp-print-map-preview.png')
const url = `http://localhost:${port}/#/print/district-6`

// Launch with extra GPU memory headroom for big WebGL canvases.
const browser = await chromium.launch({
  args: [
    '--disable-gpu-sandbox',
    '--enable-unsafe-webgpu',
    '--ignore-gpu-blocklist',
  ],
})
// Viewport sized to hold the un-scaled print canvas (5400×7200) + page chrome.
const page = await browser.newPage({
  viewport: { width: 5600, height: 7500 },
  deviceScaleFactor: 1,
})

const consoleMsgs = []
const failedRequests = []
page.on('console', (msg) => {
  if (msg.type() === 'error') consoleMsgs.push(`[error] ${msg.text()}`)
})
page.on('pageerror', (err) => consoleMsgs.push(`pageerror: ${err.message}`))
page.on('requestfailed', (req) => {
  failedRequests.push(`${req.method()} ${req.url()} :: ${req.failure()?.errorText}`)
})

await page.goto(url, { waitUntil: 'networkidle' })
await page.waitForSelector('#print-canvas canvas', { timeout: 20000 })

// Remove the screen-only scale transform so the canvas sits at its real size.
// (The MapLibre container CSS dimensions don't change — the transform was purely
// visual — so the map doesn't need to resize.)
await page.evaluate(() => {
  const wrapper = document.getElementById('print-scale-wrapper')
  if (wrapper) {
    wrapper.style.transform = 'none'
    wrapper.style.width = ''
    wrapper.style.height = ''
  }
})

// Give MapLibre time to settle. At z16 over a 12km district that's hundreds of
// tiles to fetch from OpenFreeMap — plus sprites, glyphs, label collision passes.
// Wait for the map's idle event (no pending tiles, no in-flight renders).
await page.evaluate(async () => {
  const map = window.__printMap
  if (!map) return
  await new Promise((resolve) => {
    let timeout = setTimeout(resolve, 30000) // hard cap
    const checkIdle = () => {
      if (map.areTilesLoaded() && !map.isMoving()) {
        clearTimeout(timeout)
        resolve(undefined)
        return
      }
      map.once('idle', () => {
        clearTimeout(timeout)
        resolve(undefined)
      })
    }
    checkIdle()
  })
  // One more rAF to flush the final paint.
  await new Promise((r) => requestAnimationFrame(() => r(undefined)))
})

// Quick probe — confirm the map ended up at the expected zoom.
const probe = await page.evaluate(() => {
  const map = window.__printMap
  if (!map) return { ok: false }
  return { ok: true, zoom: map.getZoom() }
})
console.log('Probe:', JSON.stringify(probe))

// Composite inside the page so the WebGL canvas pixels survive.
const result = await page.evaluate(async () => {
  const root = document.getElementById('print-canvas')
  if (!root) return { error: 'no print-canvas' }
  const mapCanvas = root.querySelector('canvas')
  if (!(mapCanvas instanceof HTMLCanvasElement)) return { error: 'no map canvas' }
  const header = root.querySelector('header')
  const footer = root.querySelector('footer')
  if (!header || !footer) return { error: 'no header/footer' }

  const rootRect = root.getBoundingClientRect()
  const mapRect = mapCanvas.getBoundingClientRect()
  const headerRect = header.getBoundingClientRect()
  const footerRect = footer.getBoundingClientRect()

  const out = document.createElement('canvas')
  out.width = Math.round(rootRect.width)
  out.height = Math.round(rootRect.height)
  const ctx = out.getContext('2d')
  if (!ctx) return { error: 'no 2d ctx' }

  // White paper
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, out.width, out.height)

  // Stamp the WebGL map at its position
  ctx.drawImage(
    mapCanvas,
    Math.round(mapRect.x - rootRect.x),
    Math.round(mapRect.y - rootRect.y),
    Math.round(mapRect.width),
    Math.round(mapRect.height),
  )

  // Helpers — read computed style so font sizes match the DOM
  const readPx = (val) => parseFloat(val) || 0

  // ---- Header ----
  const headerY = headerRect.y - rootRect.y
  const h1 = header.querySelector('h1')
  const sub = header.querySelector('p')
  if (h1 && sub) {
    const h1Style = window.getComputedStyle(h1)
    const subStyle = window.getComputedStyle(sub)
    const headerStyle = window.getComputedStyle(header)
    const padLeft = readPx(headerStyle.paddingLeft)
    const padBottom = readPx(headerStyle.paddingBottom)

    const titleSize = readPx(h1Style.fontSize)
    const subSize = readPx(subStyle.fontSize)
    const subMarginTop = readPx(subStyle.marginTop) || Math.round(titleSize * 0.1)

    // Position from the BOTTOM of the header band upward (flex-end behavior).
    // textBaseline='top' so y values are line-box tops.
    const subTop = headerY + headerRect.height - padBottom - subSize
    const titleTop = subTop - subMarginTop - titleSize

    ctx.textAlign = 'left'
    ctx.textBaseline = 'top'

    ctx.fillStyle = '#0f172a'
    ctx.font = `600 ${titleSize}px -apple-system, "Segoe UI", system-ui, sans-serif`
    ctx.fillText(h1.textContent || '', padLeft, titleTop)

    ctx.fillStyle = '#525252'
    ctx.font = `400 ${subSize}px -apple-system, "Segoe UI", system-ui, sans-serif`
    ctx.fillText(sub.textContent || '', padLeft, subTop)

    // Bottom rule
    ctx.fillStyle = '#d4d4d4'
    ctx.fillRect(0, headerY + headerRect.height - 1, out.width, 1)
  }

  // ---- Footer ----
  const footerY = footerRect.y - rootRect.y
  const footerStyle = window.getComputedStyle(footer)
  const footerSize = readPx(footerStyle.fontSize)
  const padLeftF = readPx(footerStyle.paddingLeft)
  const padRightF = readPx(footerStyle.paddingRight)

  ctx.fillStyle = '#d4d4d4'
  ctx.fillRect(0, footerY, out.width, 1)

  ctx.fillStyle = '#6b7280'
  ctx.font = `400 ${footerSize}px -apple-system, "Segoe UI", system-ui, sans-serif`
  ctx.textBaseline = 'middle'
  const mid = footerY + footerRect.height / 2
  const spans = footer.querySelectorAll('span')
  ctx.textAlign = 'left'
  ctx.fillText(spans[0]?.textContent || '', padLeftF, mid)
  ctx.textAlign = 'right'
  ctx.fillText(spans[1]?.textContent || '', out.width - padRightF, mid)

  return { dataUrl: out.toDataURL('image/png') }
})

if (result.error || !result.dataUrl) {
  console.error('compose failed:', result.error)
  process.exit(2)
}

const b64 = result.dataUrl.replace(/^data:image\/png;base64,/, '')
writeFileSync(outfile, Buffer.from(b64, 'base64'))

await browser.close()

if (consoleMsgs.length) {
  console.log('Console errors:')
  for (const e of consoleMsgs) console.log('  -', e)
}
if (failedRequests.length) {
  console.log('Failed requests:')
  for (const r of failedRequests) console.log('  -', r)
}
console.log(`Saved: ${outfile}`)
