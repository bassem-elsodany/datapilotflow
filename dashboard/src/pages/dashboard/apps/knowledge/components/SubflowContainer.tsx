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
        backgroundColor: selected ? 'rgba(34, 139, 230, 0.05)' : 'rgba(200, 200, 200, 0.05)',
        border: selected ? '2px dashed #228be6' : '2px dashed #ccc',
        borderRadius: '8px',
        padding: '12px',
        boxSizing: 'border-box',
        pointerEvents: 'none',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'flex-start',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: '-20px',
          left: '12px',
          backgroundColor: selected ? '#228be6' : '#666',
          color: 'white',
          padding: '2px 8px',
          borderRadius: '4px',
          fontSize: '12px',
          fontWeight: 600,
        }}
      >
        {data.title}
      </div>
    </div>
  );
});

SubflowContainer.displayName = 'SubflowContainer';
