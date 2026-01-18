"use client";

interface ScoreCorrelation {
  score_range_start: number;
  score_range_end: number;
  total_leads: number;
  converted_count: number;
  lost_count: number;
  conversion_rate: number;
  response_rate: number;
}

interface ScoreCorrelationProps {
  correlations: ScoreCorrelation[];
}

export function ScoreCorrelationChart({ correlations }: ScoreCorrelationProps) {
  if (!correlations || correlations.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Intent Score vs Outcomes
        </h3>
        <p className="text-gray-500 dark:text-gray-400 text-center py-8">
          No correlation data available for this period.
        </p>
      </div>
    );
  }

  const maxLeads = Math.max(...correlations.map((c) => c.total_leads), 1);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Intent Score vs Outcomes
      </h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
        Conversion rate by intent score range
      </p>
      <div className="space-y-4">
        {correlations.map((correlation) => {
          const barWidth = (correlation.total_leads / maxLeads) * 100;
          const conversionWidth = correlation.conversion_rate;

          return (
            <div key={`${correlation.score_range_start}-${correlation.score_range_end}`}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {correlation.score_range_start}-{correlation.score_range_end}
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {correlation.total_leads} leads
                </span>
              </div>
              <div className="flex items-center gap-4">
                {/* Lead volume bar */}
                <div className="flex-1 h-8 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden relative">
                  <div
                    className="h-full bg-blue-200 dark:bg-blue-900 transition-all duration-300"
                    style={{ width: `${barWidth}%` }}
                  />
                  {/* Conversion overlay */}
                  <div
                    className="absolute inset-y-0 left-0 bg-green-500 opacity-70 transition-all duration-300"
                    style={{ width: `${(conversionWidth / 100) * barWidth}%` }}
                  />
                  {/* Label */}
                  <div className="absolute inset-0 flex items-center px-3">
                    <span className="text-xs font-medium text-gray-700 dark:text-gray-200">
                      {correlation.converted_count} converted
                    </span>
                  </div>
                </div>
                {/* Conversion rate */}
                <div className="w-20 text-right">
                  <span
                    className={`text-sm font-bold ${
                      correlation.conversion_rate >= 20
                        ? "text-green-600 dark:text-green-400"
                        : correlation.conversion_rate >= 10
                        ? "text-yellow-600 dark:text-yellow-400"
                        : "text-gray-600 dark:text-gray-400"
                    }`}
                  >
                    {correlation.conversion_rate.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <div className="flex items-center gap-4 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-blue-200 dark:bg-blue-900 rounded" />
          <span className="text-xs text-gray-500 dark:text-gray-400">Lead volume</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-green-500 rounded" />
          <span className="text-xs text-gray-500 dark:text-gray-400">Converted</span>
        </div>
      </div>
    </div>
  );
}
