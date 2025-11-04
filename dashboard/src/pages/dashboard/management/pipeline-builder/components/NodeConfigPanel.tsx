/**
 * Node Configuration Panel
 *
 * Bottom panel that displays simple configuration forms for different node types.
 * Replaces the old multi-step wizard with focused, single-purpose forms.
 */

import { ActionIcon, Group, Paper, Stack, Text } from '@mantine/core';
import { IconChevronDown, IconChevronUp, IconX } from '@tabler/icons-react';
import { useState, useEffect } from 'react';
import { PipelineNode } from '@/api/resources/pipelines';

// Import node-specific configuration components
import { WebsiteSourceConfig } from './node-configs/WebsiteSourceConfig';
import { MultiplePagesConfig } from './node-configs/MultiplePagesConfig';
import { SinglePageConfig } from './node-configs/SinglePageConfig';
import { LocalFilesConfig } from './node-configs/LocalFilesConfig';
import { ConfluenceConfig } from './node-configs/ConfluenceConfig';
import { DomainFilterConfig } from './node-configs/DomainFilterConfig';
import { ContentFilterConfig } from './node-configs/ContentFilterConfig';
import { HtmlExtractorConfig } from './node-configs/HtmlExtractorConfig';
import { MarkdownGeneratorConfig } from './node-configs/MarkdownGeneratorConfig';
import { LlmMarkdownGeneratorConfig } from './node-configs/LlmMarkdownGeneratorConfig';
import { TextSplitterConfig } from './node-configs/TextSplitterConfig';
import { EmbeddingGeneratorConfig } from './node-configs/EmbeddingGeneratorConfig';
import { VectorDatabaseConfig } from './node-configs/VectorDatabaseConfig';
import { FileExportConfig } from './node-configs/FileExportConfig';

interface NodeConfigPanelProps {
  node: PipelineNode | null;
  opened: boolean;
  onClose: () => void;
  onSave: (nodeId: string, config: any) => void;
}

export function NodeConfigPanel({ node, opened, onClose, onSave }: NodeConfigPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  // Auto-expand panel when a new node is selected for editing or when panel is opened
  useEffect(() => {
    if (opened && node) {
      setIsExpanded(true);
    }
  }, [node, opened]);

  if (!opened || !node) return null;

  // Get display name for panel title
  const getNodeDisplayName = (type: string): string => {
    const displayNames: Record<string, string> = {
      website: 'Website Source',
      multiple_pages: 'Multiple Pages Source',
      single_page: 'Single Page Source',
      local_files: 'Local Files Source',
      confluence: 'Confluence Source',
      domainFilter: 'Domain Filter',
      contentFilter: 'Content Filter',
      htmlExtractor: 'HTML Extractor',
      markdownGenerator: 'Markdown Generator',
      llmMarkdownGenerator: 'LLM Markdown Generator',
      textSplitter: 'Text Splitter',
      embeddingGenerator: 'Embedding Generator',
      vectorDatabase: 'Vector Database',
      fileExport: 'File Export',
    };
    return displayNames[type] || type;
  };

  // Render appropriate configuration form based on node type
  const renderNodeConfig = () => {
    switch (node.type) {
      // Data Sources
      case 'website':
        return <WebsiteSourceConfig node={node} onSave={onSave} onClose={onClose} />;

      case 'multiple_pages':
        return <MultiplePagesConfig node={node} onSave={onSave} onClose={onClose} />;

      case 'single_page':
        return <SinglePageConfig node={node} onSave={onSave} onClose={onClose} />;

      case 'local_files':
        return <LocalFilesConfig node={node} onSave={onSave} onClose={onClose} />;

      case 'confluence':
        return <ConfluenceConfig node={node} onSave={onSave} onClose={onClose} />;

      // Filters & Transforms
      case 'domainFilter':
        return <DomainFilterConfig node={node} onSave={onSave} onClose={onClose} />;

      case 'contentFilter':
        return <ContentFilterConfig node={node} onSave={onSave} onClose={onClose} />;

      // Output Formats
      case 'htmlExtractor':
        return <HtmlExtractorConfig node={node} onSave={onSave} onClose={onClose} />;

      case 'markdownGenerator':
        return <MarkdownGeneratorConfig node={node} onSave={onSave} onClose={onClose} />;

      case 'llmMarkdownGenerator':
        return <LlmMarkdownGeneratorConfig node={node} onSave={onSave} onClose={onClose} />;

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
            <Text>Configuration for "{node.type}" is coming soon!</Text>
          </div>
        );
    }
  };

  return (
    <Paper
      shadow="xl"
      radius="md"
      style={{
        position: 'absolute',
        top: '0',
        right: '0',
        height: '100%',
        zIndex: 100,
        width: isExpanded ? '420px' : '50px',
        maxWidth: '90vw',
        overflow: 'hidden',
        border: '2px solid #45c9bb',
        borderRight: 'none',
        borderTopRightRadius: '0',
        borderBottomRightRadius: '0',
        backgroundColor: '#f8fffe',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.3s ease',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '8px 12px',
          borderBottom: isExpanded ? '1px solid #45c9bb' : 'none',
          backgroundColor: '#f8fffe',
          cursor: 'pointer',
          minHeight: '44px',
          display: 'flex',
          alignItems: 'center',
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? (
          <Group justify="space-between" style={{ width: '100%' }} gap="xs">
            <Group gap="xs">
              <ActionIcon
                variant="subtle"
                color="teal"
                size="xs"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsExpanded(!isExpanded);
                }}
              >
                <IconChevronDown size={16} style={{ transform: 'rotate(-90deg)' }} />
              </ActionIcon>
              <Text fw={600} size="sm" c="#45c9bb">
                {getNodeDisplayName(node.type)}
              </Text>
            </Group>
            <ActionIcon
              variant="subtle"
              color="red"
              size="xs"
              onClick={(e) => {
                e.stopPropagation();
                onClose();
              }}
            >
              <IconX size={16} />
            </ActionIcon>
          </Group>
        ) : (
          <ActionIcon
            variant="subtle"
            color="teal"
            size="xs"
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(true);
            }}
          >
            <IconChevronUp size={16} style={{ transform: 'rotate(-90deg)' }} />
          </ActionIcon>
        )}
      </div>

      {/* Content */}
      {isExpanded && (
        <div
          style={{
            flex: 1,
            overflow: 'auto',
            padding: '0',
          }}
        >
          {renderNodeConfig()}
        </div>
      )}
    </Paper>
  );
}
