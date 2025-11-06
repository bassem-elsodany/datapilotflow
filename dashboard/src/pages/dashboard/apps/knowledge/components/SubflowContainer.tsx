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
        width: `${data.width}px`,
        height: `${data.height}px`,
        backgroundColor: 'rgba(200, 220, 255, 0.4)',
        border: '2px solid #74a9e0',
        borderRadius: '6px',
        padding: '0px',
        boxSizing: 'border-box',
        pointerEvents: 'none',
        position: 'relative',
        zIndex: -1,
      }}
    />
  );
});

SubflowContainer.displayName = 'SubflowContainer';
