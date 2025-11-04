/**
 * Pipeline Builder Toolbox
 * 
 * Categorized toolbox for drag-and-drop pipeline components.
 * Provides tools organized by category for building visual pipelines.
 */

import { useState } from 'react';
import { 
  Paper, 
  Title, 
  Stack, 
  Group, 
  Text, 
  TextInput,
  Collapse,
  UnstyledButton
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconChevronRight,
  IconWorldWww,
  IconFileUpload,
  IconList,
  IconApi,
  IconFolder,
  IconFileText,
  IconScan,
  IconTable,
  IconLink,
  IconTag,
  IconCut,
  IconEraser,
  IconFilter,
  IconChartBar,
  IconTransform,
  IconBrain,
  IconMessageDots,
  IconCategory,
  IconSparkles,
  IconLanguage,
  IconDatabase,
  IconFileExport,
  IconReportAnalytics,
  IconBell,
  IconChartLine,
  IconArrowsSplit,
  IconGitMerge,
  IconHelp,
  IconRepeat,
  IconClock,
  IconSearch,
  IconRobot,
  IconFileText as IconTextFile,
  IconMicrophone,
  IconPalette,
  IconCode
} from '@tabler/icons-react';
import { SiConfluence } from "react-icons/si";
import { GrDocumentText } from "react-icons/gr";
import { BsCardList } from "react-icons/bs";

interface ToolboxProps {
  onAddNode: (nodeType: string, position: { x: number; y: number }) => void;
}

interface ToolCategory {
  name: string;
  icon: React.ReactNode;
  tools: { type: string; label: string; icon: React.ReactNode }[];
}

const toolCategories: ToolCategory[] = [
  {
    name: 'DATA SOURCES',
    icon: <IconFolder size={16} />,
    tools: [
      { type: 'website', label: 'Website Crawling', icon: <IconWorldWww size={16} /> },
      { type: 'multiple_pages', label: 'Links File', icon: <BsCardList size={16} /> },
      { type: 'single_page', label: 'Single Page', icon: <GrDocumentText size={16} /> },
      { type: 'local_files', label: 'Local Files', icon: <IconFileUpload size={16} /> },
    ],
  },
  {
    name: 'FILTERS & TRANSFORMS',
    icon: <IconFilter size={16} />,
    tools: [
      { type: 'domainFilter', label: 'Domain Filter', icon: <IconFilter size={16} /> },
      { type: 'contentFilter', label: 'Content Filter', icon: <IconTag size={16} /> },
      { type: 'llmContentFilter', label: 'LLM Content Filter', icon: <IconBrain size={16} /> },
    ],
  },
  {
    name: 'OUTPUT FORMATS',
    icon: <IconTransform size={16} />,
    tools: [
      { type: 'outputFormat', label: 'Output Format Selector', icon: <IconFileText size={16} /> },
      { type: 'htmlExtractor', label: 'HTML Extractor', icon: <IconCode size={16} /> },
      { type: 'markdownGenerator', label: 'Markdown Generator', icon: <IconFileText size={16} /> },
      { type: 'llmMarkdownGenerator', label: 'LLM Markdown Generator', icon: <IconSparkles size={16} /> },
    ],
  },
  {
    name: 'PROCESSING',
    icon: <IconCut size={16} />,
    tools: [
      { type: 'textSplitter', label: 'Document Splitter', icon: <IconCut size={16} /> },
    ],
  },
  {
    name: 'AI & EMBEDDINGS',
    icon: <IconBrain size={16} />,
    tools: [
      { type: 'embeddingGenerator', label: 'Embedding Generator', icon: <IconBrain size={16} /> },
    ],
  },
  {
    name: 'STORAGE & OUTPUT',
    icon: <IconDatabase size={16} />,
    tools: [
      { type: 'vectorDatabase', label: 'Vector Database', icon: <IconDatabase size={16} /> },
      { type: 'fileExport', label: 'File Export', icon: <IconFileExport size={16} /> },
    ],
  },
];

export function Toolbox({ onAddNode }: ToolboxProps) {
  const [openedCategories, setOpenedCategories] = useState<Record<string, boolean>>({
    'DATA SOURCES': true,
    'FILTERS & TRANSFORMS': true,
    'OUTPUT FORMATS': true,
    'PROCESSING': true,
    'AI & EMBEDDINGS': true,
    'STORAGE & OUTPUT': true,
  });
  const [searchQuery, setSearchQuery] = useState('');

  const toggleCategory = (categoryName: string) => {
    setOpenedCategories(prev => ({
      ...prev,
      [categoryName]: !prev[categoryName]
    }));
  };

  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const filteredCategories = toolCategories.map(category => ({
    ...category,
    tools: category.tools.filter(tool => 
      tool.label.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(category => category.tools.length > 0);

  return (
    <Stack gap="xs">
      <Title order={4}>Toolbox</Title>
      
      <Text size="xs" c="dimmed" style={{ fontStyle: 'italic' }}>
        💡 Drag tools to canvas or click to add. You can add multiple tools!
      </Text>
      
      <TextInput
        placeholder="Search tools..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.currentTarget.value)}
        leftSection={<IconSearch size={16} />}
        size="sm"
      />

      {filteredCategories.map((category) => (
        <Paper key={category.name} withBorder p="xs" radius="md">
          <UnstyledButton onClick={() => toggleCategory(category.name)} style={{ width: '100%' }}>
            <Group justify="space-between">
              <Group>
                {category.icon}
                <Text fw={700} size="sm">{category.name}</Text>
              </Group>
              <IconChevronRight 
                size={16} 
                style={{
                  transform: openedCategories[category.name] ? 'rotate(90deg)' : 'rotate(0deg)',
                }} 
              />
            </Group>
          </UnstyledButton>
          
          <Collapse in={openedCategories[category.name]}>
            <Stack gap={4} mt="xs">
              {category.tools.map((tool) => (
                <Paper
                  key={tool.type}
                  p={6}
                  withBorder
                  style={{ 
                    cursor: 'grab',
                    transition: 'all 0.2s ease',
                    ':hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
                    }
                  }}
                  draggable
                  onDragStart={(event) => onDragStart(event, tool.type)}
                  onClick={() => {
                    // Calculate a better position - center of typical canvas view
                    const centerX = 400;
                    const centerY = 300;
                    onAddNode(tool.type, { x: centerX, y: centerY });
                  }}
                  title={`Drag to canvas or click to add ${tool.label}`}
                >
                  <Group gap="xs">
                    {tool.icon}
                    <Text size="sm">{tool.label}</Text>
                  </Group>
                </Paper>
              ))}
            </Stack>
          </Collapse>
        </Paper>
      ))}
    </Stack>
  );
}