'use client';

import { useState } from 'react';
import { ConversationMemory } from '../hooks/useMemory';
import { MemoryStats } from './MemoryStats';

interface MemoryDisplayProps {
  memory: ConversationMemory | null;
  onClearMemory?: () => void;
}

export default function MemoryDisplay({ memory, onClearMemory }: MemoryDisplayProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Show memory stats if we have enhanced memory data
  if (memory && memory.stats) {
    return (
      <div className="mb-4">
        <MemoryStats 
          stats={memory.stats}
          bufferMessages={memory.bufferMessages || []}
          summary={memory.summary}
        />
      </div>
    );
  }

  if (!memory || !memory.summary) {
    return (
      <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 mb-4">
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          <span>No conversation memory yet</span>
        </div>
      </div>
    );
  }

  const formatTimeAgo = (timestamp: number) => {
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    
    if (hours > 0) {
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else if (minutes > 0) {
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else {
      return 'Just now';
    }
  };

  return (
    <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 mb-4">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-300">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          <span className="font-medium">Conversation Memory</span>
          <span className="text-xs text-blue-600 dark:text-blue-400">
            ({memory.messageCount} messages, {formatTimeAgo(memory.lastUpdated)})
          </span>
        </div>
        
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 transition-colors"
            title={isExpanded ? 'Collapse' : 'Expand'}
          >
            <svg className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {onClearMemory && (
            <button
              onClick={onClearMemory}
              className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 transition-colors ml-1"
              title="Clear memory"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
        </div>
      </div>
      
      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-blue-200 dark:border-blue-800">
          <div className="text-sm text-blue-800 dark:text-blue-200 whitespace-pre-wrap">
            {memory.summary}
          </div>
        </div>
      )}
      
      {!isExpanded && memory.summary && (
        <div className="mt-2 text-sm text-blue-700 dark:text-blue-300 line-clamp-2">
          {memory.summary.length > 100 
            ? `${memory.summary.substring(0, 100)}...` 
            : memory.summary
          }
        </div>
      )}
    </div>
  );
}