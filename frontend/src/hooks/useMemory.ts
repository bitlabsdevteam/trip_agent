'use client';

import { useState, useEffect, useCallback } from 'react';

export interface ConversationMemory {
  summary: string;
  lastUpdated: number;
  messageCount: number;
  bufferMessages: Array<{role: string; content: string}>;
  stats: {
    total_messages: number;
    summarizations_count: number;
    buffer_size: number;
    summarization_threshold: number;
    current_buffer_count: number;
    has_summary: boolean;
    last_summarization?: string;
  };
  bufferSize: number;
  currentBufferCount: number;
  summarizationsCount: number;
  hasSummary: boolean;
}

export interface UseMemoryOptions {
  storageKey?: string;
  maxSummaryAge?: number; // in milliseconds
}

export function useMemory(options: UseMemoryOptions = {}) {
  const {
    storageKey = 'conversationMemory',
    maxSummaryAge = 24 * 60 * 60 * 1000 // 24 hours default
  } = options;

  const [memory, setMemory] = useState<ConversationMemory | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Load memory from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        const savedMemory = localStorage.getItem(storageKey);
        if (savedMemory) {
          const parsedMemory: ConversationMemory = JSON.parse(savedMemory);
          
          // Check if memory is still valid (not too old)
          const isValid = Date.now() - parsedMemory.lastUpdated < maxSummaryAge;
          
          if (isValid) {
            setMemory(parsedMemory);
          } else {
            // Clear expired memory
            localStorage.removeItem(storageKey);
          }
        }
      } catch (error) {
        console.error('Failed to load conversation memory:', error);
        localStorage.removeItem(storageKey);
      }
    }
  }, [storageKey, maxSummaryAge]);

  // Save memory to localStorage whenever it changes
  useEffect(() => {
    if (typeof window !== 'undefined' && memory) {
      try {
        localStorage.setItem(storageKey, JSON.stringify(memory));
      } catch (error) {
        console.error('Failed to save conversation memory:', error);
      }
    }
  }, [memory, storageKey]);

  // Update memory with new summary
  const updateMemory = useCallback(async (summary: string, messageCount: number, additionalData?: Partial<ConversationMemory>) => {
    const newMemory: ConversationMemory = {
      summary,
      lastUpdated: Date.now(),
      messageCount,
      bufferMessages: additionalData?.bufferMessages || [],
      stats: additionalData?.stats || {
        total_messages: messageCount,
        summarizations_count: 0,
        buffer_size: 0,
        summarization_threshold: 0,
        current_buffer_count: 0,
        has_summary: !!summary
      },
      bufferSize: additionalData?.bufferSize || 0,
      currentBufferCount: additionalData?.currentBufferCount || 0,
      summarizationsCount: additionalData?.summarizationsCount || 0,
      hasSummary: additionalData?.hasSummary || !!summary
    };
    
    setMemory(newMemory);
  }, []);

interface MemoryData {
  summary: string;
  message_count: number;
  has_history: boolean;
  buffer_messages: Array<{role: string; content: string}>;
  stats: {
    total_messages: number;
    summarizations_count: number;
    buffer_size: number;
    summarization_threshold: number;
    current_buffer_count: number;
    has_summary: boolean;
    last_summarization?: string;
  };
  buffer_size: number;
  current_buffer_count: number;
  summarizations_count: number;
  has_summary: boolean;
}

  // Fetch memory summary from backend
  const fetchMemoryFromBackend = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/memory', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();
      
      // Handle the direct response from backend API
      if (data && typeof data === 'object') {
        const memoryData = data as MemoryData;
        const newMemory: ConversationMemory = {
          summary: memoryData.summary || '',
          lastUpdated: Date.now(),
          messageCount: memoryData.message_count || 0,
          bufferMessages: memoryData.buffer_messages || [],
          stats: memoryData.stats || {
            total_messages: 0,
            summarizations_count: 0,
            buffer_size: 0,
            summarization_threshold: 0,
            current_buffer_count: 0,
            has_summary: false
          },
          bufferSize: memoryData.buffer_size || 0,
          currentBufferCount: memoryData.current_buffer_count || 0,
          summarizationsCount: memoryData.summarizations_count || 0,
          hasSummary: memoryData.has_summary || false
        };
        setMemory(newMemory);
      } else {
        // Log the error but don't throw - backend might be unavailable
        console.warn('Failed to fetch memory from backend: Invalid response format');
      }
    } catch (error) {
      // Network or parsing errors - log but don't throw
      console.warn('Failed to fetch memory from backend:', error instanceof Error ? error.message : 'Network error');
    } finally {
      setIsLoading(false);
    }
  }, [updateMemory]);

  // Clear memory
  const clearMemory = useCallback(async () => {
    // Clear local memory first
    setMemory(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem(storageKey);
    }
    
    // Attempt to clear backend memory, but don't fail if backend is unavailable
    try {
      const response = await fetch('/api/memory', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action: 'clear' })
      });
      
      const data = await response.json();
      if (!data.success) {
        console.warn('Backend memory clear failed:', data.error || 'Unknown error');
      }
    } catch (error) {
      // Log but don't throw - backend might be unavailable
      console.warn('Failed to clear memory on backend:', error instanceof Error ? error.message : 'Network error');
    }
  }, [storageKey]);

  // Get memory summary for sending to backend
  const getMemoryForRequest = useCallback(() => {
    if (!memory) return null;
    
    return {
      summary: memory.summary,
      messageCount: memory.messageCount,
      bufferMessages: memory.bufferMessages,
      stats: memory.stats
    };
  }, [memory]);

  // Check if memory should be updated (e.g., after every few messages)
  const shouldUpdateMemory = useCallback((currentMessageCount: number) => {
    if (!memory) return currentMessageCount >= 4; // Start summarizing after 4 messages
    
    // Update if we have 3+ new messages since last summary
    return currentMessageCount - memory.messageCount >= 3;
  }, [memory]);

  return {
    memory,
    isLoading,
    updateMemory,
    fetchMemoryFromBackend,
    clearMemory,
    getMemoryForRequest,
    shouldUpdateMemory
  };
}