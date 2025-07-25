import React from 'react';

type MessageRole = 'user' | 'assistant' | 'system' | 'thinking';

interface ChatMessageProps {
  content: string;
  role: MessageRole;
  timestamp?: number;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ content, role, timestamp }) => {
  // Format timestamp if available
  const formattedTime = timestamp ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
  
  // Determine styling based on message role
  const getMessageStyles = () => {
    switch (role) {
      case 'user':
        return {
          container: 'justify-end',
          message: 'bg-blue-500 text-white',
          timestamp: 'text-blue-200'
        };
      case 'assistant':
        return {
          container: 'justify-start',
          message: 'bg-gray-700 text-white',
          timestamp: 'text-gray-300'
        };
      case 'system':
        return {
          container: 'justify-center',
          message: 'bg-red-500 text-white',
          timestamp: 'text-red-200'
        };
      case 'thinking':
        return {
          container: 'justify-start',
          message: 'bg-gray-500 text-white italic',
          timestamp: 'text-gray-300'
        };
      default:
        return {
          container: 'justify-start',
          message: 'bg-gray-700 text-white',
          timestamp: 'text-gray-300'
        };
    }
  };

  const styles = getMessageStyles();

  return (
    <div className={`flex ${styles.container} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${styles.message}`}
      >
        <div className="whitespace-pre-wrap">{content}</div>
        {timestamp && (
          <div className={`text-xs mt-1 text-right ${styles.timestamp}`}>
            {formattedTime}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;