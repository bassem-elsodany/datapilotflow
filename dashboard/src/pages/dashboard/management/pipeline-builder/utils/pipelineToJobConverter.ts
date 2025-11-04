/**
 * Pipeline to Job Converter
 *
 * Converts visual pipeline state (nodes/edges) to backend configurations:
 * - KnowledgeSourceConfig (data source + extraction + filtering + output)
 * - DocumentSplitter (chunking config)
 * - VectorDBCollection (vector storage)
 * - KnowledgeJob (orchestration with job settings)
 */

export interface PipelineConverterInput {
  nodes: any[];
  edges: any[];
  jobName: string;
  jobDescription?: string;
  jobSettings: {
    batchSize: number;
    saveToFile: boolean;
    writeConsolidatedFile: boolean;
    clearCollectionBeforeStart: boolean;
    checkDuplicatesBeforeInsert: boolean;
  };
}

export interface ConversionResult {
  knowledgeSourceConfig: any;
  documentSplitter?: any;
  vectorDBCollection: any;
  knowledgeJob?: any; // Deprecated - we now build this in the pipeline builder
}

/**
 * Find a node by type in the pipeline
 */
function findNodeByType(nodes: any[], type: string): any {
  return nodes.find(n => n.data?.type === type);
}

/**
 * Find all nodes of a type
 */
function findNodesByType(nodes: any[], type: string): any[] {
  return nodes.filter(n => n.data?.type === type);
}

/**
 * Find incoming edge to a node
 */
function findIncomingEdge(nodeId: string, edges: any[]): any {
  return edges.find(e => e.target === nodeId);
}

/**
 * Convert pipeline to KnowledgeSourceConfig
 */
function createKnowledgeSourceConfig(nodes: any[], edges: any[], jobSettings: any): any {
  // Find data source node (website, single_page, multiple_pages, or local_files)
  const dataSourceNode = findNodeByType(nodes, 'website') ||
                        findNodeByType(nodes, 'single_page') ||
                        findNodeByType(nodes, 'multiple_pages') ||
                        findNodeByType(nodes, 'local_files');

  if (!dataSourceNode) {
    throw new Error('Pipeline must have at least one data source node (website, single_page, multiple_pages, or local_files)');
  }

  const sourceType = dataSourceNode.data.type;
  const sourceConfig = dataSourceNode.data;

  // Determine content source type
  let contentSourceType = 'web_scraping';
  let scrapingMode = sourceType;

  if (['html_files', 'markdown_files', 'pdf_files', 'docx_files', 'txt_files'].includes(sourceType)) {
    contentSourceType = 'local_files';
  }

  // Find LLM content filter node if present
  const llmFilterNode = findNodeByType(nodes, 'llmContentFilter');
  const llmFilterConfig = llmFilterNode?.data || null;

  // Find output format node
  const outputFormatNode = findNodeByType(nodes, 'outputFormat');
  let outputFormat = 'html';
  if (outputFormatNode) {
    outputFormat = outputFormatNode.data.format || 'html';
  } else {
    // Fallback based on legacy nodes if outputFormat node not present
    if (findNodeByType(nodes, 'markdownGenerator')) {
      outputFormat = 'markdown';
    } else if (findNodeByType(nodes, 'llmMarkdownGenerator')) {
      outputFormat = 'llm_markdown';
    }
  }

  // Build KnowledgeSourceConfig
  const config: any = {
    name: sourceConfig.name || `Config for ${jobSettings.jobName || 'Pipeline'}`,
    description: jobSettings.jobDescription || '',
    content_source_type: contentSourceType,
    scraping_mode: scrapingMode,
    output_format: outputFormat,
    target_elements: [],
    content_filter_threshold: 0.6,
  };

  // Add source-specific fields
  if (contentSourceType === 'web_scraping') {
    config.url = sourceConfig.url;
    config.crawl_depth = sourceConfig.crawl_depth ?? (scrapingMode === 'website' ? 2 : 0);

    // Handle target_elements - could be string or array
    if (sourceConfig.target_elements) {
      if (typeof sourceConfig.target_elements === 'string') {
        config.target_elements = sourceConfig.target_elements.split(',').map((s: string) => s.trim()).filter((s: string) => s.length > 0);
      } else if (Array.isArray(sourceConfig.target_elements)) {
        config.target_elements = sourceConfig.target_elements;
      }
    }

    // Handle exclude_elements separately (not part of config schema, but keep for reference)
    if (sourceConfig.exclude_elements) {
      // Note: exclude_elements might not be in the schema, but keep it for now
      if (typeof sourceConfig.exclude_elements === 'string') {
        (config as any).exclude_elements = sourceConfig.exclude_elements.split(',').map((s: string) => s.trim()).filter((s: string) => s.length > 0);
      } else if (Array.isArray(sourceConfig.exclude_elements)) {
        (config as any).exclude_elements = sourceConfig.exclude_elements;
      }
    }
  } else if (contentSourceType === 'local_files') {
    config.local_files = sourceConfig.local_files || [];

    // Handle target_elements
    if (sourceConfig.target_elements) {
      if (typeof sourceConfig.target_elements === 'string') {
        config.target_elements = sourceConfig.target_elements.split(',').map((s: string) => s.trim()).filter((s: string) => s.length > 0);
      } else if (Array.isArray(sourceConfig.target_elements)) {
        config.target_elements = sourceConfig.target_elements;
      }
    }

    // Handle exclude_elements separately
    if (sourceConfig.exclude_elements) {
      if (typeof sourceConfig.exclude_elements === 'string') {
        (config as any).exclude_elements = sourceConfig.exclude_elements.split(',').map((s: string) => s.trim()).filter((s: string) => s.length > 0);
      } else if (Array.isArray(sourceConfig.exclude_elements)) {
        (config as any).exclude_elements = sourceConfig.exclude_elements;
      }
    }
  }

  // Add LLM filter if present
  if (llmFilterConfig) {
    config.llm_content_filter_id = llmFilterConfig.id || `llm-filter-${Date.now()}`;
    // Store LLM config for later creation
    (config as any)._llmFilterConfig = llmFilterConfig;
  }

  return config;
}

/**
 * Create DocumentSplitter config from pipeline
 */
function createDocumentSplitter(nodes: any[], jobSettings: any): any {
  const splitterNode = findNodeByType(nodes, 'textSplitter');

  if (!splitterNode) {
    // Return default text splitter config
    return {
      name: `Splitter for ${jobSettings.jobName || 'Pipeline'}`,
      splitter_type: 'text',
      chunk_size: 1024,
      chunk_overlap: 200,
    };
  }

  const splitterConfig = splitterNode.data;

  return {
    name: splitterConfig.name || `Splitter for ${jobSettings.jobName || 'Pipeline'}`,
    splitter_type: splitterConfig.splitterType || 'text',
    chunk_size: splitterConfig.chunkSize || 1024,
    chunk_overlap: splitterConfig.chunkOverlap || 200,
    headers_to_split_on: splitterConfig.headersToSplitOn || [],
    sections_to_split_on: splitterConfig.sectionsToSplitOn || [],
  };
}

/**
 * Create VectorDBCollection config from pipeline
 */
function createVectorDBCollection(nodes: any[], jobSettings: any): any {
  const vectorDbNode = findNodeByType(nodes, 'vectorDatabase');

  if (!vectorDbNode) {
    throw new Error('Pipeline must have a Vector Database node');
  }

  const dbConfig = vectorDbNode.data;

  return {
    collection_name: dbConfig.collectionName || `collection-${Date.now()}`,
    embedding_model_provider_id: dbConfig.modelProvider || 'openai',
    embedding_model_name: dbConfig.embeddingModel || 'text-embedding-3-small',
    vector_dimension: dbConfig.vectorDimension || 1536,
  };
}

/**
 * Create KnowledgeJob config from pipeline
 */
function createKnowledgeJob(
  jobName: string,
  knowledgeSourceConfigId: string,
  vectorDBCollectionId: string,
  documentSplitterId: string,
  jobSettings: any
): any {
  return {
    name: jobName,
    description: jobSettings.jobDescription || '',
    knowledge_source_config_id: knowledgeSourceConfigId,
    vectordb_collection_id: vectorDBCollectionId,
    splitter_id: documentSplitterId,
    batch_size: jobSettings.batchSize || 100,
    save_to_file: jobSettings.saveToFile || false,
    write_consolidated_file: jobSettings.writeConsolidatedFile || false,
    clear_collection_before_start: jobSettings.clearCollectionBeforeStart || false,
    check_duplicates_before_insert: jobSettings.checkDuplicatesBeforeInsert || false,
  };
}

/**
 * Main conversion function: Pipeline → Job
 */
export function convertPipelineToJob(input: PipelineConverterInput): ConversionResult {
  const { nodes, edges, jobName, jobDescription, jobSettings } = input;

  // Validate pipeline has required nodes
  if (!findNodeByType(nodes, 'textSplitter')) {
    throw new Error('Pipeline must have a Document Splitter node');
  }

  if (!findNodeByType(nodes, 'embeddingGenerator')) {
    throw new Error('Pipeline must have an Embedding Generator node');
  }

  if (!findNodeByType(nodes, 'vectorDatabase')) {
    throw new Error('Pipeline must have a Vector Database node');
  }

  // Create configs
  const knowledgeSourceConfig = createKnowledgeSourceConfig(nodes, edges, {
    jobName,
    jobDescription,
    ...jobSettings,
  });

  const documentSplitter = createDocumentSplitter(nodes, {
    jobName,
    ...jobSettings,
  });

  const vectorDBCollection = createVectorDBCollection(nodes, {
    jobName,
    ...jobSettings,
  });

  // Generate IDs (will be replaced by backend)
  const sourceConfigId = `source-${Date.now()}`;
  const splitterId = `splitter-${Date.now()}`;
  const vectorDbId = `vectordb-${Date.now()}`;

  const knowledgeJob = createKnowledgeJob(
    jobName,
    sourceConfigId,
    vectorDbId,
    splitterId,
    {
      jobDescription,
      ...jobSettings,
    }
  );

  return {
    knowledgeSourceConfig,
    documentSplitter,
    vectorDBCollection,
    knowledgeJob,
  };
}

/**
 * Extract LLM filter config if present
 */
export function extractLLMFilterConfig(knowledgeSourceConfig: any): any | null {
  if ((knowledgeSourceConfig as any)._llmFilterConfig) {
    const config = (knowledgeSourceConfig as any)._llmFilterConfig;
    delete (knowledgeSourceConfig as any)._llmFilterConfig;
    return {
      name: config.name || 'LLM Content Filter',
      llm_model_name: config.llm_model_name || 'gpt-4o-mini',
      instruction: config.instruction || '',
      temperature: config.temperature || 0.0,
      chunk_token_threshold: config.chunk_token_threshold || 500,
      enabled: true,
      max_retries: 3,
      timeout_seconds: 30,
      verbose: false,
    };
  }
  return null;
}
