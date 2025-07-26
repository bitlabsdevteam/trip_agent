'use client';

import { useState, useEffect, useCallback } from 'react';

export interface ConversationMemory {
  summary: string;
  lastUpdated: number;
  messageCount: number;
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
  const updateMemory = useCallback(async (summary: string, messageCount: number) => {
    const newMemory: ConversationMemory = {
      summary,
      lastUpdated: Date.now(),
      messageCount
    };
    
    setMemory(newMemory);
  }, []);

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
      
      // Handle both successful and failed responses gracefully
      if (data.success && data.summary) {
        await updateMemory(data.summary, data.messageCount || 0);
      } else if (!data.success) {
        // Log the error but don't throw - backend might be unavailable
        console.warn('Backend memory fetch failed:', data.error || 'Unknown error');
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
      messageCount: memory.messageCount
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