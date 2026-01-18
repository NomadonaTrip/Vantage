'use client';

/**
 * Quality Slider Component
 *
 * Controls speed vs quality trade-off for searches (0-1).
 */

interface QualitySliderProps {
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}

export function QualitySlider({ value, onChange, disabled = false }: QualitySliderProps) {
  const percentage = Math.round(value * 100);

  const getQualityLabel = (val: number): string => {
    if (val < 0.3) return 'Fast';
    if (val < 0.7) return 'Balanced';
    return 'Thorough';
  };

  const getQualityDescription = (val: number): string => {
    if (val < 0.3) return 'Quick results, fewer sources';
    if (val < 0.7) return 'Good balance of speed and coverage';
    return 'Maximum coverage, slower results';
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700">
          Search Quality
        </label>
        <span className="text-sm text-gray-500">
          {getQualityLabel(value)} ({percentage}%)
        </span>
      </div>

      <input
        type="range"
        min="0"
        max="100"
        value={percentage}
        onChange={(e) => onChange(parseInt(e.target.value) / 100)}
        disabled={disabled}
        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        style={{
          background: disabled
            ? '#e5e7eb'
            : `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${percentage}%, #e5e7eb ${percentage}%, #e5e7eb 100%)`,
        }}
      />

      <div className="flex justify-between text-xs text-gray-400">
        <span>Fast</span>
        <span>Balanced</span>
        <span>Thorough</span>
      </div>

      <p className="text-xs text-gray-500">{getQualityDescription(value)}</p>
    </div>
  );
}
