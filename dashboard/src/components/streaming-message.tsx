import { Box, Code, Paper, Text } from '@mantine/core';
import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { EnhancedMessageRenderer } from './enhanced-message-renderer';

// CSS keyframes for animations
const fadeInAnimation = `
  @keyframes fadeIn {
    0% { opacity: 0; transform: translateY(10px); }
    100% { opacity: 1; transform: translateY(0); }
  }
`;

const blinkAnimation = `
  @keyframes blink {
    0%, 49% { opacity: 1; }
    50%, 100% { opacity: 0; }
  }
`;

interface MessageMetadata {
  source_urls?: string[];
  chunk_ids?: string[];
  document_count?: number;
  enhancement_strategy?: string;
  enhanced_query?: string;
  enhanced_queries?: string[];
}

interface StreamingMessageProps {
  content: string;
  isStreaming: boolean;
  timestamp: Date | string;
  onComplete?: () => void;
  showSender?: boolean;
  senderName?: string;
  metadata?: MessageMetadata;
}

export function StreamingMessage({
  content,
  isStreaming,
  timestamp,
  onComplete,
  showSender = true,
  senderName = "Assistant",
  metadata
}: StreamingMessageProps) {
  const [displayContent, setDisplayContent] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    if (isStreaming) {
      setIsTyping(true);

      // For real-time streaming, show content immediately as it comes
      setDisplayContent(content);
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
  }, [content, isStreaming, onComplete]);

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
        {blinkAnimation}
      </style>
      <Paper
        p="md"
        style={{
          backgroundColor: 'var(--mantine-color-gray-1)',
          borderRadius: '18px 18px 18px 4px',
          maxWidth: '100%',
          animation: 'fadeIn 0.3s ease-out',
          position: 'relative',
          overflow: 'hidden',
          border: '1px solid var(--mantine-color-gray-3)',
        }}
      >
        {showSender && (
          <Text size="sm" fw={500} mb="xs">
            {senderName}
          </Text>
        )}

        <Box>
          {/* During streaming: show raw text (like typing), After complete: show enhanced markdown */}
          {isStreaming ? (
            <Box
              style={{
                fontFamily: 'var(--mantine-font-family-monospace)',
                fontSize: '12px',
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap',
                color: 'var(--mantine-color-gray-8)',
              }}
            >
              {displayContent}
              <Box
                component="span"
                style={{
                  display: 'inline-block',
                  width: '8px',
                  height: '16px',
                  backgroundColor: 'var(--mantine-color-blue-6)',
                  marginLeft: '2px',
                  animation: 'blink 1s infinite',
                }}
              />
            </Box>
          ) : (
            <EnhancedMessageRenderer
              content={displayContent}
              metadata={metadata}
              isRawMode={displayContent.includes('**Raw Results Mode**')}
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
