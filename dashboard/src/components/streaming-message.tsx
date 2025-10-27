import { Box, Code, Paper, Text } from '@mantine/core';
import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

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
          {/* During streaming: show raw text (like typing), After complete: show formatted markdown */}
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
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ inline, className, children, ...props }: any) {
                  return !inline ? (
                    <Code
                      block
                      style={{
                        display: 'block',
                        backgroundColor: 'var(--mantine-color-gray-1)',
                        padding: '16px',
                        borderRadius: '8px',
                        fontFamily: 'var(--mantine-font-family-monospace)',
                        fontSize: '12px',
                        lineHeight: '1.6',
                        margin: '12px 0',
                        overflowX: 'auto',
                        whiteSpace: 'pre',
                      }}
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </Code>
                  ) : (
                    <Code
                      style={{
                        backgroundColor: 'var(--mantine-color-gray-1)',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontFamily: 'var(--mantine-font-family-monospace)',
                        fontSize: '0.9em',
                      }}
                      {...props}
                    >
                      {children}
                    </Code>
                  );
                },
                h1: ({ children }) => (
                  <h1 style={{ marginTop: '24px', marginBottom: '16px', fontSize: '24px', fontWeight: 700 }}>
                    {children}
                  </h1>
                ),
                h2: ({ children }) => (
                  <h2 style={{ marginTop: '24px', marginBottom: '12px', fontSize: '18px', fontWeight: 600 }}>
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 style={{ marginTop: '20px', marginBottom: '10px', fontSize: '16px', fontWeight: 600 }}>
                    {children}
                  </h3>
                ),
                ul: ({ children }) => (
                  <ul style={{ marginTop: '12px', marginBottom: '12px', paddingLeft: '24px' }}>
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol style={{ marginTop: '12px', marginBottom: '12px', paddingLeft: '24px' }}>
                    {children}
                  </ol>
                ),
                li: ({ children }) => (
                  <li style={{ marginTop: '6px', marginBottom: '6px', lineHeight: '1.6' }}>
                    {children}
                  </li>
                ),
                p: ({ children }) => (
                  <p style={{ marginTop: '12px', marginBottom: '12px', lineHeight: '1.6' }}>
                    {children}
                  </p>
                ),
                strong: ({ children }) => (
                  <strong style={{ fontWeight: 600, color: 'var(--mantine-color-gray-9)' }}>
                    {children}
                  </strong>
                ),
                a: ({ href, children }) => (
                  <a
                    href={href}
                    style={{
                      color: 'var(--mantine-color-blue-6)',
                      textDecoration: 'none',
                      borderBottom: '1px solid var(--mantine-color-blue-3)',
                    }}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {children}
                  </a>
                ),
              }}
            >
              {displayContent}
            </ReactMarkdown>
          )}
        </Box>

        <Text size="xs" c="dimmed" mt="xs">
          {formatTimestamp(timestamp)}
        </Text>
      </Paper>
    </>
  );
}
