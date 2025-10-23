import { Box, Group, Stack, Text, ThemeIcon } from '@mantine/core';
import { ReactNode } from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  color: string;
  gradientFrom?: string;
  gradientTo?: string;
  description?: string;
  trend?: {
    value: number;
    label: string;
  };
}

export function StatCard({
  title,
  value,
  icon,
  color,
  gradientFrom,
  gradientTo,
  description,
  trend
}: StatCardProps) {
  return (
    <Box
      style={{
        background: `linear-gradient(135deg, ${gradientFrom || color}08 0%, ${gradientTo || color}15 100%)`,
        border: `1px solid ${color}20`,
        borderRadius: '12px',
        padding: '14px',
        position: 'relative',
        overflow: 'hidden',
        transition: 'all 0.3s ease',
        cursor: 'default'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-4px)';
        e.currentTarget.style.boxShadow = `0 8px 24px ${color}20`;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      {/* Decorative gradient bar on top */}
      <Box
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          background: `linear-gradient(90deg, ${gradientFrom || color} 0%, ${gradientTo || color} 100%)`
        }}
      />

      <Stack gap="sm">
        <Group justify="space-between" align="flex-start">
          <Stack gap={2}>
            <Text size="xs" c="dimmed" fw={500}>
              {title}
            </Text>
            <Text size="lg" fw={700} style={{ color }}>
              {value}
            </Text>
            {description && (
              <Text size="xs" c="dimmed">
                {description}
              </Text>
            )}
          </Stack>

          <ThemeIcon
            size={36}
            radius="md"
            variant="light"
            style={{
              background: `linear-gradient(135deg, ${gradientFrom || color} 0%, ${gradientTo || color} 100%)`,
              color: 'white',
              border: 'none'
            }}
          >
            {icon}
          </ThemeIcon>
        </Group>

        {trend && (
          <Group gap="xs">
            <Text
              size="xs"
              fw={600}
              style={{
                color: trend.value >= 0 ? '#51cf66' : '#ff6b6b'
              }}
            >
              {trend.value >= 0 ? '+' : ''}{trend.value}%
            </Text>
            <Text size="xs" c="dimmed">
              {trend.label}
            </Text>
          </Group>
        )}
      </Stack>
    </Box>
  );
}
