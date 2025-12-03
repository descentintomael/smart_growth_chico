import type { PopupConfig } from '@/types'

/**
 * Generate HTML content for a feature popup
 */
export function generatePopupContent(
  config: PopupConfig,
  properties: Record<string, unknown>
): string {
  // Replace {property} placeholders in title
  const title = config.title.replace(/\{(\w+)\}/g, (_, key) => {
    const value = properties[key]
    return value != null ? String(value) : ''
  })

  // Generate field rows
  const rows = config.fields
    .map(field => {
      const rawValue = properties[field.property]
      const formatted = field.format ? field.format(rawValue) : String(rawValue ?? 'N/A')

      return `
        <tr>
          <td class="pr-3 text-gray-500">${field.label}</td>
          <td class="font-medium text-gray-900">${formatted}</td>
        </tr>
      `
    })
    .join('')

  return `
    <div class="popup-content">
      <h3 class="font-semibold text-gray-900 text-base mb-2">${title}</h3>
      <table class="text-sm w-full">
        <tbody>
          ${rows}
        </tbody>
      </table>
    </div>
  `
}
