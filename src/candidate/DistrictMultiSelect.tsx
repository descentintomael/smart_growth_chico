import { useNavigate } from 'react-router-dom'

const ALL_DISTRICTS = ['2', '4', '6']

interface Props {
  selectedDistricts: string[]
}

function urlForDistricts(districts: string[]): string {
  if (districts.length === 0) return '/candidate/district-6'
  const sorted = [...districts].sort((a, b) => Number(a) - Number(b))
  if (sorted.length === 1) return `/candidate/district-${sorted[0]}`
  return `/candidate/forum/${sorted.join('-')}`
}

/**
 * Pill-shaped segmented multi-selector for District 2 / 4 / 6.
 * Selecting only one navigates to /candidate/district-N (the original URL).
 * Selecting multiple navigates to /candidate/forum/N-M (the forum URL).
 * Zero selections is prevented (the last-selected pill can't be turned off).
 */
export function DistrictMultiSelect({ selectedDistricts }: Props) {
  const navigate = useNavigate()
  const selectedSet = new Set(selectedDistricts)

  function toggle(d: string) {
    const isSelected = selectedSet.has(d)
    let next: string[]
    if (isSelected) {
      if (selectedSet.size === 1) return  // never allow zero
      next = selectedDistricts.filter(s => s !== d)
    } else {
      next = [...selectedDistricts, d]
    }
    navigate(urlForDistricts(next))
  }

  return (
    <div
      role="group"
      aria-label="District selector"
      className="inline-flex items-center gap-1 rounded-full border border-gray-200 bg-gray-100 p-1 shadow-sm"
    >
      {ALL_DISTRICTS.map(d => {
        const isSelected = selectedSet.has(d)
        return (
          <button
            key={d}
            type="button"
            onClick={() => toggle(d)}
            aria-pressed={isSelected}
            className={`rounded-full px-3 py-1.5 text-xs font-semibold transition-all duration-150 ${
              isSelected
                ? 'bg-white text-gray-900 shadow-sm ring-1 ring-gray-900/5'
                : 'text-gray-500 hover:text-gray-900'
            }`}
          >
            District {d}
          </button>
        )
      })}
    </div>
  )
}
