'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useMemory } from './useMemory';

export type MessageRole = 'user' | 'assistant' | 'thinking' | 'system';

export interface Message {
  content: string;
  role: MessageRole;
  timestamp?: number; // Add timestamp for message ordering
  isThinking?: boolean; // Flag to identify thinking/reasoning messages
  id?: string; // Optional ID for message identification
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
  
  // Initialize memory hook
  const {
    memory,
    updateMemory,
    fetchMemoryFromBackend,
    clearMemory,
    shouldUpdateMemory
  } = useMemory();
  
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
  
  // Fetch memory from backend on mount
  useEffect(() => {
    fetchMemoryFromBackend();
  }, [fetchMemoryFromBackend]);
  
  const [isLoading, setIsLoading] = useState(false);
  const [currentAssistantMessage, setCurrentAssistantMessage] = useState('');
  const [thinkingMessages, setThinkingMessages] = useState<Message[]>([]);

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
                    
                    // Capture conversation_summary if available and update memory
                    if (parsedData.conversation_summary) {
                      console.log('Conversation summary received:', parsedData.conversation_summary);
                      try {
                        // Update memory with the conversation summary from backend
                        await updateMemory(parsedData.conversation_summary, messages.length + 1);
                      } catch (memoryError) {
                        console.warn('Failed to update memory with conversation summary:', memoryError);
                      }
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
                  
                  // Improved regex pattern to handle different error formats with multiline content
                  // This handles both direct LLM output errors and Stream errors
                  const patterns = [
                    /Could not parse LLM output: `([\s\S]+?)`/,  // Standard format
                    /Stream error: "Could not parse LLM output: `([\s\S]+?)`/,  // Stream error format
                    /OUTPUT_PARSING_FAILURE[\s\S]*?`([\s\S]+?)`/  // OUTPUT_PARSING_FAILURE format
                  ];
                  
                  let match = null;
                  for (const pattern of patterns) {
                    match = errorMsg.match(pattern);
                    if (match && match[1]) break;
                  }
                  
                  if (match && match[1]) {
                    // Extract the actual content from the error message
                    // Clean up any escaped characters
                    let extractedContent = match[1];
                    let hasExtractedThinking = false;
                    
                    try {
                      // Try to handle escaped characters if they exist
                      if (extractedContent.includes('\\n')) {
                        extractedContent = JSON.parse('"' + extractedContent.replace(/"/g, '\\"') + '"');
                      }
                      
                      // Handle <think> tag format - extract thinking and response parts
                      const thinkMatch = extractedContent.match(/<think>([\s\S]+?)<\/think>([\s\S]+)/);
                      if (thinkMatch && thinkMatch.length >= 3) {
                        const thinkingContent = thinkMatch[1].trim();
                        const responseContent = thinkMatch[2].trim();
                        
                        // Add thinking content to thinking messages
                        if (thinkingContent) {
                          const thinkingMessage: Message = {
                            content: thinkingContent,
                            role: 'thinking',
                            timestamp: Date.now(),
                            isThinking: true
                          };
                          setThinkingMessages(prev => [...prev, thinkingMessage]);
                          hasExtractedThinking = true;
                        }
                        
                        // Use only the response part for the assistant's message
                        extractedContent = responseContent;
                      }
                    } catch (e) {
                      console.warn('Failed to parse escaped characters or thinking content in extracted content', e);
                      // Continue with the original extracted content
                    }
                    
                    assistantResponse = extractedContent;
                    setCurrentAssistantMessage(assistantResponse);
                    
                    // Add the error message to the chat as a system message
                    // Only add if we successfully extracted content
                    if (extractedContent && extractedContent.trim()) {
                      // Check if we extracted thinking content
                      const hasThinking = hasExtractedThinking || (
                        thinkingMessages.length > 0 && 
                        thinkingMessages[thinkingMessages.length - 1]?.timestamp !== undefined &&
                        thinkingMessages[thinkingMessages.length - 1].timestamp! > Date.now() - 5000
                      );
                      
                      const systemMessage: Message = {
                        content: hasThinking 
                          ? 'There was an error in the response format, but I extracted both the thinking process and the response content.'
                          : 'There was an error in the response format, but I was able to extract the content.',
                        role: 'system',
                        timestamp: Date.now(),
                        id: crypto.randomUUID()
                      };
                      setMessages(prevMessages => [...prevMessages, systemMessage]);
                    }
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
        const newMessages: Message[] = [...messages, userMessage, { 
          content: assistantResponse, 
          role: 'assistant' as MessageRole,
          timestamp: Date.now() 
        }];
        setMessages(newMessages);
        
        // Check if we should update memory after this conversation
        if (shouldUpdateMemory(newMessages.length)) {
          // Fetch updated memory from backend after a short delay
          setTimeout(() => {
            try {
              fetchMemoryFromBackend();
            } catch (memoryError) {
              console.warn('Failed to fetch memory from backend:', memoryError);
            }
          }, 1000);
        }
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

  const clearMessages = useCallback(async () => {
    setMessages([]);
    setCurrentAssistantMessage('');
    setThinkingMessages([]);

    // Also clear localStorage
    if (typeof window !== 'undefined') {
      localStorage.removeItem('chatMessages');
    }
    
    // Clear memory both locally and on backend using the updated clearMemory function
    try {
      await clearMemory();
    } catch (error) {
      console.warn('Failed to clear memory:', error);
    }
  }, [clearMemory]);

  // Create a handleSubmit function to be used in the component
  const [userInput, setUserInput] = useState('');

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (userInput.trim() && !isLoading) {
      sendMessage(userInput);
      setUserInput('');
    }
  }, [userInput, isLoading, sendMessage]);

  // Memory functionality removed







  return {
    messages,
    isLoading,
    currentAssistantMessage,
    thinkingMessages,
    memory,

    sendMessage,
    stopGenerating,
    clearMessages,

    userInput,
    setUserInput,
    handleSubmit,
  };
}