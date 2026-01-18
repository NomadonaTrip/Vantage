'use client';

/**
 * Lead Card Component
 *
 * Displays individual lead with intent score and breakdown.
 */

import { useState } from 'react';
import { Lead, IntentScoreBreakdown } from '@/stores/search-store';

interface LeadCardProps {
  lead: Lead;
}

const getScoreColor = (score: number): string => {
  if (score >= 0.8) return 'text-green-600 bg-green-100';
  if (score >= 0.6) return 'text-blue-600 bg-blue-100';
  if (score >= 0.4) return 'text-yellow-600 bg-yellow-100';
  return 'text-gray-600 bg-gray-100';
};

const formatBreakdownKey = (key: string): string => {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
};

function ScoreBreakdownTooltip({ breakdown }: { breakdown: IntentScoreBreakdown }) {
  const entries = Object.entries(breakdown).filter(
    ([, value]) => typeof value === 'number'
  );

  return (
    <div className="absolute z-10 w-64 p-3 bg-white border border-gray-200 rounded-lg shadow-lg -top-2 left-full ml-2">
      <h4 className="text-xs font-semibold text-gray-700 mb-2">Score Breakdown</h4>
      <div className="space-y-1">
        {entries.map(([key, value]) => (
          <div key={key} className="flex justify-between text-xs">
            <span className="text-gray-600">{formatBreakdownKey(key)}</span>
            <span className="font-medium text-gray-900">
              {Math.round((value as number) * 100)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function LeadCard({ lead }: LeadCardProps) {
  const [showBreakdown, setShowBreakdown] = useState(false);
  const scorePercentage = Math.round(lead.intent_score * 100);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        {/* Lead Info */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-gray-900 truncate">
            {lead.name}
          </h3>
          <p className="text-sm text-gray-600 truncate">{lead.company}</p>

          {/* Contact Info */}
          <div className="mt-2 space-y-1">
            {lead.email && (
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <svg
                  className="h-3 w-3"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
                <a
                  href={`mailto:${lead.email}`}
                  className="hover:text-blue-600 truncate"
                >
                  {lead.email}
                </a>
              </div>
            )}
            {lead.phone && (
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <svg
                  className="h-3 w-3"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                  />
                </svg>
                <a href={`tel:${lead.phone}`} className="hover:text-blue-600">
                  {lead.phone}
                </a>
              </div>
            )}
          </div>

          {/* Source */}
          <div className="mt-2 flex items-center gap-1 text-xs text-gray-400">
            <span>Source:</span>
            {lead.source_url ? (
              <a
                href={lead.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:text-blue-700 hover:underline"
              >
                {lead.source}
              </a>
            ) : (
              <span>{lead.source}</span>
            )}
          </div>
        </div>

        {/* Intent Score */}
        <div className="relative ml-4">
          <div
            className={`relative px-3 py-1.5 rounded-full text-sm font-bold cursor-help ${getScoreColor(
              lead.intent_score
            )}`}
            onMouseEnter={() => setShowBreakdown(true)}
            onMouseLeave={() => setShowBreakdown(false)}
          >
            {scorePercentage}%
            {lead.score_breakdown && showBreakdown && (
              <ScoreBreakdownTooltip breakdown={lead.score_breakdown} />
            )}
          </div>
          <p className="text-xs text-gray-400 text-center mt-1">Intent</p>
        </div>
      </div>
    </div>
  );
}
