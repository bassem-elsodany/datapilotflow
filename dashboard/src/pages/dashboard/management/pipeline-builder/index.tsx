/**
 * Pipeline Builder Page
 * 
 * Visual canvas-based pipeline builder for knowledge processing workflows.
 * Users can drag and drop components to create custom processing pipelines.
 */

import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { Button, Container, Group, Paper, Stack, Title } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconDeviceFloppy, IconGripVertical, IconHierarchy, IconPlayerPlay, IconRefresh, IconSettings } from '@tabler/icons-react';
import React, { useCallback, useRef, useState } from 'react';

import { Node } from 'reactflow';
import { useCreatePipeline, useExecutePipeline, useUpdatePipeline } from '@/api/resources/pipelines';
import { CanvasWrapper } from './components/Canvas';
import { NodeConfigPanel } from './components/NodeConfigPanel';
import { PipelineRunner } from './components/PipelineRunner';
import { PipelineValidator } from './components/PipelineValidator';
import { Toolbox } from './components/Toolbox';
import { usePipelineBuilder } from './hooks/usePipelineBuilder';

// Draggable Toolbox Component
interface DraggableToolboxProps {
  onAddNode: (nodeType: string, position: { x: number; y: number }) => void;
}

function DraggableToolbox({ onAddNode }: DraggableToolboxProps) {
  const [position, setPosition] = useState({ x: 20, y: 20 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const toolboxRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target instanceof HTMLElement && e.target.closest('[data-draggable="false"]')) {
      return; // Don't drag if clicking on non-draggable elements
    }

    setIsDragging(true);
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y
    });
    e.preventDefault();
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging) return;

    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Add event listeners for mouse move and up
  React.useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);

      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragStart]);

  return (
    <div
      ref={toolboxRef}
      style={{
        position: 'absolute',
        top: position.y,
        left: position.x,
        zIndex: 10,
        maxWidth: '300px',
        maxHeight: '500px',
        overflow: 'auto',
        cursor: isDragging ? 'grabbing' : 'grab',
        userSelect: 'none'
      }}
      onMouseDown={handleMouseDown}
    >
      <Paper
        shadow="lg"
        p="md"
        withBorder
        radius="md"
        style={{
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          border: isDragging ? '2px solid #228be6' : '1px solid #e0e0e0'
        }}
      >
        <Stack gap="md">
          <Group style={{ cursor: 'grab' }}>
            <IconGripVertical size={16} style={{ color: '#666' }} />
            <IconHierarchy size={20} />
            <Title order={6}>Pipeline Tools</Title>
          </Group>

          <div data-draggable="false">
            <Toolbox onAddNode={onAddNode} />
          </div>
        </Stack>
      </Paper>
    </div>
  );
}

const breadcrumbs = [
  { label: 'Dashboard', href: '/dashboard' },
  { label: 'Management', href: '/dashboard/management' },
  { label: 'Pipeline Builder' },
];

export default function PipelineBuilderPage() {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    addNode,
    updateNode,
    deleteNode,
    selectedNode,
    setSelectedNode,
    handleNodeSelect,
    validateCurrentPipeline,
    clearCanvas
  } = usePipelineBuilder();

  const [isRunning, setIsRunning] = useState(false);
  const [configModalOpened, setConfigModalOpened] = useState(false);
  const [currentPipelineId, setCurrentPipelineId] = useState<string | null>(null);

  // API Hooks
  const createPipeline = useCreatePipeline();
  const updatePipeline = useUpdatePipeline();
  const executePipeline = useExecutePipeline();

  const handleSavePipeline = useCallback(async () => {
    try {
      // Validate pipeline before saving
      const validation = validateCurrentPipeline();
      if (!validation.isValid) {
        notifications.show({
          title: 'Invalid Pipeline',
          message: `Cannot save pipeline: ${validation.errors.join(', ')}`,
          color: 'red',
        });
        return;
      }

      const pipelineData = {
        name: `Pipeline ${new Date().toLocaleString()}`,
        description: 'Pipeline created from builder',
        nodes: nodes.map((node) => ({
          id: node.id,
          type: node.data.type,
          name: node.data.name || node.data.type,
          position: node.position,
          status: node.data.status || 'pending',
          configured: node.data.configured || false,
          config: node.data.config || {},
        })),
        edges: edges.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          type: edge.type || 'arrow',
        })),
      };

      let result;
      if (currentPipelineId) {
        // Update existing pipeline
        result = await updatePipeline.mutateAsync({
          pathParams: { pipelineId: currentPipelineId },
          body: pipelineData,
        });
        notifications.show({
          title: 'Pipeline Updated',
          message: 'Your pipeline has been updated successfully',
          color: 'green',
        });
      } else {
        // Create new pipeline
        result = await createPipeline.mutateAsync({ body: pipelineData });
        setCurrentPipelineId(result.id);
        notifications.show({
          title: 'Pipeline Saved',
          message: 'Your pipeline has been saved successfully',
          color: 'green',
        });
      }
    } catch (error) {
      console.error('Error saving pipeline:', error);
      notifications.show({
        title: 'Save Failed',
        message: error instanceof Error ? error.message : 'Failed to save pipeline',
        color: 'red',
      });
    }
  }, [nodes, edges, currentPipelineId, validateCurrentPipeline, createPipeline, updatePipeline]);

  const handleRunPipeline = useCallback(async () => {
    try {
      if (isRunning) {
        setIsRunning(false);
        notifications.show({
          title: 'Pipeline Stopped',
          message: 'Pipeline execution stopped',
          color: 'orange',
        });
        return;
      }

      // Validate pipeline before running
      const validation = validateCurrentPipeline();
      if (!validation.isValid) {
        notifications.show({
          title: 'Invalid Pipeline',
          message: `Cannot run pipeline: ${validation.errors.join(', ')}`,
          color: 'red',
        });
        return;
      }

      // Save pipeline first if not saved
      if (!currentPipelineId) {
        await handleSavePipeline();
        // Wait a bit for state to update
        await new Promise((resolve) => setTimeout(resolve, 500));
      }

      if (!currentPipelineId) {
        notifications.show({
          title: 'Pipeline Not Saved',
          message: 'Please save the pipeline before running',
          color: 'orange',
        });
        return;
      }

      // Execute pipeline
      setIsRunning(true);
      const result = await executePipeline.mutateAsync({
        pathParams: { pipelineId: currentPipelineId },
        body: {},
      });

      notifications.show({
        title: 'Pipeline Started',
        message: `Pipeline execution started. Job ID: ${result.job_id}`,
        color: 'blue',
      });

      // TODO: Navigate to job monitoring page or show status
      console.log('Pipeline execution result:', result);
    } catch (error) {
      console.error('Error running pipeline:', error);
      setIsRunning(false);
      notifications.show({
        title: 'Execution Failed',
        message: error instanceof Error ? error.message : 'Failed to run pipeline',
        color: 'red',
      });
    }
  }, [isRunning, currentPipelineId, validateCurrentPipeline, handleSavePipeline, executePipeline]);

  const handleResetPipeline = useCallback(() => {
    console.log('Resetting pipeline...');
    clearCanvas();
    setConfigModalOpened(false);
  }, [clearCanvas]);

  const handleNodeConfigure = useCallback((node: Node) => {
    handleNodeSelect(node);
    setConfigModalOpened(true);
  }, [handleNodeSelect]);

  const handleCloseConfigModal = useCallback(() => {
    setConfigModalOpened(false);
  }, []);

  const handleSaveNodeConfig = useCallback((nodeId: string, config: any) => {
    updateNode(nodeId, { ...config, configured: true });
    setConfigModalOpened(false);
  }, [updateNode]);

  // Convert React Flow node to PipelineNode format for modal
  const selectedPipelineNode = selectedNode ? {
    id: selectedNode.id,
    type: selectedNode.data?.type || selectedNode.type || 'unknown',
    name: selectedNode.data?.name || 'Unnamed Node',
    position: selectedNode.position || { x: 0, y: 0 },
    status: selectedNode.data?.status || 'pending',
    configured: selectedNode.data?.configured || false,
    config: selectedNode.data || {},
  } : null;

  return (
    <Page title="Pipeline Builder">
      <PageHeader title="Pipeline Builder" breadcrumbs={breadcrumbs} />

      <Container fluid my="md">
        <Stack gap="md">
          {/* Canvas Controls */}
          <Paper shadow="sm" p="md">
            <Group justify="space-between" mb="md">
              <Title order={5}>Pipeline Canvas</Title>
              <Group>
                <Button
                  variant="light"
                  leftSection={<IconDeviceFloppy size={16} />}
                  onClick={handleSavePipeline}
                  disabled={isRunning}
                >
                  Save
                </Button>
                <Button
                  color={isRunning ? 'red' : 'blue'}
                  leftSection={isRunning ? <IconSettings size={16} /> : <IconPlayerPlay size={16} />}
                  onClick={handleRunPipeline}
                >
                  {isRunning ? 'Stop' : 'Run Pipeline'}
                </Button>
                <Button
                  variant="light"
                  leftSection={<IconRefresh size={16} />}
                  onClick={handleResetPipeline}
                >
                  Reset
                </Button>
              </Group>
            </Group>

            {/* Canvas with Floating Toolbox */}
            <div style={{ position: 'relative', width: '100%', height: '600px' }}>
              <CanvasWrapper
                nodes={nodes}
                edges={edges}
                onNodeSelect={handleNodeSelect}
                onNodeUpdate={updateNode}
                onNodeDelete={deleteNode}
                onNodeConfigure={handleNodeConfigure}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
              />

              {/* Floating Toolbox */}
              <DraggableToolbox onAddNode={addNode} />

              {/* Node Configuration Right Panel - Inside Canvas */}
              <NodeConfigPanel
                node={selectedPipelineNode}
                opened={configModalOpened}
                onClose={handleCloseConfigModal}
                onSave={handleSaveNodeConfig}
              />
            </div>
          </Paper>

          {/* Pipeline Validator */}
          <PipelineValidator validation={validateCurrentPipeline()} />

          {/* Pipeline Runner */}
          <Paper shadow="sm" p="md">
            <PipelineRunner isRunning={isRunning} />
          </Paper>
        </Stack>
      </Container>
    </Page>
  );
}