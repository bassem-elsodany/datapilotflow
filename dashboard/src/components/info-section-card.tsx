import { Box, Group, Stack, Text } from '@mantine/core';
import { ReactNode } from 'react';

interface InfoSectionCardProps {
  title: string;
  icon: ReactNode;
  color: string;
  gradientFrom?: string;
  gradientTo?: string;
  children: ReactNode;
}

export function InfoSectionCard({
  title,
  icon,
  color,
  gradientFrom,
  gradientTo,
  children
}: InfoSectionCardProps) {
  return (
    <Box
      style={{
        background: 'white',
        border: `1px solid ${color}15`,
        borderRadius: '12px',
        padding: '16px',
        position: 'relative',
        overflow: 'hidden',
        transition: 'all 0.3s ease'
      }}
    >
      {/* Gradient accent bar on left */}
      <Box
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          bottom: 0,
          width: '4px',
          background: `linear-gradient(180deg, ${gradientFrom || color} 0%, ${gradientTo || color} 100%)`
        }}
      />

      <Stack gap="sm">
        {/* Header */}
        <Group gap="xs">
          <Box
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: `linear-gradient(135deg, ${gradientFrom || color}15 0%, ${gradientTo || color}25 100%)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: color
            }}
          >
            {icon}
          </Box>
          <Text size="sm" fw={600} style={{ color }}>
            {title}
          </Text>
        </Group>

        {/* Content */}
        <Box style={{ paddingLeft: '6px' }}>
          {children}
        </Box>
      </Stack>
    </Box>
  );
}

interface InfoItemProps {
  label: string;
  value: ReactNode;
  fullWidth?: boolean;
}

export function InfoItem({ label, value, fullWidth = false }: InfoItemProps) {
  return (
    <Stack gap={4} style={{ flex: fullWidth ? '1 1 100%' : '1 1 45%', minWidth: fullWidth ? '100%' : '200px' }}>
      <Text size="xs" c="dimmed" fw={600} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
        {label}
      </Text>
      <Box style={{ fontSize: 'var(--mantine-font-size-sm)', fontWeight: 500 }}>
        {value}
      </Box>
    </Stack>
  );
}
