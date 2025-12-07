import { FIRE_TIER_COLORS, FIRE_TIER_LABELS } from '@/components/layers/FireRiskLayer'
import type { FireRiskTier } from '@/types'

// Tiers in order from low to high risk
const TIERS_IN_ORDER: FireRiskTier[] = ['Low', 'Moderate', 'High', 'Extreme']

/**
 * Legend for fire risk layer (categorical tiers)
 */
export function FireRiskLegend() {
  return (
    <div className="space-y-2">
      <span className="text-sm font-medium text-gray-700">Fire Risk Tier</span>

      {/* Categorical legend items */}
      <div className="space-y-1.5">
        {TIERS_IN_ORDER.map((tier) => (
          <div key={tier} className="flex items-center gap-2">
            <div
              className="h-4 w-6 rounded border border-gray-300"
              style={{ backgroundColor: FIRE_TIER_COLORS[tier] }}
              aria-hidden="true"
            />
            <span className="text-xs text-gray-600">{FIRE_TIER_LABELS[tier]}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
