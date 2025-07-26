'use client';

import { useState, useRef, useEffect } from 'react';
import { useChat } from '../hooks/useChat';
import MemoryDisplay from './MemoryDisplay';

export default function StreamingDemo() {
  const {
    messages,
    thinkingMessages,
    userInput,
    setUserInput,
    handleSubmit,
    isLoading,
    stopGenerating,
    clearMessages,
    currentAssistantMessage,
    memory
  } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Scroll to bottom when messages change or when streaming
  useEffect(() => {
    scrollToBottom();
  }, [messages, currentAssistantMessage, thinkingMessages]);

  // Only show the most recent thinking message
  const latestThinkingMessage = thinkingMessages.length > 0 ? thinkingMessages[thinkingMessages.length - 1] : null;

  return (
    <div className="flex flex-col h-screen w-full">
      <h1 className="text-2xl font-bold p-4 text-center bg-gray-800 text-white">Token-by-Token Streaming Demo</h1>
      
      <div className="flex-1 overflow-auto border-t border-gray-200 pb-2">
        <div className="max-w-6xl mx-auto w-full p-4 space-y-6">
          <MemoryDisplay memory={memory} onClearMemory={clearMessages} />
          {messages.map((message, index) => (
            <div 
              key={index} 
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`p-4 rounded-lg ${message.role === 'user' ? 'bg-blue-100 dark:bg-blue-900 dark:text-white' : 'bg-gray-100 dark:bg-gray-700 dark:text-white'} max-w-[80%]`}>
                <div className="font-semibold mb-1">{message.role === 'user' ? 'YOU' : 'Trip Agent'}</div>
                <div className="whitespace-pre-wrap">{message.content}</div>
              </div>
            </div>
          ))}
          
          {/* Show only the latest thinking message during streaming without background */}
          {isLoading && latestThinkingMessage && (
            <div className="flex justify-start">
              <div className="max-w-[80%]">
                <div className="font-semibold mb-1 text-gray-500 flex items-center">
                  <svg className="w-4 h-4 mr-1 animate-spin" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Thinking...
                </div>
                <div className="whitespace-pre-wrap text-gray-600 dark:text-gray-300">{latestThinkingMessage.content}</div>
              </div>
            </div>
          )}
          
          {/* Show streaming response */}
          {isLoading && currentAssistantMessage && (
            <div className="flex justify-start">
              <div className="p-4 rounded-lg bg-gray-100 dark:bg-gray-700 dark:text-white max-w-[80%]">
                <div className="font-semibold mb-1">Trip Agent</div>
                <div className="whitespace-pre-wrap">{currentAssistantMessage}</div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>
      
      <div className="max-w-5xl mx-auto w-full p-4 sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 shadow-md z-10">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="Type your message..."
            disabled={isLoading}
            className="flex-1 p-4 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base shadow-sm"
          />
          {isLoading ? (
            <button 
              type="button" 
              onClick={stopGenerating}
              className="px-6 py-4 bg-red-500 text-white font-medium rounded-lg hover:bg-red-600 transition-colors shadow-sm"
            >
              Stop
            </button>
          ) : (
            <button 
              type="submit" 
              disabled={!userInput.trim()}
              className="px-6 py-4 bg-blue-500 text-white font-medium rounded-lg hover:bg-blue-600 transition-colors disabled:bg-blue-300 disabled:hover:bg-blue-300 shadow-sm"
            >
              Send
            </button>
          )}
          <button 
            type="button" 
            onClick={clearMessages}
            className="px-6 py-4 bg-gray-500 text-white font-medium rounded-lg hover:bg-gray-600 transition-colors shadow-sm"
          >
            Clear
          </button>
        </form>
      </div>
    </div>
  );
}