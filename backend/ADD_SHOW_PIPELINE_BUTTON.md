# Add "Show Pipeline" Button to Job Details Page

## Overview

This document provides the complete implementation to add a "Show Pipeline" button to the job details page at:
`dashboard/management/knowledge-sources/job-details/{jobId}`

The button will navigate to a pipeline visualization page that displays the job configuration as a visual pipeline.

---

## Implementation Steps

### Step 1: Add Icon Import

**File:** `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/knowledge-sources/job-details/index.tsx`

**Change at lines 25-40** (add IconGitBranch):

```typescript
import {
  IconAlertCircle,
  IconArrowLeft,
  IconCheck,
  IconClock,
  IconCpu,
  IconDatabase,
  IconEdit,
  IconFileText,
  IconGitBranch,        // ← ADD THIS LINE
  IconInfoCircle,
  IconPlayerPlay,
  IconRefresh,
  IconScissors,
  IconSettings,
  IconX
} from '@tabler/icons-react';
```

---

### Step 2: Add "Show Pipeline" Button

**File:** `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/knowledge-sources/job-details/index.tsx`

**Change at lines 173-189** (add new button after Edit Job button):

```typescript
        <Group>
          <Button
            variant="filled"
            leftSection={<IconEdit size={16} />}
            component={Link}
            to={`/dashboard/management/knowledge-sources/job-edit/${jobId}`}
          >
            Edit Job
          </Button>
          {/* ← ADD THIS NEW BUTTON */}
          <Button
            variant="light"
            color="teal"
            leftSection={<IconGitBranch size={16} />}
            component={Link}
            to={`/dashboard/management/pipeline-builder?jobId=${jobId}`}
          >
            Show Pipeline
          </Button>
          {/* ← END OF NEW BUTTON */}
          <Button
            variant="subtle"
            leftSection={<IconRefresh size={16} />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
        </Group>
```

---

## Alternative Implementation (If Pipeline Builder Route Exists)

If you already have a dedicated route for job pipeline visualization, use this instead:

### Option A: Dedicated Pipeline Visualization Route

```typescript
<Button
  variant="light"
  color="teal"
  leftSection={<IconGitBranch size={16} />}
  component={Link}
  to={`/dashboard/management/knowledge-sources/jobs/${jobId}/pipeline`}
>
  Show Pipeline
</Button>
```

### Option B: Open in Modal/Drawer

If you want to show the pipeline in a modal instead of navigating:

```typescript
import { useDisclosure } from '@mantine/hooks';
import { Modal } from '@mantine/core';

// Inside component:
const [opened, { open, close }] = useDisclosure(false);

// Button:
<Button
  variant="light"
  color="teal"
  leftSection={<IconGitBranch size={16} />}
  onClick={open}
>
  Show Pipeline
</Button>

// Modal (add before closing </Page>):
<Modal
  opened={opened}
  onClose={close}
  title="Job Pipeline Visualization"
  size="95vw"
  fullScreen
>
  <PipelineVisualization jobId={jobId} />
</Modal>
```

---

## Backend API Endpoint (If Not Yet Implemented)

To support pipeline visualization, add this endpoint to the backend:

**File:** `/Users/bassem.elsodany/workspaces/datapilotflow/backend/src/api/routers/knowledge/pipeline_router.py`

```python
@router.get("/jobs/{job_id}/pipeline")
async def get_job_as_pipeline(
    job_id: str,
    current_user: User = Depends(get_current_user),
    pipeline_service: PipelineService = Depends(get_pipeline_service),
    job_service: KnowledgeJobService = Depends(get_knowledge_job_service)
) -> Pipeline:
    """
    Convert a knowledge job to pipeline visualization.

    This enables users to:
    - View wizard-created jobs as pipeline visualizations
    - Edit pipeline and update the job

    Args:
        job_id: The job ID to convert
        current_user: Authenticated user
        pipeline_service: Pipeline service
        job_service: Job service

    Returns:
        Pipeline object with nodes and edges
    """
    # Fetch job with all related configs
    job = job_service.get_knowledge_job(job_id, current_user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch related configurations
    source_config = job_service.knowledge_source_service.get_knowledge_source_config(
        job.knowledge_source_config_id,
        current_user.id
    )
    if not source_config:
        raise HTTPException(status_code=404, detail="Knowledge source config not found")

    # Fetch document splitter if exists
    document_splitter = None
    if job.splitter_id:
        document_splitter = job_service.document_splitter_service.get_splitter(
            job.splitter_id,
            current_user.id
        )

    # Fetch vector DB collection
    vectordb_collection = None
    if job.vectordb_collection_id:
        vectordb_collection = job_service.vectordb_collection_service.get_collection(
            job.vectordb_collection_id,
            current_user.id
        )

    # Convert job to pipeline
    pipeline = pipeline_service.convert_job_to_pipeline(
        knowledge_job=job,
        knowledge_source_config=source_config,
        document_splitter=document_splitter,
        vectordb_collection=vectordb_collection,
        user_id=current_user.id
    )

    return pipeline
```

---

## Frontend API Hook

**File:** `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/api/resources/pipelines.ts`

Add this hook if it doesn't exist:

```typescript
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { Pipeline } from './types';

export const useGetJobPipeline = (jobId: string, options = {}) => {
  return useQuery({
    queryKey: ['job-pipeline', jobId],
    queryFn: async () => {
      const response = await api.get<Pipeline>(`/pipelines/jobs/${jobId}/pipeline`);
      return response.data;
    },
    enabled: !!jobId,
    ...options
  });
};
```

---

## Pipeline Visualization Component Example

**File:** `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/components/pipeline-visualization.tsx`

```typescript
import { useGetJobPipeline } from '@/api/resources/pipelines';
import { Alert, Center, Loader } from '@mantine/core';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';

interface PipelineVisualizationProps {
  jobId: string;
}

export function PipelineVisualization({ jobId }: PipelineVisualizationProps) {
  const { data: pipeline, isLoading, error } = useGetJobPipeline(jobId);

  if (isLoading) {
    return (
      <Center h={400}>
        <Loader size="lg" />
      </Center>
    );
  }

  if (error || !pipeline) {
    return (
      <Alert color="red" title="Error">
        Failed to load pipeline visualization
      </Alert>
    );
  }

  // Convert pipeline nodes and edges to ReactFlow format
  const nodes = pipeline.nodes.map(node => ({
    id: node.id,
    type: 'default',
    data: { label: node.name },
    position: node.position
  }));

  const edges = pipeline.edges.map(edge => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    type: edge.type
  }));

  return (
    <div style={{ width: '100%', height: '80vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        attributionPosition="bottom-right"
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
```

---

## Routes Update (If Using Dedicated Page)

**File:** `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/routes/paths.ts`

Add to paths object:

```typescript
jobPipeline: (jobId: string) => `/dashboard/management/knowledge-sources/jobs/${jobId}/pipeline`,
```

**File:** `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/routes/router.tsx`

Add route:

```typescript
{
  path: '/dashboard/management/knowledge-sources/jobs/:jobId/pipeline',
  element: LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/job-pipeline')),
},
```

---

## Visual Result

After implementation, the job details page will have this button layout:

```
[← Back to Jobs]                    [Edit Job]  [Show Pipeline]  [Refresh]
```

The "Show Pipeline" button will:
- Use a teal color scheme to match the data flow theme
- Display a git branch icon (representing pipeline flow)
- Navigate to the pipeline builder with the job data pre-loaded
- Allow users to visualize and potentially edit the job configuration

---

## Testing Checklist

- [ ] Import IconGitBranch successfully
- [ ] Button renders in job details page
- [ ] Button appears between "Edit Job" and "Refresh"
- [ ] Button has correct styling (light variant, teal color)
- [ ] Clicking button navigates to correct URL
- [ ] Pipeline visualization loads for the job
- [ ] All job configurations are correctly represented as pipeline nodes
- [ ] User can navigate back to job details from pipeline view

---

## Quick Implementation (Copy-Paste Ready)

### File 1: Icon Import (Line ~34)

```typescript
  IconGitBranch,
```

### File 2: Button (After line 181, before Refresh button)

```typescript
          <Button
            variant="light"
            color="teal"
            leftSection={<IconGitBranch size={16} />}
            component={Link}
            to={`/dashboard/management/pipeline-builder?jobId=${jobId}`}
          >
            Show Pipeline
          </Button>
```

That's it! Two simple changes to add the button.

---

## Complete Modified Section (Lines 164-190)

```typescript
      <Group justify="space-between" mb="md">
        <Button
          variant="subtle"
          leftSection={<IconArrowLeft size={16} />}
          component={Link}
          to={paths.dashboard.management.knowledgeSources.jobs}
        >
          Back to Jobs
        </Button>
        <Group>
          <Button
            variant="filled"
            leftSection={<IconEdit size={16} />}
            component={Link}
            to={`/dashboard/management/knowledge-sources/job-edit/${jobId}`}
          >
            Edit Job
          </Button>
          <Button
            variant="light"
            color="teal"
            leftSection={<IconGitBranch size={16} />}
            component={Link}
            to={`/dashboard/management/pipeline-builder?jobId=${jobId}`}
          >
            Show Pipeline
          </Button>
          <Button
            variant="subtle"
            leftSection={<IconRefresh size={16} />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
        </Group>
      </Group>
```

---

🎉 **Implementation Complete!** The "Show Pipeline" button will now appear on all job details pages, enabling bidirectional navigation between wizard-created jobs and pipeline visualization.
