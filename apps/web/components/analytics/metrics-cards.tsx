"use client";

interface OutcomeMetrics {
  total_leads: number;
  response_rate: number;
  conversion_rate: number;
  accuracy_rate: number;
}

interface SearchMetrics {
  total_searches: number;
  success_rate: number;
  avg_leads_per_search: number;
}

interface MetricsCardsProps {
  outcomeMetrics: OutcomeMetrics;
  searchMetrics: SearchMetrics;
}

export function MetricsCards({ outcomeMetrics, searchMetrics }: MetricsCardsProps) {
  const cards = [
    {
      title: "Total Leads",
      value: outcomeMetrics.total_leads.toLocaleString(),
      description: "Leads generated",
      color: "bg-blue-500",
    },
    {
      title: "Response Rate",
      value: `${outcomeMetrics.response_rate.toFixed(1)}%`,
      description: "Responded / Contacted",
      color: "bg-green-500",
    },
    {
      title: "Conversion Rate",
      value: `${outcomeMetrics.conversion_rate.toFixed(1)}%`,
      description: "Converted / Total",
      color: "bg-purple-500",
    },
    {
      title: "Accuracy Rate",
      value: `${outcomeMetrics.accuracy_rate.toFixed(1)}%`,
      description: "Verified / Classified",
      color: "bg-orange-500",
    },
    {
      title: "Total Searches",
      value: searchMetrics.total_searches.toLocaleString(),
      description: "Search operations",
      color: "bg-indigo-500",
    },
    {
      title: "Search Success",
      value: `${searchMetrics.success_rate.toFixed(1)}%`,
      description: "Completed searches",
      color: "bg-teal-500",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card) => (
        <div
          key={card.title}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4"
        >
          <div className="flex items-center gap-2 mb-2">
            <div className={`w-2 h-2 rounded-full ${card.color}`} />
            <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
              {card.title}
            </span>
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {card.value}
          </div>
          <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
            {card.description}
          </div>
        </div>
      ))}
    </div>
  );
}
