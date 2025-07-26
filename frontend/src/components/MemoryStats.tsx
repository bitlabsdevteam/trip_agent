'use client';

import React from 'react';

interface MemoryStatsProps {
  stats: {
    total_messages: number;
    summarizations_count: number;
    buffer_size: number;
    summarization_threshold: number;
    current_buffer_count: number;
    has_summary: boolean;
    last_summarization?: string;
  };
  bufferMessages: Array<{role: string; content: string}>;
  summary: string;
}

export const MemoryStats: React.FC<MemoryStatsProps> = ({ stats, bufferMessages, summary }) => {
  const bufferUsagePercentage = (stats.current_buffer_count / stats.buffer_size) * 100;
  const isNearThreshold = stats.current_buffer_count >= stats.summarization_threshold;

  return (
    <div className="space-y-4">
      {/* Memory Overview */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <div className="pb-3">
          <h3 className="flex items-center gap-2 text-lg font-semibold">
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            Memory Overview
          </h3>
        </div>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Messages</p>
              <p className="text-2xl font-bold">{stats.total_messages}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-gray-600 dark:text-gray-400">Summarizations</p>
              <p className="text-2xl font-bold">{stats.summarizations_count}</p>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Buffer Usage</span>
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                isNearThreshold 
                  ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' 
                  : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
              }`}>
                {stats.current_buffer_count}/{stats.buffer_size}
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                style={{ width: `${bufferUsagePercentage}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Threshold: {stats.summarization_threshold} messages
            </p>
          </div>

          {stats.has_summary && (
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8l6 6L5 20l-1-1m0 0l1-1m-1 1l6-6L5 8l6-6 1 1m0 0l1 1m-1-1L5 8l6-6" />
              </svg>
              <span className="text-sm text-green-600">Has conversation summary</span>
            </div>
          )}

          {stats.last_summarization && (
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-xs text-gray-600 dark:text-gray-400">
                Last summarized: {new Date(stats.last_summarization).toLocaleString()}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Buffer Messages */}
      {bufferMessages.length > 0 && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="pb-3">
            <h3 className="flex items-center gap-2 text-lg font-semibold">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              Recent Buffer ({bufferMessages.length})
            </h3>
          </div>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {bufferMessages.map((msg, index) => (
              <div key={index} className="p-2 rounded border border-gray-200 dark:border-gray-600">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    msg.role === 'human' 
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' 
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                  }`}>
                    {msg.role === 'human' ? 'User' : 'Assistant'}
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                  {msg.content.substring(0, 100)}{msg.content.length > 100 ? '...' : ''}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Conversation Summary */}
      {summary && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="pb-3">
            <h3 className="flex items-center gap-2 text-lg font-semibold">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8l6 6L5 20l-1-1m0 0l1-1m-1 1l6-6L5 8l6-6 1 1m0 0l1 1m-1-1L5 8l6-6" />
              </svg>
              Conversation Summary
            </h3>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
            {summary}
          </p>
        </div>
      )}
    </div>
  );
};

export default MemoryStats;