/**
 * Pipeline Edge Component
 * 
 * Custom edge component for the pipeline builder canvas.
 * Displays connection between nodes with status indicators.
 */

import { memo } from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';

interface PipelineEdgeData {
  status?: 'idle' | 'active' | 'completed' | 'failed';
  label?: string;
}

export const PipelineEdge = memo(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  data,
  selected,
}: EdgeProps<PipelineEdgeData>) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const getEdgeColor = (status?: string) => {
    switch (status) {
      case 'active':
        return '#007bff';
      case 'completed':
        return '#28a745';
      case 'failed':
        return '#dc3545';
      default:
        return '#6c757d';
    }
  };

  const getEdgeWidth = (status?: string) => {
    switch (status) {
      case 'active':
        return 3;
      case 'completed':
        return 2;
      case 'failed':
        return 2;
      default:
        return 1;
    }
  };

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: getEdgeColor(data?.status),
          strokeWidth: getEdgeWidth(data?.status),
          strokeDasharray: data?.status === 'active' ? '5,5' : 'none',
          ...style,
        }}
      />
      {data?.label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              background: 'white',
              padding: '2px 6px',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 500,
              border: '1px solid #e9ecef',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            }}
            className="nodrag nopan"
          >
            {data.label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});

PipelineEdge.displayName = 'PipelineEdge';
