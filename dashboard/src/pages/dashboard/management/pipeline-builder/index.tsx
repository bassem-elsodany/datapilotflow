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
import { IconDeviceFloppy, IconGripVertical, IconHierarchy, IconPlayerPlay, IconRefresh, IconSettings, IconChevronRight } from '@tabler/icons-react';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';

import { Node } from 'reactflow';
import { useCreatePipeline, useExecutePipeline, useUpdatePipeline, useGetJobAsPipeline } from '@/api/resources/pipelines';
import { useGetKnowledgeJob, useCreateKnowledgeJob, useUpdateKnowledgeJob } from '@/api/resources/knowledge-jobs';
import { useCreateKnowledgeSourceConfig, useUpdateKnowledgeSourceConfig } from '@/api/resources/knowledge-sources';
import { useCreateDocumentSplitter, useUpdateDocumentSplitter } from '@/api/resources/document-splitters';
import { useCreateVectorDBCollection, useUpdateVectorDBCollection } from '@/api/resources/vectordb-collections';
import { CanvasWrapper } from './components/Canvas';
import { NodeConfigPanel } from './components/NodeConfigPanel';
import { JobSettingsPanel, JobSettings } from './components/JobSettingsPanel';
import { PipelineRunner } from './components/PipelineRunner';
import { PipelineValidator } from './components/PipelineValidator';
import { TemplateSelector } from './components/TemplateSelector';
import { Toolbox } from './components/Toolbox';
import { usePipelineBuilder } from './hooks/usePipelineBuilder';
import { RagTemplate } from './templates/ragTemplates';
import { convertPipelineToJob, extractLLMFilterConfig } from './utils/pipelineToJobConverter';
import { convertJobToPipeline, extractComponentsFromJob } from './utils/jobToPipelineConverter';
import { calculateStaircaseLayout } from './utils/nodeLayoutCalculator';

// Docked Toolbox Sidebar Component
interface DockedToolboxProps {
  onAddNode: (nodeType: string, position: { x: number; y: number }) => void;
  isCollapsed: boolean;
  onToggle: () => void;
}

function DockedToolbox({ onAddNode, isCollapsed, onToggle }: DockedToolboxProps) {
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        height: '100%',
        width: isCollapsed ? '60px' : '320px',
        backgroundColor: 'white',
        borderRight: '1px solid #e0e0e0',
        boxShadow: isCollapsed ? 'none' : '2px 0 8px rgba(0,0,0,0.1)',
        zIndex: 5,
        transition: 'all 0.3s ease',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Toggle Button */}
      <Button
        variant="subtle"
        size="sm"
        onClick={onToggle}
        style={{
          alignSelf: isCollapsed ? 'center' : 'flex-start',
          margin: '8px',
          minWidth: isCollapsed ? '40px' : 'auto'
        }}
        leftSection={<IconChevronRight size={16} style={{ transform: isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.3s' }} />}
      >
        {!isCollapsed && 'Hide'}
      </Button>

      {/* Toolbox Content */}
      {!isCollapsed && (
        <div style={{ flex: 1, padding: '12px', overflow: 'auto' }}>
          <Stack gap="sm">
            <Group gap="xs">
              <IconHierarchy size={18} />
              <Title order={6}>Pipeline Tools</Title>
            </Group>
            <Toolbox onAddNode={onAddNode} />
          </Stack>
        </div>
      )}
    </div>
  );
}

const breadcrumbs = [
  { label: 'Dashboard', href: '/dashboard' },
  { label: 'Management', href: '/dashboard/management' },
  { label: 'Pipeline Builder' },
];

export default function PipelineBuilderPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const fromJobId = searchParams.get('fromJobId');

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
    clearCanvas,
    loadPipeline
  } = usePipelineBuilder();

  const [isRunning, setIsRunning] = useState(false);
  const [configModalOpened, setConfigModalOpened] = useState(false);
  const [jobSettingsOpened, setJobSettingsOpened] = useState(false);
  const [currentPipelineId, setCurrentPipelineId] = useState<string | null>(null);
  const [pipelineLoaded, setPipelineLoaded] = useState(false);
  const [templateSelectorOpened, setTemplateSelectorOpened] = useState(!fromJobId);
  const [showBlankCanvas, setShowBlankCanvas] = useState(false);
  const [toolboxCollapsed, setToolboxCollapsed] = useState(false);
  const [isSavingJob, setIsSavingJob] = useState(false);
  const [isEditingExistingJob, setIsEditingExistingJob] = useState(!!fromJobId);
  const [originalJobData, setOriginalJobData] = useState<any>(null);

  // API Hooks - Create
  const createPipeline = useCreatePipeline();
  const updatePipeline = useUpdatePipeline();
  const executePipeline = useExecutePipeline();
  const createKnowledgeSourceConfig = useCreateKnowledgeSourceConfig();
  const createDocumentSplitter = useCreateDocumentSplitter();
  const createVectorDBCollection = useCreateVectorDBCollection();
  const createKnowledgeJob = useCreateKnowledgeJob();

  // API Hooks - Update
  const updateKnowledgeSourceConfig = useUpdateKnowledgeSourceConfig();
  const updateDocumentSplitter = useUpdateDocumentSplitter();
  const updateVectorDBCollection = useUpdateVectorDBCollection();
  const updateKnowledgeJob = useUpdateKnowledgeJob();

  // Load job data if fromJobId is present
  const { data: jobData } = useGetKnowledgeJob(fromJobId as string, {
    enabled: !!fromJobId && fromJobId.length > 0,
  });

  // Fetch pipeline from job if fromJobId is present
  const { data: jobPipeline, isLoading: isLoadingPipeline, error: pipelineError } = useGetJobAsPipeline(fromJobId as string, {
    enabled: !!fromJobId && fromJobId.length > 0,
  });

  // Show error if pipeline fetch fails
  useEffect(() => {
    if (pipelineError) {
      console.error('Failed to fetch pipeline from job:', pipelineError);
      notifications.show({
        title: 'Error Loading Pipeline',
        message: `Failed to load pipeline: ${pipelineError.message || 'Unknown error'}`,
        color: 'red',
      });
    }
  }, [pipelineError]);

  // Load pipeline when job data is available (convert from job config to visual pipeline)
  useEffect(() => {
    if (fromJobId && jobData && !pipelineLoaded) {
      console.log('Loading pipeline from job data:', fromJobId);
      console.log('Job data:', jobData);

      // Store original job data for comparison later (to detect changes)
      setOriginalJobData(JSON.parse(JSON.stringify(jobData)));

      try {
        // Extract components from the job data
        const components = extractComponentsFromJob(jobData);

        // Convert job configuration to visual pipeline
        const pipelineRepresentation = convertJobToPipeline(components);

        console.log('Converted pipeline nodes:', pipelineRepresentation.nodes);
        console.log('Converted pipeline edges:', pipelineRepresentation.edges);

        // Load the pipeline
        loadPipeline({
          nodes: pipelineRepresentation.nodes,
          edges: pipelineRepresentation.edges,
        });

        setPipelineLoaded(true);

        notifications.show({
          title: 'Pipeline Loaded',
          message: `Successfully loaded pipeline from job with ${pipelineRepresentation.nodes.length} nodes`,
          color: 'green',
        });
      } catch (error) {
        console.error('Error converting job to pipeline:', error);
        notifications.show({
          title: 'Error Loading Pipeline',
          message: `Failed to convert job to pipeline: ${error instanceof Error ? error.message : 'Unknown error'}`,
          color: 'red',
        });
      }
    }
  }, [fromJobId, jobData, pipelineLoaded, loadPipeline]);

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

  const handleSelectTemplate = useCallback((template: RagTemplate, selectedOptionalNodes: string[]) => {
    // Get all nodes to include (required + selected optional)
    const nodesToInclude = new Set([
      ...template.requiredNodes.map(n => n.type),
      ...template.optionalNodes.filter(n => selectedOptionalNodes.includes(n.id)).map(n => n.type)
    ]);

    // Filter nodes to only include selected ones
    let filteredNodes = template.defaultNodes.filter(node => {
      const nodeType = (node.data as any).type;
      return nodesToInclude.has(nodeType);
    });

    // Apply staircase layout (2 nodes per row, stacking vertically)
    filteredNodes = calculateStaircaseLayout(filteredNodes, {
      horizontalSpacing: 300,
      verticalSpacing: 140,
      startX: 50,
      startY: 50,
    });

    // Update edges to only connect existing nodes
    const nodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredEdges = template.defaultEdges.filter(
      edge => nodeIds.has(edge.source) && nodeIds.has(edge.target)
    );

    // Load the filtered template
    loadPipeline({
      nodes: filteredNodes,
      edges: filteredEdges,
    });

    setTemplateSelectorOpened(false);

    const staircaseRows = Math.ceil(filteredNodes.length / 2);
    notifications.show({
      title: 'Template Loaded',
      message: `${template.name} template loaded with ${filteredNodes.length} nodes (staircase layout: ${staircaseRows} row${staircaseRows > 1 ? 's' : ''})`,
      color: 'green',
    });
  }, [loadPipeline]);

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

  const handleUpdateExistingJob = useCallback(async (jobSettings: JobSettings) => {
    try {
      setIsSavingJob(true);

      // Validate pipeline
      const validation = validateCurrentPipeline();
      if (!validation.isValid) {
        notifications.show({
          title: 'Invalid Pipeline',
          message: `Cannot update pipeline: ${validation.errors.join(', ')}`,
          color: 'red',
        });
        setJobSettingsOpened(false);
        setIsSavingJob(false);
        return;
      }

      // Convert pipeline to job configurations
      const conversionResult = convertPipelineToJob({
        nodes,
        edges,
        jobName: jobSettings.jobName,
        jobDescription: jobSettings.jobDescription,
        jobSettings: {
          batchSize: jobSettings.batchSize,
          saveToFile: jobSettings.saveToFile,
          writeConsolidatedFile: jobSettings.writeConsolidatedFile,
          clearCollectionBeforeStart: jobSettings.clearCollectionBeforeStart,
          checkDuplicatesBeforeInsert: jobSettings.checkDuplicatesBeforeInsert,
        },
      });

      console.log('Update conversion result:', conversionResult);

      // Update Step 1: Update KnowledgeSourceConfig
      console.log('Updating KnowledgeSourceConfig...');
      notifications.show({
        title: 'Updating Configuration',
        message: 'Updating knowledge source configuration...',
        color: 'blue',
      });

      const sourceConfigId = originalJobData?.knowledge_source_config?.id || jobData?.knowledge_source_config_id;
      const sourceConfigUpdateResult = await updateKnowledgeSourceConfig.mutateAsync({
        pathParams: { configId: sourceConfigId },
        body: conversionResult.knowledgeSourceConfig,
      });

      console.log('KnowledgeSourceConfig updated:', sourceConfigUpdateResult);
      notifications.show({
        title: 'Configuration Updated',
        message: `Knowledge source config updated`,
        color: 'blue',
      });

      // Update Step 2: Update DocumentSplitter if it exists
      let splitterId = originalJobData?.document_splitter?.id || jobData?.splitter_id;
      if (conversionResult.documentSplitter && splitterId) {
        console.log('Updating DocumentSplitter...');
        const splitterUpdateResult = await updateDocumentSplitter.mutateAsync({
          pathParams: { splitterId },
          body: conversionResult.documentSplitter,
        });
        console.log('DocumentSplitter updated:', splitterUpdateResult);
      }

      // Update Step 3: Update VectorDBCollection
      console.log('Updating VectorDBCollection...');
      const vectorDBId = originalJobData?.vectordb_collection?.id || jobData?.vectordb_collection_id;
      const vectorDBUpdateResult = await updateVectorDBCollection.mutateAsync({
        pathParams: { collectionId: vectorDBId },
        body: conversionResult.vectorDBCollection,
      });
      console.log('VectorDBCollection updated:', vectorDBUpdateResult);

      // Update Step 4: Update KnowledgeJob with new settings
      console.log('Updating KnowledgeJob...');
      const jobUpdatePayload = {
        name: jobSettings.jobName,
        description: jobSettings.jobDescription || '',
        batch_size: jobSettings.batchSize,
        save_to_file: jobSettings.saveToFile,
        write_consolidated_file: jobSettings.writeConsolidatedFile,
        clear_collection_before_start: jobSettings.clearCollectionBeforeStart,
        check_duplicates_before_insert: jobSettings.checkDuplicatesBeforeInsert,
      };

      console.log('Job update payload:', jobUpdatePayload);

      const jobUpdateResult = await updateKnowledgeJob.mutateAsync({
        pathParams: { jobId: fromJobId },
        body: jobUpdatePayload,
      });

      notifications.show({
        title: 'Job Updated Successfully',
        message: `Knowledge job "${jobSettings.jobName}" has been updated`,
        color: 'green',
      });

      setJobSettingsOpened(false);
      setIsSavingJob(false);

      // Navigate back to job details after a short delay
      setTimeout(() => {
        navigate(`/dashboard/management/knowledge-jobs/${fromJobId}`);
      }, 1500);
    } catch (error) {
      console.error('Error updating job:', error);
      setIsSavingJob(false);
      notifications.show({
        title: 'Job Update Failed',
        message: error instanceof Error ? error.message : 'Failed to update job',
        color: 'red',
      });
    }
  }, [nodes, edges, validateCurrentPipeline, updateKnowledgeSourceConfig, updateDocumentSplitter, updateVectorDBCollection, updateKnowledgeJob, fromJobId, jobData, originalJobData, navigate]);

  const handleSaveAndExecuteJob = useCallback(async (jobSettings: JobSettings) => {
    try {
      setIsSavingJob(true);

      // Validate pipeline
      const validation = validateCurrentPipeline();
      if (!validation.isValid) {
        notifications.show({
          title: 'Invalid Pipeline',
          message: `Cannot execute pipeline: ${validation.errors.join(', ')}`,
          color: 'red',
        });
        setJobSettingsOpened(false);
        setIsSavingJob(false);
        return;
      }

      // Convert pipeline to job configurations
      const conversionResult = convertPipelineToJob({
        nodes,
        edges,
        jobName: jobSettings.jobName,
        jobDescription: jobSettings.jobDescription,
        jobSettings: {
          batchSize: jobSettings.batchSize,
          saveToFile: jobSettings.saveToFile,
          writeConsolidatedFile: jobSettings.writeConsolidatedFile,
          clearCollectionBeforeStart: jobSettings.clearCollectionBeforeStart,
          checkDuplicatesBeforeInsert: jobSettings.checkDuplicatesBeforeInsert,
        },
      });

      console.log('Conversion result:', conversionResult);

      // Step 1: Create KnowledgeSourceConfig
      console.log('Creating KnowledgeSourceConfig...', conversionResult.knowledgeSourceConfig);
      notifications.show({
        title: 'Creating Configuration',
        message: 'Creating knowledge source configuration...',
        color: 'blue',
      });

      const sourceConfigResult = await createKnowledgeSourceConfig.mutateAsync({
        configData: conversionResult.knowledgeSourceConfig,
      });

      console.log('KnowledgeSourceConfig created:', sourceConfigResult);
      notifications.show({
        title: 'Configuration Created',
        message: `Knowledge source config created with ID: ${sourceConfigResult.id}`,
        color: 'blue',
      });

      // Step 2: Create DocumentSplitter if needed
      let splitterId = conversionResult.documentSplitter?.id;
      if (conversionResult.documentSplitter && !splitterId) {
        console.log('Creating DocumentSplitter...', conversionResult.documentSplitter);
        const splitterResult = await createDocumentSplitter.mutateAsync({
          body: conversionResult.documentSplitter,
        });
        splitterId = splitterResult.id;
        console.log('DocumentSplitter created:', splitterResult);
      }

      // Step 3: Create VectorDBCollection
      console.log('Creating VectorDBCollection...', conversionResult.vectorDBCollection);
      const vectorDBResult = await createVectorDBCollection.mutateAsync({
        body: conversionResult.vectorDBCollection,
      });
      console.log('VectorDBCollection created:', vectorDBResult);

      // Step 4: Create KnowledgeJob with the IDs we got from previous steps
      console.log('Creating KnowledgeJob...');
      const jobCreatePayload = {
        name: jobSettings.jobName,
        description: jobSettings.jobDescription || '',
        splitter_id: splitterId,
        embedding_model_provider_id: conversionResult.vectorDBCollection.embedding_model_provider_id,
        embedding_model_name: conversionResult.vectorDBCollection.embedding_model_name,
        batch_size: jobSettings.batchSize,
        save_to_file: jobSettings.saveToFile,
        write_consolidated_file: jobSettings.writeConsolidatedFile,
        clear_collection_before_start: jobSettings.clearCollectionBeforeStart,
        check_duplicates_before_insert: jobSettings.checkDuplicatesBeforeInsert,
        existing_collection_id: vectorDBResult.id,
      };

      console.log('Job creation payload:', jobCreatePayload);

      // The createKnowledgeJob hook expects pathParams with configId
      const jobResult = await createKnowledgeJob.mutateAsync({
        pathParams: { configId: sourceConfigResult.id },
        body: jobCreatePayload,
      });

      notifications.show({
        title: 'Job Created Successfully',
        message: `Knowledge job "${jobSettings.jobName}" has been created. Job ID: ${jobResult.id}`,
        color: 'green',
      });

      setJobSettingsOpened(false);
      setIsSavingJob(false);

      // Navigate to job details after a short delay
      setTimeout(() => {
        navigate(`/dashboard/management/knowledge-jobs/${jobResult.id}`);
      }, 1500);
    } catch (error) {
      console.error('Error saving and executing job:', error);
      setIsSavingJob(false);
      notifications.show({
        title: 'Job Creation Failed',
        message: error instanceof Error ? error.message : 'Failed to create job',
        color: 'red',
      });
    }
  }, [nodes, edges, validateCurrentPipeline, createKnowledgeSourceConfig, createDocumentSplitter, createVectorDBCollection, createKnowledgeJob, navigate]);

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

      <Container fluid my="md" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 200px)' }}>
        <Stack gap="md" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Canvas Controls */}
          <Paper shadow="sm" p="md">
            <Group justify="space-between" mb="md">
              <Title order={5}>Pipeline Canvas</Title>
              <Group>
                <Button
                  variant="light"
                  leftSection={<IconHierarchy size={16} />}
                  onClick={() => setTemplateSelectorOpened(true)}
                  disabled={isRunning}
                >
                  Load Template
                </Button>
                <Button
                  variant="light"
                  leftSection={<IconDeviceFloppy size={16} />}
                  onClick={handleSavePipeline}
                  disabled={isRunning}
                >
                  Save
                </Button>
                <Button
                  color="green"
                  leftSection={<IconPlayerPlay size={16} />}
                  onClick={() => setJobSettingsOpened(true)}
                  disabled={isRunning || isSavingJob}
                >
                  Save & Execute Job
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
                  disabled={isRunning || isSavingJob}
                >
                  Reset
                </Button>
              </Group>
            </Group>

            {/* Canvas with Docked Toolbox */}
            <div style={{ position: 'relative', width: '100%', height: 'calc(100vh - 380px)', minHeight: '500px' }}>
              <div style={{ width: '100%', height: '100%', position: 'relative', zIndex: 0, paddingLeft: toolboxCollapsed ? '60px' : '320px', transition: 'padding-left 0.3s ease' }}>
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
              </div>

              {/* Docked Toolbox Sidebar */}
              <DockedToolbox
                onAddNode={addNode}
                isCollapsed={toolboxCollapsed}
                onToggle={() => setToolboxCollapsed(!toolboxCollapsed)}
              />

              {/* Node Configuration Right Panel - Inside Canvas */}
              <NodeConfigPanel
                node={selectedPipelineNode}
                opened={configModalOpened}
                onClose={handleCloseConfigModal}
                onSave={handleSaveNodeConfig}
              />
            </div>
          </Paper>

          {/* Pipeline Validator and Runner - Compact */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <Paper shadow="sm" p="sm">
              <PipelineValidator validation={validateCurrentPipeline()} />
            </Paper>

            <Paper shadow="sm" p="sm">
              <PipelineRunner isRunning={isRunning} />
            </Paper>
          </div>
        </Stack>
      </Container>

      {/* Template Selector Modal */}
      <TemplateSelector
        opened={templateSelectorOpened}
        onClose={() => setTemplateSelectorOpened(false)}
        onSelectTemplate={handleSelectTemplate}
      />

      {/* Job Settings Panel Modal */}
      <JobSettingsPanel
        opened={jobSettingsOpened}
        onClose={() => setJobSettingsOpened(false)}
        onSave={isEditingExistingJob ? handleUpdateExistingJob : handleSaveAndExecuteJob}
        isLoading={isSavingJob}
        isEditing={isEditingExistingJob}
      />
    </Page>
  );
}