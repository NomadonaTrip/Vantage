"use client";

interface SourceMetrics {
  source: string;
  total_leads: number;
  leads_converted: number;
  avg_intent_score: number;
  response_rate: number;
  conversion_rate: number;
  accuracy_rate: number;
}

interface SourceBreakdownProps {
  sourceMetrics: SourceMetrics[];
}

const SOURCE_LABELS: Record<string, string> = {
  upwork: "Upwork",
  reddit: "Reddit",
  apollo: "Apollo",
  clutch: "Clutch",
  bing: "Bing",
  google: "Google",
  manual: "Manual",
};

const SOURCE_COLORS: Record<string, string> = {
  upwork: "bg-green-500",
  reddit: "bg-orange-500",
  apollo: "bg-blue-500",
  clutch: "bg-purple-500",
  bing: "bg-cyan-500",
  google: "bg-red-500",
  manual: "bg-gray-500",
};

export function SourceBreakdown({ sourceMetrics }: SourceBreakdownProps) {
  if (!sourceMetrics || sourceMetrics.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Source Performance
        </h3>
        <p className="text-gray-500 dark:text-gray-400 text-center py-8">
          No source data available for this period.
        </p>
      </div>
    );
  }

  // Sort by total leads descending
  const sortedMetrics = [...sourceMetrics].sort(
    (a, b) => b.total_leads - a.total_leads
  );

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Source Performance
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-2 text-sm font-medium text-gray-500 dark:text-gray-400">
                Source
              </th>
              <th className="text-right py-3 px-2 text-sm font-medium text-gray-500 dark:text-gray-400">
                Leads
              </th>
              <th className="text-right py-3 px-2 text-sm font-medium text-gray-500 dark:text-gray-400">
                Converted
              </th>
              <th className="text-right py-3 px-2 text-sm font-medium text-gray-500 dark:text-gray-400">
                Avg Score
              </th>
              <th className="text-right py-3 px-2 text-sm font-medium text-gray-500 dark:text-gray-400">
                Response
              </th>
              <th className="text-right py-3 px-2 text-sm font-medium text-gray-500 dark:text-gray-400">
                Conversion
              </th>
              <th className="text-right py-3 px-2 text-sm font-medium text-gray-500 dark:text-gray-400">
                Accuracy
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedMetrics.map((metric) => (
              <tr
                key={metric.source}
                className="border-b border-gray-100 dark:border-gray-700 last:border-0"
              >
                <td className="py-3 px-2">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        SOURCE_COLORS[metric.source] || "bg-gray-400"
                      }`}
                    />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {SOURCE_LABELS[metric.source] || metric.source}
                    </span>
                  </div>
                </td>
                <td className="text-right py-3 px-2 text-sm text-gray-700 dark:text-gray-300">
                  {metric.total_leads.toLocaleString()}
                </td>
                <td className="text-right py-3 px-2 text-sm text-gray-700 dark:text-gray-300">
                  {metric.leads_converted.toLocaleString()}
                </td>
                <td className="text-right py-3 px-2 text-sm text-gray-700 dark:text-gray-300">
                  {metric.avg_intent_score.toFixed(1)}
                </td>
                <td className="text-right py-3 px-2">
                  <span
                    className={`text-sm font-medium ${
                      metric.response_rate >= 50
                        ? "text-green-600 dark:text-green-400"
                        : metric.response_rate >= 25
                        ? "text-yellow-600 dark:text-yellow-400"
                        : "text-red-600 dark:text-red-400"
                    }`}
                  >
                    {metric.response_rate.toFixed(1)}%
                  </span>
                </td>
                <td className="text-right py-3 px-2">
                  <span
                    className={`text-sm font-medium ${
                      metric.conversion_rate >= 20
                        ? "text-green-600 dark:text-green-400"
                        : metric.conversion_rate >= 10
                        ? "text-yellow-600 dark:text-yellow-400"
                        : "text-red-600 dark:text-red-400"
                    }`}
                  >
                    {metric.conversion_rate.toFixed(1)}%
                  </span>
                </td>
                <td className="text-right py-3 px-2">
                  <span
                    className={`text-sm font-medium ${
                      metric.accuracy_rate >= 85
                        ? "text-green-600 dark:text-green-400"
                        : metric.accuracy_rate >= 70
                        ? "text-yellow-600 dark:text-yellow-400"
                        : "text-red-600 dark:text-red-400"
                    }`}
                  >
                    {metric.accuracy_rate.toFixed(1)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
