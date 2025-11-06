/**
 * Conversation Node Component
 *
 * Compact circular icon node for conversation pipeline canvas
 * Matches the job pipeline node style with small 32px circle + icon + label
 */

import { memo, useState } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Text, Tooltip } from '@mantine/core';
import {
  IconSettings,
  IconFilter,
  IconDatabase,
  IconBrain,
  IconCheck,
  IconClock,
  IconMessageCircle,
  IconWand,
  IconArrowDown,
} from '@tabler/icons-react';

interface ConversationNodeData {
  id: string;
  name: string;
  type: 'userQuery' | 'settings' | 'enhancement' | 'retrieval' | 'reranking' | 'llm' | 'formatter';
  description: string;
  configured: boolean;
}

export const ConversationNode = memo(({ data, selected }: NodeProps<ConversationNodeData>) => {
  const [isHovered, setIsHovered] = useState(false);

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'userQuery':
        return <IconMessageCircle size={14} />;
      case 'settings':
        return <IconSettings size={14} />;
      case 'enhancement':
        return <IconWand size={14} />;
      case 'retrieval':
        return <IconDatabase size={14} />;
      case 'reranking':
        return <IconArrowDown size={14} />;
      case 'llm':
        return <IconBrain size={14} />;
      case 'formatter':
        return <IconDatabase size={14} />;
      default:
        return <IconSettings size={14} />;
    }
  };

  const getStatusColor = (configured: boolean) => {
    return configured ? '#51cf66' : '#868e96';
  };

  const getStatusIcon = (configured: boolean) => {
    if (configured) {
      return <IconCheck size={10} />;
    }
    return <IconClock size={10} />;
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        position: 'relative',
        cursor: 'pointer',
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Hidden handles */}
      <Handle
        type="target"
        position={Position.Left}
        id="target"
        style={{ opacity: 0, pointerEvents: 'none' }}
      />

      {/* Circular Icon Node */}
      <Tooltip label={`${data.name}\n${data.description}`} multiline withArrow position="top">
        <div style={{ position: 'relative' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: selected ? '#e3f2fd' : '#ffffff',
              border: selected ? '2px solid #228be6' : '1px solid #e0e0e0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: selected ? '0 0 4px rgba(34, 139, 230, 0.4)' : '0 1px 2px rgba(0,0,0,0.1)',
              transition: 'all 0.2s ease',
              color: selected ? '#228be6' : '#333',
            }}
          >
            {getNodeIcon(data.type)}
          </div>

          {/* Status indicator circle */}
          <div
            style={{
              position: 'absolute',
              top: '-1px',
              right: '-1px',
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: getStatusColor(data.configured),
              border: '1px solid #ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {getStatusIcon(data.configured)}
          </div>
        </div>
      </Tooltip>

      {/* Label underneath */}
      <div style={{ marginTop: '4px', textAlign: 'center', maxWidth: '60px' }}>
        <Text
          size="xs"
          fw={500}
          ta="center"
          style={{
            fontSize: '6px',
            lineHeight: 1.0,
            color: selected ? '#228be6' : '#333',
          }}
        >
          {data.name}
        </Text>
      </div>

      {/* Hidden handles */}
      <Handle
        type="source"
        position={Position.Right}
        id="source"
        style={{ opacity: 0, pointerEvents: 'none' }}
      />
    </div>
  );
});

ConversationNode.displayName = 'ConversationNode';
