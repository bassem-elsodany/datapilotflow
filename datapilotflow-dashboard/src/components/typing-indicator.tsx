import React from 'react';
import { Box, Group, Text } from '@mantine/core';
import { IconBrain } from '@tabler/icons-react';

// CSS keyframes for animations
const bounceAnimation = `
  @keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
  }
`;

const pulseAnimation = `
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

interface TypingIndicatorProps {
  message?: string;
  showIcon?: boolean;
}

export function TypingIndicator({ message = "Assistant is thinking...", showIcon = true }: TypingIndicatorProps) {
  return (
    <>
      <style>
        {bounceAnimation}
        {pulseAnimation}
      </style>
      <Group gap="xs" align="center">
        {showIcon && (
          <Box
            style={{
              animation: 'pulse 2s ease-in-out infinite',
            }}
          >
            <IconBrain size={16} color="var(--mantine-color-blue-6)" />
          </Box>
        )}
        <Text size="sm" c="dimmed" style={{ fontStyle: 'italic' }}>
          {message}
        </Text>
        <Group gap={4}>
          {[0, 1, 2].map((i) => (
            <Box
              key={i}
              style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                backgroundColor: 'var(--mantine-color-blue-6)',
                animation: 'bounce 1.4s ease-in-out infinite both',
                animationDelay: `${i * 0.16}s`,
              }}
            />
          ))}
        </Group>
      </Group>
    </>
  );
}
