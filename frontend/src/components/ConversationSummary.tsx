'use client';

import React from 'react';
import { ConversationSummary as SummaryType } from '@/hooks/useChat';
import LoadingSpinner from './LoadingSpinner';

interface ConversationSummaryProps {
  summary: SummaryType | null;
  isLoading: boolean;
  onUpdateSummary: () => void;
  onSetMaxTokenLimit: (limit: number) => void;
}

const ConversationSummary: React.FC<ConversationSummaryProps> = ({
  summary,
  isLoading,
  onUpdateSummary,
  onSetMaxTokenLimit,
}) => {
  const [showTokenLimitInput, setShowTokenLimitInput] = React.useState(false);
  const [tokenLimit, setTokenLimit] = React.useState(2000);

  const handleTokenLimitSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSetMaxTokenLimit(tokenLimit);
    setShowTokenLimitInput(false);
  };

  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-4">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-md font-semibold">Conversation Memory</h3>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowTokenLimitInput(!showTokenLimitInput)}
            className="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600"
          >
            Set Token Limit
          </button>
          <button
            onClick={onUpdateSummary}
            disabled={isLoading}
            className="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Update Summary
          </button>
        </div>
      </div>

      {showTokenLimitInput && (
        <form onSubmit={handleTokenLimitSubmit} className="mb-3 flex items-center space-x-2">
          <input
            type="number"
            value={tokenLimit}
            onChange={(e) => setTokenLimit(Number(e.target.value))}
            min="100"
            max="10000"
            className="border rounded px-2 py-1 text-sm w-24 dark:bg-gray-700 dark:border-gray-600"
          />
          <button
            type="submit"
            className="text-xs px-2 py-1 bg-green-500 text-white rounded hover:bg-green-600"
          >
            Save
          </button>
        </form>
      )}

      {isLoading ? (
        <div className="flex justify-center my-4">
          <LoadingSpinner size="small" />
        </div>
      ) : summary ? (
        <div>
          <div className="mb-3">
            <h4 className="text-sm font-medium mb-1">Summary</h4>
            <div className="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-gray-200 dark:border-gray-700">
              {summary.summary || "No summary available yet."}
            </div>
          </div>
          
          {summary.recent_messages && summary.recent_messages.length > 0 && (
            <div>
              <h4 className="text-sm font-medium mb-1">Recent Messages (Not Yet Summarized)</h4>
              <div className="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-gray-200 dark:border-gray-700 max-h-40 overflow-y-auto">
                {summary.recent_messages.map((msg, index) => (
                  <div key={index} className="mb-2 last:mb-0">
                    <span className="font-medium">{msg.type === 'human' ? 'You: ' : 'Assistant: '}</span>
                    {msg.content}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-sm text-gray-500 dark:text-gray-400">
          No conversation summary available. Start chatting to generate a summary.
        </div>
      )}
    </div>
  );
};

export default ConversationSummary;