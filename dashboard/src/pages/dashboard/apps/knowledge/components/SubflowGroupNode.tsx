/**
 * Subflow Group Node Component
 *
 * Renders a group/container node that displays expanded subflow steps as a grouped box
 * Used for RAG Agent and Task Agent subflows in Assistant mode
 */

import { memo, useState } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Group, Text, Box, Stack } from '@mantine/core';

interface SubflowGroupNodeData {
  id: string;
  agentName: string;
  steps: Array<{
    id: string;
    label: string;
  }>;
  isExpanded: boolean;
}

export const SubflowGroupNode = memo(({ data, selected }: NodeProps<SubflowGroupNodeData>) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <>
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Left}
        id="target"
        style={{ opacity: 0, pointerEvents: 'none' }}
      />

      {/* Group container for subflow steps */}
      <Box
        p={data.isExpanded ? 'md' : 'sm'}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        style={{
          backgroundColor: selected ? '#e3f2fd' : isHovered ? '#f5f5f5' : '#ffffff',
          border: selected ? '2px solid #228be6' : '1px solid #d0d0d0',
          borderRadius: '8px',
          minWidth: data.isExpanded ? '340px' : '140px',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          boxShadow: selected ? '0 0 8px rgba(34, 139, 230, 0.3)' : isHovered ? '0 2px 8px rgba(0,0,0,0.1)' : 'none',
        }}
      >
        {/* Agent title with expand/collapse indicator */}
        <Group justify="space-between" gap="xs">
          <Text size="sm" fw={600} c={selected ? '#228be6' : '#333'}>
            {data.agentName}
          </Text>
          {data.isExpanded && (
            <Text size="xs" c="dimmed">
              {data.steps.length} steps
            </Text>
          )}
        </Group>

        {/* Steps display - only when expanded */}
        {data.isExpanded && data.steps.length > 0 && (
          <Stack gap="xs" mt="sm">
            <Group gap="xs" wrap="nowrap" justify="center">
              {data.steps.map((step, index) => (
                <div key={step.id} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Box
                    p="6px 10px"
                    style={{
                      backgroundColor: '#e7f5ff',
                      border: '1px solid #74c0fc',
                      borderRadius: '4px',
                      minWidth: '70px',
                      textAlign: 'center',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    <Text size="xs" fw={500} c="#1f7ed8">
                      {step.label}
                    </Text>
                  </Box>
                  {index < data.steps.length - 1 && (
                    <Text size="xs" c="gray">
                      →
                    </Text>
                  )}
                </div>
              ))}
            </Group>
          </Stack>
        )}
      </Box>

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Right}
        id="source"
        style={{ opacity: 0, pointerEvents: 'none' }}
      />
    </>
  );
});

SubflowGroupNode.displayName = 'SubflowGroupNode';
