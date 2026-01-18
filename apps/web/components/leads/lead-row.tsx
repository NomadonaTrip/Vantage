'use client';

/**
 * Lead Row Component
 *
 * Single row in the leads table.
 */

import { useState } from 'react';
import { Lead, LeadStatus, LeadAccuracy } from '@/stores/leads-store';
import { StatusDropdown } from './status-dropdown';
import { AccuracyBadge } from './accuracy-badge';
import { StatusHistory } from './status-history';

interface LeadRowProps {
  lead: Lead;
  onStatusChange: (leadId: string, status: LeadStatus) => void;
  onAccuracyChange: (leadId: string, accuracy: LeadAccuracy) => void;
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
};

const getScoreColor = (score: number): string => {
  if (score >= 0.8) return 'text-green-600';
  if (score >= 0.6) return 'text-blue-600';
  if (score >= 0.4) return 'text-yellow-600';
  return 'text-gray-600';
};

export function LeadRow({ lead, onStatusChange, onAccuracyChange }: LeadRowProps) {
  const [showHistory, setShowHistory] = useState(false);

  return (
    <>
      <tr className="hover:bg-gray-50">
        {/* Name & Company */}
        <td className="px-4 py-3">
          <div className="text-sm font-medium text-gray-900 truncate max-w-xs">
            {lead.name}
          </div>
          <div className="text-xs text-gray-500 truncate max-w-xs">
            {lead.company}
          </div>
        </td>

        {/* Contact */}
        <td className="px-4 py-3">
          {lead.email && (
            <div className="text-xs text-gray-600 truncate max-w-xs">
              <a href={`mailto:${lead.email}`} className="hover:text-blue-600">
                {lead.email}
              </a>
            </div>
          )}
          {lead.phone && (
            <div className="text-xs text-gray-500">
              <a href={`tel:${lead.phone}`} className="hover:text-blue-600">
                {lead.phone}
              </a>
            </div>
          )}
        </td>

        {/* Intent Score */}
        <td className="px-4 py-3 text-center">
          <span className={`text-sm font-semibold ${getScoreColor(lead.intent_score)}`}>
            {Math.round(lead.intent_score * 100)}%
          </span>
        </td>

        {/* Source */}
        <td className="px-4 py-3">
          <div className="text-xs text-gray-600">
            {lead.source_url ? (
              <a
                href={lead.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-blue-600 hover:underline"
              >
                {lead.source}
              </a>
            ) : (
              lead.source
            )}
          </div>
        </td>

        {/* Status */}
        <td className="px-4 py-3">
          <div className="flex items-center gap-1">
            <StatusDropdown
              status={lead.status}
              onChange={(status) => onStatusChange(lead.id, status)}
            />
            {lead.status_history && lead.status_history.length > 0 && (
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="text-gray-400 hover:text-gray-600"
                title="View history"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </button>
            )}
          </div>
        </td>

        {/* Accuracy */}
        <td className="px-4 py-3 text-center">
          <AccuracyBadge
            accuracy={lead.accuracy}
            onChange={(accuracy) => onAccuracyChange(lead.id, accuracy)}
          />
        </td>

        {/* Created Date */}
        <td className="px-4 py-3 text-xs text-gray-500">
          {formatDate(lead.created_at)}
        </td>
      </tr>

      {/* Status History Row */}
      {showHistory && (
        <tr>
          <td colSpan={7} className="px-4 py-3 bg-gray-50">
            <StatusHistory history={lead.status_history || []} />
          </td>
        </tr>
      )}
    </>
  );
}
