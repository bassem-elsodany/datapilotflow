/**
 * Job to Pipeline Converter
 *
 * Converts backend job configurations back to visual pipeline nodes/edges
 * This is the reverse of pipelineToJobConverter
 *
 * Source of truth: KnowledgeSourceConfig + KnowledgeJob
 * Visual representation: Pipeline nodes and edges
 */

export interface JobToPipelineInput {
  knowledgeSourceConfig: any;
  knowledgeJob: any;
  documentSplitter?: any;
  vectorDBCollection?: any;
  llmContentFilterConfig?: any;
}

export interface PipelineRepresentation {
  nodes: any[];
  edges: any[];
}

/**
 * Create data source node based on KnowledgeSourceConfig
 */
function createDataSourceNode(config: any): any {
  const sourceType = config.content_source_type;
  let nodeType = 'website'; // default
  const position = { x: 0, y: 0 };

  if (sourceType === 'web_scraping') {
    const mode = config.scraping_mode;
    if (mode === 'single_page') {
      nodeType = 'single_page';
    } else if (mode === 'multiple_pages') {
      nodeType = 'multiple_pages';
    } else {
      nodeType = 'website';
    }
  } else if (sourceType === 'local_files') {
    nodeType = 'local_files';
  }

  return {
    id: `${nodeType}-1`,
    type: 'pipelineNode',
    position,
    data: {
      id: `${nodeType}-1`,
      type: nodeType,
      name: config.name || `${nodeType} Source`,
      status: 'configured',
      configured: true,
      url: config.url || '',
      crawl_depth: config.crawl_depth ?? (nodeType === 'website' ? 2 : 0),
      target_elements: (config.target_elements || []).join(', '),
      exclude_elements: (config.exclude_elements || []).join(', '),
      local_files: config.local_files || [],
      scraping_mode: config.scraping_mode,
    },
  };
}

/**
 * Create output format node based on output_format
 */
function createOutputFormatNode(config: any): any {
  const format = config.output_format || 'html';

  return {
    id: 'outputFormat-1',
    type: 'pipelineNode',
    position: { x: 200, y: 0 },
    data: {
      id: 'outputFormat-1',
      type: 'outputFormat',
      name: 'Output Format',
      status: 'configured',
      configured: true,
      format: format,
    },
  };
}

/**
 * Create LLM content filter node if present
 */
function createLLMFilterNode(config: any): any | null {
  if (!config || !config.llm_model_name) {
    return null;
  }

  return {
    id: 'llmContentFilter-1',
    type: 'pipelineNode',
    position: { x: 400, y: 0 },
    data: {
      id: 'llmContentFilter-1',
      type: 'llmContentFilter',
      name: config.name || 'LLM Content Filter',
      status: 'configured',
      configured: true,
      llm_model_name: config.llm_model_name,
      instruction: config.instruction || '',
      temperature: config.temperature || 0.0,
      chunk_token_threshold: config.chunk_token_threshold || 500,
    },
  };
}

/**
 * Create text splitter node from DocumentSplitter config
 */
function createTextSplitterNode(config: any): any {
  const defaultConfig = {
    splitter_type: 'text',
    chunk_size: 1024,
    chunk_overlap: 200,
    name: 'Document Splitter',
  };

  const finalConfig = config || defaultConfig;
  const xPos = config ? 600 : 400; // Adjust position based on if llm filter exists

  return {
    id: 'textSplitter-1',
    type: 'pipelineNode',
    position: { x: xPos, y: 0 },
    data: {
      id: 'textSplitter-1',
      type: 'textSplitter',
      name: finalConfig.name || 'Document Splitter',
      status: 'configured',
      configured: true,
      splitterType: finalConfig.splitter_type,
      chunkSize: finalConfig.chunk_size,
      chunkOverlap: finalConfig.chunk_overlap,
      headersToSplitOn: finalConfig.headers_to_split_on || [],
      sectionsToSplitOn: finalConfig.sections_to_split_on || [],
    },
  };
}

/**
 * Create embedding generator node
 */
function createEmbeddingGeneratorNode(): any {
  return {
    id: 'embeddingGenerator-1',
    type: 'pipelineNode',
    position: { x: 800, y: 0 },
    data: {
      id: 'embeddingGenerator-1',
      type: 'embeddingGenerator',
      name: 'Embedding Generator',
      status: 'configured',
      configured: true,
      embeddingModel: 'text-embedding-3-small',
      modelProvider: 'openai',
    },
  };
}

/**
 * Create vector database node from VectorDBCollection config
 */
function createVectorDatabaseNode(config: any): any {
  const defaultConfig = {
    collection_name: 'default-collection',
    embedding_model_name: 'text-embedding-3-small',
    vector_dimension: 1536,
  };

  const finalConfig = config || defaultConfig;

  return {
    id: 'vectorDatabase-1',
    type: 'pipelineNode',
    position: { x: 1000, y: 0 },
    data: {
      id: 'vectorDatabase-1',
      type: 'vectorDatabase',
      name: 'Vector Database',
      status: 'configured',
      configured: true,
      collectionName: finalConfig.collection_name,
      embeddingModel: finalConfig.embedding_model_name,
      modelProvider: finalConfig.embedding_model_provider_id || 'openai',
      vectorDimension: finalConfig.vector_dimension,
    },
  };
}

/**
 * Create edges connecting the nodes
 */
function createEdges(nodes: any[]): any[] {
  const edges: any[] = [];
  const nodeIds = nodes.map((n) => n.id);

  // Connect nodes in sequence
  for (let i = 0; i < nodeIds.length - 1; i++) {
    edges.push({
      id: `edge-${nodeIds[i]}-${nodeIds[i + 1]}`,
      source: nodeIds[i],
      target: nodeIds[i + 1],
      type: 'arrow',
      animated: true,
      style: { stroke: '#228be6', strokeWidth: 2 },
    });
  }

  return edges;
}

/**
 * Adjust node positions to distribute them evenly
 */
function adjustNodePositions(nodes: any[]): any[] {
  const spacing = 200;
  return nodes.map((node, index) => ({
    ...node,
    position: { x: index * spacing, y: 0 },
  }));
}

/**
 * Main conversion function: Job → Pipeline
 */
export function convertJobToPipeline(input: JobToPipelineInput): PipelineRepresentation {
  const {
    knowledgeSourceConfig,
    knowledgeJob,
    documentSplitter,
    vectorDBCollection,
    llmContentFilterConfig,
  } = input;

  if (!knowledgeSourceConfig) {
    throw new Error('KnowledgeSourceConfig is required');
  }

  const nodes: any[] = [];

  // 1. Add data source node
  nodes.push(createDataSourceNode(knowledgeSourceConfig));

  // 2. Add output format node
  nodes.push(createOutputFormatNode(knowledgeSourceConfig));

  // 3. Add LLM filter node if present
  const llmFilterNode = createLLMFilterNode(llmContentFilterConfig);
  if (llmFilterNode) {
    nodes.push(llmFilterNode);
  }

  // 4. Add text splitter node
  nodes.push(createTextSplitterNode(documentSplitter));

  // 5. Add embedding generator node
  nodes.push(createEmbeddingGeneratorNode());

  // 6. Add vector database node
  nodes.push(createVectorDatabaseNode(vectorDBCollection));

  // Adjust positions for even distribution
  const adjustedNodes = adjustNodePositions(nodes);

  // Create edges connecting all nodes
  const edges = createEdges(adjustedNodes);

  return {
    nodes: adjustedNodes,
    edges,
  };
}

/**
 * Extract component configs from full job response
 * This helps when you have a job with nested/expanded relationships
 */
export function extractComponentsFromJob(jobData: any): JobToPipelineInput {
  return {
    knowledgeSourceConfig: jobData.knowledge_source_config,
    knowledgeJob: jobData,
    documentSplitter: jobData.document_splitter,
    vectorDBCollection: jobData.vectordb_collection,
    llmContentFilterConfig: jobData.llm_content_filter_config,
  };
}
