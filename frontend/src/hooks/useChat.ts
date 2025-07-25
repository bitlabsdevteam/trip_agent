'use client';

import { useState, useCallback, useRef, useEffect } from 'react';

export type MessageRole = 'user' | 'assistant' | 'thinking' | 'system';

export interface Message {
  content: string;
  role: MessageRole;
  timestamp?: number; // Add timestamp for message ordering
  isThinking?: boolean; // Flag to identify thinking/reasoning messages
  id?: string; // Optional ID for message identification
}

export interface ConversationSummary {
  summary: string;
  recent_messages: {
    type: string;
    content: string;
  }[];
}

export interface UseChatOptions {
  onError?: (error: Error) => void;
  initialMessages?: Message[];
}

export function useChat(options: UseChatOptions = {}) {
  // Initialize with empty array or initialMessages, will load from localStorage after mount
  const [messages, setMessages] = useState<Message[]>(
    options.initialMessages || []
  );
  
  // Load messages from localStorage on client-side only
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedMessages = localStorage.getItem('chatMessages');
      if (savedMessages) {
        try {
          setMessages(JSON.parse(savedMessages));
        } catch (e) {
          console.error('Failed to parse saved messages:', e);
        }
      }
    }
  }, []);
  
  const [isLoading, setIsLoading] = useState(false);
  const [currentAssistantMessage, setCurrentAssistantMessage] = useState('');
  const [thinkingMessages, setThinkingMessages] = useState<Message[]>([]);
  const [conversationSummary, setConversationSummary] = useState<ConversationSummary | null>(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (typeof window !== 'undefined' && messages.length > 0) {
      localStorage.setItem('chatMessages', JSON.stringify(messages));
    }
  }, [messages]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    // Add user message to chat with timestamp
    const userMessage: Message = { 
      content, 
      role: 'user',
      timestamp: Date.now() 
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setCurrentAssistantMessage('');
    setThinkingMessages([]);

    // Create a new AbortController for this request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      // Connect to our Next.js API proxy endpoint
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({ message: content }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Response body is null');
      }

      // Process the stream
      const decoder = new TextDecoder();
      let buffer = '';
      let assistantResponse = '';
      
      console.log('Starting to process stream...');

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          
          // Process complete lines from the buffer
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep the last incomplete line in the buffer
          
          for (const line of lines) {
            if (line.startsWith('data:')) {
              try {
                // Extract the JSON part after 'data:'
                const jsonStr = line.slice(5).trim();
                if (!jsonStr) continue;
                
                const data = JSON.parse(jsonStr);
                console.log('Received data:', data); // Debug log
                
                // Handle different event types
                if (data.event === 'token') {
                  // Get the token content
                  const tokenContent = data.token || '';
                  
                  // Try to parse the token as JSON to extract thinking content
                  try {
                    if (tokenContent.trim().startsWith('{') && tokenContent.trim().endsWith('}')) {
                      const parsedToken = JSON.parse(tokenContent);
                      
                      // If it has a response field, use that
                      if (parsedToken.response !== undefined) {
                        // Remove the green tick and 'Final Answer:' prefix if present
                        let cleanResponse = parsedToken.response;
                        cleanResponse = cleanResponse.replace(/^\s*✅\s*Final\s*Answer:\s*/i, '');
                        
                        assistantResponse = cleanResponse;
                        setCurrentAssistantMessage(assistantResponse);
                      } else {
                        // Otherwise append the token to the response
                        assistantResponse += tokenContent;
                        setCurrentAssistantMessage(assistantResponse);
                      }
                      
                      // Capture thinking content if available
                      if (parsedToken.thinking) {
                        const thinkingMessage: Message = {
                          content: parsedToken.thinking,
                          role: 'thinking',
                          timestamp: Date.now(),
                          isThinking: true
                        };
                        setThinkingMessages(prev => [...prev, thinkingMessage]);
                      }
                    } else {
                      // Not JSON, treat as plain text
                      assistantResponse += tokenContent;
                      setCurrentAssistantMessage(assistantResponse);
                    }
                  } catch (parseError) {
                    // If parsing fails, treat it as a regular token
                    assistantResponse += tokenContent;
                    setCurrentAssistantMessage(assistantResponse);
                  }
                } else if (data.event === 'structured_output') {
                  try {
                    // Handle structured output data
                    let parsedData;
                    
                    if (typeof data.data === 'string') {
                      // If it's a string, parse it
                      parsedData = JSON.parse(data.data);
                    } else if (typeof data.data === 'object' && data.data !== null) {
                      // If it's already an object, use it directly
                      parsedData = data.data;
                    } else {
                      continue; // Skip if no valid data
                    }
                    
                    // Extract the response field
                    if (parsedData.response !== undefined) {
                      // Remove the green tick and 'Final Answer:' prefix if present
                      let cleanResponse = parsedData.response;
                      cleanResponse = cleanResponse.replace(/^\s*✅\s*Final\s*Answer:\s*/i, '');
                      
                      assistantResponse = cleanResponse;
                      setCurrentAssistantMessage(assistantResponse);
                    }
                    
                    // Capture thinking content if available
                    if (parsedData.thinking) {
                      console.log('AI thinking:', parsedData.thinking);
                      const thinkingMessage: Message = {
                        content: parsedData.thinking,
                        role: 'thinking',
                        timestamp: Date.now(),
                        isThinking: true
                      };
                      setThinkingMessages(prev => [...prev, thinkingMessage]);
                    }
                    
                    // Capture function_calls if available
                    if (parsedData.function_calls) {
                      console.log('Function calls:', parsedData.function_calls);
                      const functionCallMessage: Message = {
                        content: JSON.stringify(parsedData.function_calls, null, 2),
                        role: 'thinking',
                        timestamp: Date.now(),
                        isThinking: true
                      };
                      setThinkingMessages(prev => [...prev, functionCallMessage]);
                    }
                  } catch (parseError) {
                    console.error('Error parsing structured output:', parseError, data.data);
                  }
                } else if (data.event === 'message') {
                  // The backend sends tokens with event type 'message' and content in 'data' field
                  const tokenContent = data.data || '';
                  assistantResponse += tokenContent;
                  setCurrentAssistantMessage(assistantResponse);
                } else if (data.event === 'error') {
                  // Handle error events
                  console.error('Stream error:', data.data);
                  // Extract any useful information from the error message
                  const errorMsg = data.data || '';
                  const match = errorMsg.match(/Could not parse LLM output: `(.+)`/);
                  if (match && match[1]) {
                    // Extract the actual content from the error message
                    assistantResponse = match[1];
                    setCurrentAssistantMessage(assistantResponse);
                    
                    // Add the error message to the chat as a system message
                    const systemMessage: Message = {
                      content: 'There was an error processing the response, but I was able to extract the content.',
                      role: 'system',
                      timestamp: Date.now(),
                      id: crypto.randomUUID()
                    };
                    setMessages(prevMessages => [...prevMessages, systemMessage]);
                  } else {
                    // Add a generic error message if we couldn't extract content
                    const systemMessage: Message = {
                      content: 'There was an error processing the response: ' + errorMsg,
                      role: 'system',
                      timestamp: Date.now(),
                      id: crypto.randomUUID()
                    };
                    setMessages(prevMessages => [...prevMessages, systemMessage]);
                  }
                } else if (data.event === 'final') {
                  // Final message received
                  console.log('Final message received');
                  // Clear thinking messages when response is complete
                  setThinkingMessages([]);
                } else {
                  // Handle any other event type or format
                  console.log('Unknown event type:', data);
                  // Try to extract content from various possible fields
                  const content = data.token || data.data || data.content || '';
                  if (content) {
                    assistantResponse += content;
                    setCurrentAssistantMessage(assistantResponse);
                  }
                }
              } catch (e) {
                console.error('Error parsing JSON:', e, 'Line:', line);
              }
            }
          }
        }
      } catch (streamError) {
        console.error('Error processing stream:', streamError);
        // Don't throw here, just log the error and continue
      }

      // Add the complete assistant message to the chat with timestamp
      if (assistantResponse) {
        setMessages((prev) => [...prev, { 
          content: assistantResponse, 
          role: 'assistant',
          timestamp: Date.now() 
        }]);
      }
    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        console.error('Error fetching from API:', error);
        setMessages((prev) => [...prev, { 
          content: 'Sorry, there was an error processing your request.', 
          role: 'assistant' 
        }]);
        options.onError?.(error);
      }
    } finally {
      setIsLoading(false);
      setCurrentAssistantMessage('');
      abortControllerRef.current = null;
    }
  }, [isLoading, options]);

  const stopGenerating = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setCurrentAssistantMessage('');
    setThinkingMessages([]);
    setConversationSummary(null);
    // Also clear localStorage
    if (typeof window !== 'undefined') {
      localStorage.removeItem('chatMessages');
    }
  }, []);

  // Create a handleSubmit function to be used in the component
  const [userInput, setUserInput] = useState('');

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (userInput.trim() && !isLoading) {
      sendMessage(userInput);
      setUserInput('');
    }
  }, [userInput, isLoading, sendMessage]);

  // Function to fetch the conversation summary
  const fetchSummary = useCallback(async () => {
    setIsSummaryLoading(true);
    try {
      const response = await fetch('/api/memory', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setConversationSummary(data);
      return data;
    } catch (error) {
      console.error('Error fetching conversation summary:', error);
      options.onError?.(error instanceof Error ? error : new Error(String(error)));
      return null;
    } finally {
      setIsSummaryLoading(false);
    }
  }, [options]);

  // Function to manually update the conversation summary
  const updateSummary = useCallback(async () => {
    setIsSummaryLoading(true);
    try {
      const response = await fetch('/api/memory/update-summary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      // After updating, fetch the full summary to get both summary and recent messages
      await fetchSummary();
      return data.summary;
    } catch (error) {
      console.error('Error updating conversation summary:', error);
      options.onError?.(error instanceof Error ? error : new Error(String(error)));
      return null;
    } finally {
      setIsSummaryLoading(false);
    }
  }, [fetchSummary, options]);

  // Function to set the maximum token limit
  const setMaxTokenLimit = useCallback(async (maxTokenLimit: number) => {
    try {
      const response = await fetch('/api/memory/token-limit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ max_token_limit: maxTokenLimit }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.success;
    } catch (error) {
      console.error('Error setting max token limit:', error);
      options.onError?.(error instanceof Error ? error : new Error(String(error)));
      return false;
    }
  }, [options]);

  // Fetch summary after sending a message
  useEffect(() => {
    // Only fetch if there are messages and we're not currently loading a response
    if (messages.length > 0 && !isLoading) {
      fetchSummary();
    }
  }, [messages, isLoading, fetchSummary]);

  return {
    messages,
    isLoading,
    currentAssistantMessage,
    thinkingMessages,
    conversationSummary,
    isSummaryLoading,
    sendMessage,
    stopGenerating,
    clearMessages,
    fetchSummary,
    updateSummary,
    setMaxTokenLimit,
    userInput,
    setUserInput,
    handleSubmit,
  };
}