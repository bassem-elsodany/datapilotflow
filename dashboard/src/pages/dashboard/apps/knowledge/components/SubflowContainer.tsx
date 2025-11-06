/**
 * Subflow Container
 *
 * Renders a background box container for grouped subflow nodes
 * Shows when subflow is expanded to visually group the steps together
 */

import { memo } from 'react';
import { NodeProps } from 'reactflow';

interface SubflowContainerData {
  id: string;
  title: string;
  width: number;
  height: number;
}

export const SubflowContainer = memo(({ data, selected }: NodeProps<SubflowContainerData>) => {
  return (
    <div
      style={{
        position: 'absolute',
        width: `${data.width}px`,
        height: `${data.height}px`,
        backgroundColor: selected ? 'rgba(34, 139, 230, 0.15)' : 'rgba(230, 230, 230, 0.8)',
        border: selected ? '2px solid #228be6' : '2px solid #999',
        borderRadius: '8px',
        padding: '24px 12px 12px 12px',
        boxSizing: 'border-box',
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: '6px',
          left: '12px',
          backgroundColor: selected ? '#228be6' : '#666',
          color: 'white',
          padding: '4px 10px',
          borderRadius: '4px',
          fontSize: '11px',
          fontWeight: 600,
          letterSpacing: '0.5px',
        }}
      >
        {data.title}
      </div>
    </div>
  );
});

SubflowContainer.displayName = 'SubflowContainer';
