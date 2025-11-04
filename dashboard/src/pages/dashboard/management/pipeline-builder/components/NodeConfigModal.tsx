/**
 * Node Configuration Modal
 *
 * Central modal wrapper that displays simple configuration forms for different node types.
 * Each node type shows a focused, 1-3 field form (NO multi-step wizards).
 */

import { Modal } from '@mantine/core';
import { PipelineNode } from '@/api/resources/pipelines';

// Import node-specific configuration components
import { WebsiteSourceConfig } from './node-configs/WebsiteSourceConfig';
import { DomainFilterConfig } from './node-configs/DomainFilterConfig';
import { ContentFilterConfig } from './node-configs/ContentFilterConfig';
import { LlmContentFilterConfig } from './node-configs/LlmContentFilterConfig';
import { OutputFormatConfig } from './node-configs/OutputFormatConfig';
import { TextSplitterConfig } from './node-configs/TextSplitterConfig';
import { EmbeddingGeneratorConfig } from './node-configs/EmbeddingGeneratorConfig';
import { VectorDatabaseConfig } from './node-configs/VectorDatabaseConfig';
import { FileExportConfig } from './node-configs/FileExportConfig';

interface NodeConfigModalProps {
  node: PipelineNode | null;
  opened: boolean;
  onClose: () => void;
  onSave: (nodeId: string, config: any) => void;
}

export function NodeConfigModal({ node, opened, onClose, onSave }: NodeConfigModalProps) {
  if (!node) return null;

  // Get display name for modal title
  const getNodeDisplayName = (type: string): string => {
    const displayNames: Record<string, string> = {
      website: 'Website Source',
      multiple_pages: 'Multiple Pages Source',
      single_page: 'Single Page Source',
      domainFilter: 'Domain Filter',
      contentFilter: 'Content Filter',
      llmContentFilter: 'LLM Content Filter',
      outputFormat: 'Output Format',
      textSplitter: 'Text Splitter',
      embeddingGenerator: 'Embedding Generator',
      vectorDatabase: 'Vector Database',
      fileExport: 'File Export',
    };
    return displayNames[type] || type;
  };

  // Render appropriate configuration wizard based on node type
  const renderNodeConfig = () => {
    switch (node.type) {
      // Data Sources
      case 'website':
      case 'multiple_pages':
      case 'single_page':
        return <WebsiteSourceConfig node={node} onSave={onSave} onClose={onClose} />;

      // Filters & Transforms
      case 'domainFilter':
        return <DomainFilterConfig node={node} onSave={onSave} onClose={onClose} />;

      case 'contentFilter':
        return <ContentFilterConfig node={node} onSave={onSave} onClose={onClose} />;

      case 'llmContentFilter':
        return <LlmContentFilterConfig node={node} onSave={onSave} onClose={onClose} />;

      case 'outputFormat':
        return <OutputFormatConfig node={node} onSave={onSave} onClose={onClose} />;

      // Processing
      case 'textSplitter':
        return <TextSplitterConfig node={node} onSave={onSave} onClose={onClose} />;

      // AI Tools
      case 'embeddingGenerator':
        return <EmbeddingGeneratorConfig node={node} onSave={onSave} onClose={onClose} />;

      // Storage/Output
      case 'vectorDatabase':
        return <VectorDatabaseConfig node={node} onSave={onSave} onClose={onClose} />;

      case 'fileExport':
        return <FileExportConfig node={node} onSave={onSave} onClose={onClose} />;

      default:
        return (
          <div style={{ padding: '2rem', textAlign: 'center' }}>
            <p>Configuration wizard for "{node.type}" is coming soon!</p>
            <p style={{ marginTop: '1rem', color: '#666' }}>
              This node type doesn't have a configuration wizard yet.
            </p>
          </div>
        );
    }
  };

  return (
    <Modal
      key={node.id}  // Force re-render when node changes
      opened={opened}
      onClose={onClose}
      size="xl"
      title={`Configure: ${getNodeDisplayName(node.type)}`}
      padding={0}
      styles={{
        title: {
          fontWeight: 600,
          fontSize: '1.25rem',
        },
        body: {
          padding: 0,
        },
      }}
    >
      {renderNodeConfig()}
    </Modal>
  );
}
