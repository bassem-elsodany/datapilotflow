/**
 * Pipeline Node Component
 * 
 * Custom node component for the React Flow canvas.
 * Represents individual pipeline steps with status indicators.
 */

import React, { memo, useState } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Text, ActionIcon, Tooltip } from '@mantine/core';
import { 
  IconSettings, 
  IconTrash, 
  IconPlayerPlay, 
  IconCheck, 
  IconX, 
  IconClock,
  IconWorldWww,
  IconFileUpload,
  IconList,
  IconFileText,
  IconBrain,
  IconDatabase,
  IconScan,
  IconTable,
  IconLink,
  IconTag,
  IconCut,
  IconEraser,
  IconFilter,
  IconChartBar,
  IconTransform,
  IconMessageDots,
  IconCategory,
  IconSparkles,
  IconLanguage,
  IconFileExport,
  IconReportAnalytics,
  IconBell,
  IconChartLine,
  IconHelp,
  IconRepeat,
  IconArrowsSplit,
  IconGitMerge
} from '@tabler/icons-react';
import { SiConfluence } from "react-icons/si";
import { GrDocumentText } from "react-icons/gr";
import { BsCardList } from "react-icons/bs";

interface PipelineNodeData {
  id: string;
  name: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  description?: string;
  configured?: boolean;
  onDelete?: (id: string) => void;
}

interface PipelineNodeProps extends NodeProps<PipelineNodeData> {
}

export const PipelineNode = memo(({ data, selected }: PipelineNodeProps) => {
  const [isHovered, setIsHovered] = useState(false);

  const getStatusIcon = (status: string, configured?: boolean) => {
    // Show green check if node is configured, regardless of status
    if (configured) {
      return <IconCheck size={10} />;
    }
    
    switch (status) {
      case 'running':
        return <IconPlayerPlay size={10} />;
      case 'completed':
        return <IconCheck size={10} />;
      case 'failed':
        return <IconX size={10} />;
      case 'pending':
      default:
        return <IconClock size={10} />;
    }
  };

  const getStatusColor = (status: string, configured?: boolean) => {
    // Show green if node is configured, regardless of status
    if (configured) {
      return '#51cf66';
    }
    
    switch (status) {
      case 'running':
        return '#228be6';
      case 'completed':
        return '#51cf66';
      case 'failed':
        return '#ff6b6b';
      case 'pending':
      default:
        return '#868e96';
    }
  };

  const getNodeIcon = (type: string) => {
    // Return appropriate icon based on node type
    switch (type) {
      case 'website':
        return <IconWorldWww size={14} />;
      case 'multiple_pages':
        return <BsCardList size={14} />;
      case 'single_page':
        return <GrDocumentText size={14} />;
      case 'confluence':
        return <SiConfluence size={14} />;
      case 'textSplitter':
        return <IconCut size={14} />;
      case 'webCrawler':
        return <IconWorldWww size={14} />;
      case 'fileUpload':
        return <IconFileUpload size={14} />;
      case 'textExtractor':
        return <IconFileText size={14} />;
      case 'imageOCR':
        return <IconScan size={14} />;
      case 'tableExtractor':
        return <IconTable size={14} />;
      case 'linkExtractor':
        return <IconLink size={14} />;
      case 'metadataExtractor':
        return <IconTag size={14} />;
      case 'textChunker':
        return <IconCut size={14} />;
      case 'contentCleaner':
        return <IconEraser size={14} />;
      case 'contentFilter':
        return <IconFilter size={14} />;
      case 'contentAnalyzer':
        return <IconChartBar size={14} />;
      case 'contentTransformer':
        return <IconTransform size={14} />;
      case 'embeddingGenerator':
        return <IconBrain size={14} />;
      case 'textSummarizer':
        return <IconMessageDots size={14} />;
      case 'contentClassifier':
        return <IconCategory size={14} />;
      case 'contentEnricher':
        return <IconSparkles size={14} />;
      case 'translation':
        return <IconLanguage size={14} />;
      case 'vectorDatabase':
        return <IconDatabase size={14} />;
      case 'fileExport':
        return <IconFileExport size={14} />;
      case 'reportGenerator':
        return <IconReportAnalytics size={14} />;
      case 'notification':
        return <IconBell size={14} />;
      case 'analytics':
        return <IconChartLine size={14} />;
      case 'conditional':
        return <IconHelp size={14} />;
      case 'loop':
        return <IconRepeat size={14} />;
      case 'splitter':
        return <IconArrowsSplit size={14} />;
      case 'merger':
        return <IconGitMerge size={14} />;
      default:
        return <IconSettings size={14} />;
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        position: 'relative',
        cursor: 'pointer',
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
             {/* Hidden handles for automatic connections only */}
             <Handle 
               type="target" 
               position={Position.Left} 
               id="target"
               style={{ opacity: 0, pointerEvents: 'none' }}
             />
             
             {/* Circular Icon Node */}
             <div style={{ position: 'relative' }}>
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            backgroundColor: selected ? '#e3f2fd' : '#ffffff',
            border: selected ? '2px solid #228be6' : '1px solid #e0e0e0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: selected ? '0 0 4px rgba(34, 139, 230, 0.4)' : '0 1px 2px rgba(0,0,0,0.1)',
            transition: 'all 0.2s ease',
            color: selected ? '#228be6' : '#333',
          }}
        >
          {getNodeIcon(data.type)}
        </div>
        
        {/* Status indicator circle */}
        <div
          style={{
            position: 'absolute',
            top: '-1px',
            right: '-1px',
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            backgroundColor: getStatusColor(data.status, data.configured),
            border: '1px solid #ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {getStatusIcon(data.status, data.configured)}
        </div>

      </div>
      
      {/* Label underneath */}
      <div style={{ marginTop: '4px', textAlign: 'center', maxWidth: '50px' }}>
        <Text 
          size="xs" 
          fw={500} 
          ta="center" 
          style={{ 
            fontSize: '6px',
            lineHeight: 1.0,
            color: selected ? '#228be6' : '#333'
          }}
        >
          {data.name}
        </Text>
        <Text 
          size="xs" 
          c="dimmed" 
          ta="center" 
          style={{ 
            fontSize: '4px',
            lineHeight: 1.0,
            marginTop: '1px'
          }}
        >
          {data.type}
        </Text>
      </div>

        {/* Delete button - show on hover, positioned outside the circle */}
        {isHovered && data.onDelete && (
          <div
            style={{
              position: 'absolute',
              top: '-12px',
              right: '-12px',
              zIndex: 10,
            }}
          >
            <Tooltip label="Delete">
              <ActionIcon 
                size="xs" 
                variant="filled" 
                color="red"
                onClick={(e) => {
                  e.stopPropagation();
                  console.log('Delete clicked for node:', data.id);
                  data.onDelete?.(data.id);
                }}
                style={{ width: 10, height: 10 }}
              >
                <IconTrash size={5} />
              </ActionIcon>
            </Tooltip>
          </div>
        )}
        
        {/* Hidden source handle for automatic connections only */}
        <Handle 
          type="source" 
          position={Position.Right} 
          id="source"
          style={{ opacity: 0, pointerEvents: 'none' }}
        />
    </div>
  );
});