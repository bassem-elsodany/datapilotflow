/**
 * Pipeline Rules and Validation System
 * 
 * Defines rules for valid RAG pipeline construction, including:
 * - Node connection rules
 * - Pipeline flow validation
 * - Required node types and sequences
 */

export interface PipelineRule {
  fromNodeType: string;
  toNodeType: string;
  allowed: boolean;
  reason?: string;
}

export interface NodeRequirements {
  requiredAfter?: string[];
  requiredBefore?: string[];
  maxInstances?: number;
  minInstances?: number;
}

export interface PipelineValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}

// Define valid connections between node types
export const PIPELINE_CONNECTION_RULES: PipelineRule[] = [
  // DATA SOURCES can connect to FILTERS (optional)
  { fromNodeType: 'website', toNodeType: 'domainFilter', allowed: true },
  { fromNodeType: 'website', toNodeType: 'contentFilter', allowed: true },
  { fromNodeType: 'multiple_pages', toNodeType: 'contentFilter', allowed: true },
  { fromNodeType: 'single_page', toNodeType: 'contentFilter', allowed: true },

  // DATA SOURCES can connect to OUTPUT FORMATS (optional)
  { fromNodeType: 'website', toNodeType: 'htmlExtractor', allowed: true },
  { fromNodeType: 'website', toNodeType: 'markdownGenerator', allowed: true },
  { fromNodeType: 'website', toNodeType: 'llmMarkdownGenerator', allowed: true },
  { fromNodeType: 'multiple_pages', toNodeType: 'htmlExtractor', allowed: true },
  { fromNodeType: 'multiple_pages', toNodeType: 'markdownGenerator', allowed: true },
  { fromNodeType: 'multiple_pages', toNodeType: 'llmMarkdownGenerator', allowed: true },
  { fromNodeType: 'single_page', toNodeType: 'htmlExtractor', allowed: true },
  { fromNodeType: 'single_page', toNodeType: 'markdownGenerator', allowed: true },
  { fromNodeType: 'single_page', toNodeType: 'llmMarkdownGenerator', allowed: true },

  // DATA SOURCES can connect directly to PROCESSING TOOLS (filters/formats are optional)
  { fromNodeType: 'website', toNodeType: 'textSplitter', allowed: true },
  { fromNodeType: 'multiple_pages', toNodeType: 'textSplitter', allowed: true },
  { fromNodeType: 'single_page', toNodeType: 'textSplitter', allowed: true },

  // FILTERS can connect to each other (for chaining)
  { fromNodeType: 'domainFilter', toNodeType: 'contentFilter', allowed: true },
  { fromNodeType: 'contentFilter', toNodeType: 'domainFilter', allowed: true },

  // FILTERS can connect to OUTPUT FORMATS
  { fromNodeType: 'domainFilter', toNodeType: 'htmlExtractor', allowed: true },
  { fromNodeType: 'domainFilter', toNodeType: 'markdownGenerator', allowed: true },
  { fromNodeType: 'domainFilter', toNodeType: 'llmMarkdownGenerator', allowed: true },
  { fromNodeType: 'contentFilter', toNodeType: 'htmlExtractor', allowed: true },
  { fromNodeType: 'contentFilter', toNodeType: 'markdownGenerator', allowed: true },
  { fromNodeType: 'contentFilter', toNodeType: 'llmMarkdownGenerator', allowed: true },

  // FILTERS can connect to PROCESSING TOOLS
  { fromNodeType: 'domainFilter', toNodeType: 'textSplitter', allowed: true },
  { fromNodeType: 'contentFilter', toNodeType: 'textSplitter', allowed: true },

  // OUTPUT FORMATS can connect to PROCESSING TOOLS
  { fromNodeType: 'htmlExtractor', toNodeType: 'textSplitter', allowed: true },
  { fromNodeType: 'markdownGenerator', toNodeType: 'textSplitter', allowed: true },
  { fromNodeType: 'llmMarkdownGenerator', toNodeType: 'textSplitter', allowed: true },

  // PROCESSING TOOLS can connect to AI TOOLS
  { fromNodeType: 'textSplitter', toNodeType: 'embeddingGenerator', allowed: true },

  // AI TOOLS can connect to STORAGE & OUTPUT
  { fromNodeType: 'embeddingGenerator', toNodeType: 'vectorDatabase', allowed: true },
  { fromNodeType: 'embeddingGenerator', toNodeType: 'fileExport', allowed: true },
];

// Define node requirements and constraints
export const NODE_REQUIREMENTS: Record<string, NodeRequirements> = {
  // DATA SOURCES
  website: {
    maxInstances: 1,
    requiredAfter: ['textSplitter']
  },
  multiple_pages: {
    maxInstances: 1,
    requiredAfter: ['textSplitter']
  },
  single_page: {
    maxInstances: 1,
    requiredAfter: ['textSplitter']
  },

  // PROCESSING TOOLS
  textSplitter: {
    minInstances: 1,
    requiredBefore: ['website', 'multiple_pages', 'single_page'],
    requiredAfter: ['embeddingGenerator']
  },

  // AI TOOLS
  embeddingGenerator: {
    minInstances: 1,
    requiredBefore: ['textSplitter'],
    requiredAfter: ['vectorDatabase', 'fileExport']
  },

  // STORAGE & OUTPUT
  vectorDatabase: {
    minInstances: 1,
    requiredBefore: ['embeddingGenerator']
  },
  fileExport: {
    requiredBefore: ['embeddingGenerator']
  }
};

// Pipeline flow categories
export const PIPELINE_CATEGORIES = {
  DATA_SOURCES: ['website', 'multiple_pages', 'single_page'],
  FILTERS_TRANSFORMS: ['domainFilter', 'contentFilter'],
  OUTPUT_FORMATS: ['htmlExtractor', 'markdownGenerator', 'llmMarkdownGenerator'],
  PROCESSING_TOOLS: ['textSplitter'],
  AI_TOOLS: ['embeddingGenerator'],
  STORAGE_OUTPUT: ['vectorDatabase', 'fileExport']
};

// Validate a pipeline connection
export function validateConnection(fromNodeType: string, toNodeType: string): boolean {
  const rule = PIPELINE_CONNECTION_RULES.find(
    rule => rule.fromNodeType === fromNodeType && rule.toNodeType === toNodeType
  );
  return rule ? rule.allowed : false;
}

// Get valid target node types for a given source node type
export function getValidTargets(sourceNodeType: string): string[] {
  return PIPELINE_CONNECTION_RULES
    .filter(rule => rule.fromNodeType === sourceNodeType && rule.allowed)
    .map(rule => rule.toNodeType);
}

// Get valid source node types for a given target node type
export function getValidSources(targetNodeType: string): string[] {
  return PIPELINE_CONNECTION_RULES
    .filter(rule => rule.toNodeType === targetNodeType && rule.allowed)
    .map(rule => rule.fromNodeType);
}

// Validate entire pipeline
export function validatePipeline(nodes: any[], edges: any[]): PipelineValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  const suggestions: string[] = [];

  // Check for required data source
  const dataSources = nodes.filter(node => 
    PIPELINE_CATEGORIES.DATA_SOURCES.includes(node.data.type)
  );
  
  if (dataSources.length === 0) {
    errors.push('Pipeline must have at least one data source');
  }

  // Check for required text splitter
  const textSplitters = nodes.filter(node => node.data.type === 'textSplitter');
  if (textSplitters.length === 0) {
    errors.push('Pipeline must have a Document Splitter');
  }

  // Check for required embedding generator
  const embeddingGenerators = nodes.filter(node => node.data.type === 'embeddingGenerator');
  if (embeddingGenerators.length === 0) {
    errors.push('Pipeline must have an Embedding Generator for RAG functionality');
  }

  // Check for required vector database
  const vectorDatabases = nodes.filter(node => node.data.type === 'vectorDatabase');
  if (vectorDatabases.length === 0) {
    errors.push('Pipeline must have a Vector Database for storing embeddings');
  }

  // Validate connections
  edges.forEach(edge => {
    const sourceNode = nodes.find(node => node.id === edge.source);
    const targetNode = nodes.find(node => node.id === edge.target);
    
    if (sourceNode && targetNode) {
      const isValidConnection = validateConnection(sourceNode.data.type, targetNode.data.type);
      if (!isValidConnection) {
        errors.push(`Invalid connection: ${sourceNode.data.type} cannot connect to ${targetNode.data.type}`);
      }
    }
  });

  // Check for orphaned nodes
  const connectedNodeIds = new Set([
    ...edges.map(edge => edge.source),
    ...edges.map(edge => edge.target)
  ]);
  
  const orphanedNodes = nodes.filter(node => !connectedNodeIds.has(node.id));
  if (orphanedNodes.length > 0) {
    warnings.push(`Found ${orphanedNodes.length} disconnected node(s)`);
  }

  // Suggest improvements
  if (dataSources.length > 0 && textSplitters.length === 0) {
    suggestions.push('Add a Document Splitter after your data source');
  }
  
  if (textSplitters.length > 0 && embeddingGenerators.length === 0) {
    suggestions.push('Add an Embedding Generator after the Document Splitter');
  }
  
  if (embeddingGenerators.length > 0 && vectorDatabases.length === 0) {
    suggestions.push('Add a Vector Database to store the embeddings');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    suggestions
  };
}

// Get connection suggestions for a node
export function getConnectionSuggestions(nodeType: string): string[] {
  const validTargets = getValidTargets(nodeType);
  const category = Object.entries(PIPELINE_CATEGORIES).find(([_, types]) =>
    types.includes(nodeType)
  )?.[0];

  if (category === 'DATA_SOURCES') {
    return ['Connect to optional Filters (Domain/Content/Output) or directly to Document Splitter'];
  } else if (category === 'FILTERS_TRANSFORMS') {
    return ['Connect to other Filters for chaining or to Document Splitter'];
  } else if (category === 'PROCESSING_TOOLS') {
    return ['Connect to AI Tools like Embedding Generator or Text Summarizer'];
  } else if (category === 'AI_TOOLS') {
    return ['Connect to Storage & Output tools like Vector Database or File Export'];
  } else if (category === 'STORAGE_OUTPUT') {
    return ['Connect to other output tools or Notification for alerts'];
  }

  return validTargets;
}
