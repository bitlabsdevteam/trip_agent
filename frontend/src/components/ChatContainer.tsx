'use client';

import React, { useRef, useEffect, useState } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { useChat } from '@/hooks/useChat';
import LoadingSpinner from './LoadingSpinner';

export const ChatContainer: React.FC = () => {
  const { 
    messages, 
    isLoading, 
    currentAssistantMessage, 
    sendMessage, 
    stopGenerating,
    clearMessages 
  } = useChat({
    onError: (error) => console.error('Chat error:', error)
  });
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isClient, setIsClient] = useState(false);

  // Set isClient to true when component mounts on client
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentAssistantMessage]);

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Conversation</h2>
        {isClient && messages.length > 0 && (
          <button
            onClick={clearMessages}
            className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
          >
            Clear chat
          </button>
        )}
      </div>
      
      <div className="flex-grow overflow-y-auto mb-4 space-y-4 p-2">
        {isClient && messages.length === 0 ? (
          <div className="text-center text-gray-500 my-8">
            <h2 className="text-xl font-semibold mb-2">Welcome to the AI Chat!</h2>
            <p>Start a conversation by sending a message below.</p>
            <div className="mt-4 flex flex-col gap-2 text-sm">
              <p>Try asking questions like:</p>
              <button 
                onClick={() => sendMessage("What is the weather in New York?")}
                className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                What is the weather in New York?
              </button>
              <button 
                onClick={() => sendMessage("Tell me about Paris")}
                className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                Tell me about Paris
              </button>
              <button 
                onClick={() => sendMessage("What time is it in Tokyo?")}
                className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                What time is it in Tokyo?
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <ChatMessage 
              key={index} 
              content={msg.content} 
              role={msg.role} 
              timestamp={msg.timestamp} 
            />
          ))
        )}
        
        {isClient && currentAssistantMessage && (
          <ChatMessage 
            content={currentAssistantMessage} 
            role="assistant" 
          />
        )}
        
        {isClient && isLoading && !currentAssistantMessage && (
          <div className="flex justify-center my-4">
            <LoadingSpinner size="small" />
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <div className="relative">
        {isClient && isLoading && (
          <button
            onClick={stopGenerating}
            className="absolute right-2 top-2 z-10 bg-red-500 text-white px-2 py-1 rounded text-xs"
          >
            Stop
          </button>
        )}
        <ChatInput onSendMessage={sendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
};

export default ChatContainer;