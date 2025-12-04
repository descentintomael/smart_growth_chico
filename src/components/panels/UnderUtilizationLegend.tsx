import { UU_COLOR_SCALE, METRIC_LABELS } from '@/components/layers/UnderUtilizationLayer'
import { useUnderUtilizationStore } from '@/stores/underUtilizationStore'

/**
 * Legend for under-utilization layer (inline in control panel)
 */
export function UnderUtilizationLegend() {
  const selectedMetric = useUnderUtilizationStore((state) => state.selectedMetric)

  // Generate gradient string for the color bar
  const gradientStops = UU_COLOR_SCALE.map(
    (color, i) => `${color} ${(i / (UU_COLOR_SCALE.length - 1)) * 100}%`
  ).join(', ')

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">{METRIC_LABELS[selectedMetric]}</span>
      </div>

      {/* Color bar */}
      <div
        className="h-3 w-full rounded border border-gray-200"
        style={{ background: `linear-gradient(to right, ${gradientStops})` }}
        aria-hidden="true"
      />

      {/* Scale labels */}
      <div className="flex justify-between text-xs text-gray-500">
        <span>0 (Low)</span>
        <span>40</span>
        <span>60</span>
        <span>80</span>
        <span>100 (Severe)</span>
      </div>
    </div>
  )
}
