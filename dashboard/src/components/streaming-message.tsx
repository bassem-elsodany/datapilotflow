import React, { useEffect, useState } from 'react';
import { Box, Paper, Text } from '@mantine/core';
import { MarkdownRenderer } from './markdown-renderer';
import { TypingIndicator } from './typing-indicator';

// CSS keyframes for animations
const fadeInAnimation = `
  @keyframes fadeIn {
    0% { opacity: 0; transform: translateY(10px); }
    100% { opacity: 1; transform: translateY(0); }
  }
`;

const shimmerAnimation = `
  @keyframes shimmer {
    0% { background-position: -200px 0; }
    100% { background-position: calc(200px + 100%) 0; }
  }
`;

interface StreamingMessageProps {
  content: string;
  isStreaming: boolean;
  timestamp: Date | string;
  onComplete?: () => void;
  showSender?: boolean;
  senderName?: string;
}

export function StreamingMessage({ 
  content, 
  isStreaming, 
  timestamp, 
  onComplete, 
  showSender = true, 
  senderName = "Assistant" 
}: StreamingMessageProps) {
  const [displayContent, setDisplayContent] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    if (isStreaming) {
      setIsTyping(true);
      
      // For real-time streaming, show content immediately as it comes
      if (content !== displayContent) {
        setDisplayContent(content);
      }
    } else {
      // When streaming is complete, ensure full content is shown
      setDisplayContent(content);
      setIsTyping(false);
      
      // Add completion animation
      if (onComplete) {
        setTimeout(() => {
          onComplete();
        }, 300);
      }
    }
  }, [content, isStreaming, onComplete, displayContent]);

  const formatTimestamp = (timestamp: Date | string): string => {
    try {
      const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
      return date.toLocaleTimeString();
    } catch (error) {
      return 'Invalid time';
    }
  };

  return (
    <>
      <style>
        {fadeInAnimation}
        {shimmerAnimation}
      </style>
      <Paper
        p="md"
        style={{
          backgroundColor: 'var(--mantine-color-gray-0)',
          alignSelf: 'flex-start',
          maxWidth: '80%',
          animation: 'fadeIn 0.3s ease-out',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
      {showSender && (
        <Text size="sm" fw={500} mb="xs">
          {senderName}
        </Text>
      )}
      
      <Box>
        {/* Show formatted markdown during streaming */}
        <MarkdownRenderer content={displayContent} />
        
        {isStreaming && (
          <Box mt="xs">
            <TypingIndicator message="Assistant is typing..." />
          </Box>
        )}
        
        {isTyping && content && (
          <Box
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: 2,
              background: 'linear-gradient(90deg, transparent, var(--mantine-color-blue-6), transparent)',
              backgroundSize: '200px 100%',
              animation: 'shimmer 2s infinite',
            }}
          />
        )}
      </Box>
      
      <Text size="xs" c="dimmed" mt="xs">
        {formatTimestamp(timestamp)}
      </Text>
    </Paper>
    </>
  );
}
