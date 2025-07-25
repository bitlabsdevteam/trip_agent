import React from 'react';

export default function About() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 text-center">About AI Chat Assistant</h1>
      
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Project Overview</h2>
        <p className="mb-4">
          This AI Chat Assistant is a full-stack application that demonstrates real-time streaming 
          communication between a Next.js frontend and a Flask backend API. The application 
          leverages server-sent events (SSE) to provide a responsive, token-by-token streaming 
          experience similar to ChatGPT.
        </p>
        <p>
          The chat interface maintains conversation history, allowing the AI to reference previous 
          messages in its responses, creating a more coherent and contextual interaction experience.
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
          <h2 className="text-xl font-semibold mb-4">Frontend Technologies</h2>
          <ul className="list-disc pl-5 space-y-2">
            <li>Next.js 14 with App Router</li>
            <li>TypeScript for type safety</li>
            <li>Tailwind CSS for styling</li>
            <li>Server-Sent Events handling</li>
            <li>Responsive design for all devices</li>
          </ul>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
          <h2 className="text-xl font-semibold mb-4">Backend Technologies</h2>
          <ul className="list-disc pl-5 space-y-2">
            <li>Flask for the API server</li>
            <li>Flask-RESTX for API documentation</li>
            <li>Server-Sent Events for streaming</li>
            <li>Conversation memory for context</li>
            <li>CORS handling for cross-origin requests</li>
          </ul>
        </div>
      </div>
      
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 mt-6">
        <h2 className="text-xl font-semibold mb-4">How It Works</h2>
        <p className="mb-4">
          When you send a message, the frontend makes a POST request to the Flask backend. 
          The backend processes your message through an AI agent that has access to conversation 
          history and various tools. The response is streamed back token-by-token in real-time, 
          providing a fluid and interactive experience.
        </p>
        <p>
          The streaming implementation uses Server-Sent Events (SSE), which allows the server 
          to push updates to the client as they become available, without requiring the client 
          to make multiple requests.
        </p>
      </div>
    </div>
  );
}