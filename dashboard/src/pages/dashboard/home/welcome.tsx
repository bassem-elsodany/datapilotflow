import { paths } from '@/routes/paths';
import {
  Badge,
  Button,
  Card,
  Divider,
  Grid,
  Group,
  Stack,
  Text,
  ThemeIcon,
  Title
} from '@mantine/core';
import {
  IconBrain,
  IconChartBar,
  IconFileText,
  IconMessageCircle,
  IconRocket,
  IconSettings,
  IconTarget
} from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import classes from './welcome.module.css';

export function Welcome() {
  const navigate = useNavigate();

  return (
    <Stack gap="xl" mt={50}>
      {/* Hero Section */}
      <Stack align="center" gap="md">
        <Title className={classes.title} ta="center">
          Welcome to{' '}
          <Text inherit variant="gradient" component="span" gradient={{ from: 'blue', to: 'cyan' }}>
            DataPilotFlow
          </Text>
        </Title>
        <Text c="dimmed" ta="center" size="xl" maw={800} mx="auto">
          AI-Powered RAG Management & Knowledge System
        </Text>
        <Text c="dimmed" ta="center" size="lg" maw={600} mx="auto">
          Build, manage, and query sophisticated RAG knowledge bases with advanced AI workflows.
          From document ingestion to intelligent conversations - all in one platform.
        </Text>
      </Stack>

      <Divider />

      {/* Core Features Overview */}
      <Stack gap="lg">
        <Title order={2} ta="center">🚀 Core Features</Title>

        <Grid gutter="md">
          {/* Interview Process removed - focusing on knowledge management */}

          {/* Knowledge Conversations */}
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="green">
                  <IconMessageCircle size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Knowledge Conversations</Text>
                  <Badge color="green" variant="light">RAG System</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Advanced RAG (Retrieval-Augmented Generation) system with semantic search,
                context-aware conversations, and intelligent knowledge retrieval.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ Semantic Search</Text>
                <Text size="xs" fw={500}>✓ Context-Aware Chat</Text>
                <Text size="xs" fw={500}>✓ Knowledge Retrieval</Text>
                <Text size="xs" fw={500}>✓ Conversation History</Text>
              </Stack>
            </Card>
          </Grid.Col>

          {/* Document Processing */}
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="orange">
                  <IconFileText size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Document Processing</Text>
                  <Badge color="orange" variant="light">Intelligent</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Intelligent document processing with web crawling, text extraction,
                chunking, and vector storage for comprehensive knowledge base building.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ Web Crawling</Text>
                <Text size="xs" fw={500}>✓ Document Processing</Text>
                <Text size="xs" fw={500}>✓ Vector Storage</Text>
                <Text size="xs" fw={500}>✓ Content Extraction</Text>
              </Stack>
            </Card>
          </Grid.Col>

          {/* Pipeline Builder */}
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="purple">
                  <IconSettings size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Pipeline Builder</Text>
                  <Badge color="purple" variant="light">Visual</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Visual pipeline builder for creating data processing workflows with drag-and-drop
                nodes for crawling, extraction, chunking, and vector storage.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ Visual Workflow Design</Text>
                <Text size="xs" fw={500}>✓ Drag & Drop Interface</Text>
                <Text size="xs" fw={500}>✓ Real-time Execution</Text>
                <Text size="xs" fw={500}>✓ Pipeline Monitoring</Text>
              </Stack>
            </Card>
          </Grid.Col>


          {/* Model Providers */}
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="red">
                  <IconBrain size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Model Providers</Text>
                  <Badge color="red" variant="light">AI-Powered</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Configure and manage multiple LLM providers including OpenAI, Anthropic, and local models
                for embeddings, chat completions, and content generation.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ Multi-Provider Support</Text>
                <Text size="xs" fw={500}>✓ OpenAI & Anthropic</Text>
                <Text size="xs" fw={500}>✓ Local Model Support</Text>
                <Text size="xs" fw={500}>✓ Embedding Models</Text>
              </Stack>
            </Card>
          </Grid.Col>

          {/* Query Enhancement */}
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="indigo">
                  <IconTarget size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Query Enhancement</Text>
                  <Badge color="indigo" variant="light">Advanced</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Advanced query enhancement strategies including HyDE, Decomposition,
                Multi-Query, and Augmented for improved retrieval accuracy.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ Hypothetical Document Embeddings</Text>
                <Text size="xs" fw={500}>✓ Query Decomposition</Text>
                <Text size="xs" fw={500}>✓ Multi-Query Variants</Text>
              </Stack>
            </Card>
          </Grid.Col>

          {/* Vector Storage & Search */}
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="violet">
                  <IconChartBar size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Vector Storage & Search</Text>
                  <Badge color="violet" variant="light">Scalable</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                High-performance vector storage with Milvus integration, semantic search,
                and real-time document retrieval with configurable similarity metrics.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ Milvus Vector Database</Text>
                <Text size="xs" fw={500}>✓ Semantic Search</Text>
                <Text size="xs" fw={500}>✓ Real-time Retrieval</Text>
                <Text size="xs" fw={500}>✓ Configurable Similarity</Text>
              </Stack>
            </Card>
          </Grid.Col>
        </Grid>
      </Stack>

      <Divider />

      {/* Getting Started */}
      <Stack gap="lg" align="center">
        <Title order={2} ta="center">🚀 Getting Started</Title>

        <Text c="dimmed" ta="center" size="lg" maw={600} mx="auto">
          Ready to build your RAG knowledge base? Here's how to get started:
        </Text>

        <Grid gutter="md" w="100%" maw={900} mx="auto">
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
              <Stack gap="md" h="100%" justify="space-between">
                <Group mb="md">
                  <ThemeIcon size="lg" variant="light" color="blue">
                    <IconSettings size={20} />
                  </ThemeIcon>
                  <Text fw={600}>1. Configure Sources</Text>
                </Group>
                <Text size="sm" c="dimmed">
                  Set up knowledge source configurations for web crawling, document processing, and data ingestion.
                </Text>
              </Stack>
            </Card>
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
              <Stack gap="md" h="100%" justify="space-between">
                <Group mb="md">
                  <ThemeIcon size="lg" variant="light" color="green">
                    <IconFileText size={20} />
                  </ThemeIcon>
                  <Text fw={600}>2. Process Data</Text>
                </Group>
                <Text size="sm" c="dimmed">
                  Create and execute knowledge jobs to process your sources into searchable chunks and embeddings.
                </Text>
              </Stack>
            </Card>
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
              <Stack gap="md" h="100%" justify="space-between">
                <Group mb="md">
                  <ThemeIcon size="lg" variant="light" color="orange">
                    <IconMessageCircle size={20} />
                  </ThemeIcon>
                  <Text fw={600}>3. Start Conversations</Text>
                </Group>
                <Text size="sm" c="dimmed">
                  Query your knowledge base through intelligent conversations with advanced RAG capabilities.
                </Text>
              </Stack>
            </Card>
          </Grid.Col>
        </Grid>

        <Group justify="center" mt="lg">
          <Button
            leftSection={<IconRocket size={16} />}
            size="lg"
            variant="gradient"
            gradient={{ from: 'blue', to: 'cyan' }}
            onClick={() => navigate(paths.dashboard.management.knowledgeSources.configCreate)}
          >
            Start Building Your RAG System
          </Button>
          <Button
            leftSection={<IconSettings size={16} />}
            size="lg"
            variant="light"
            onClick={() => navigate(paths.dashboard.apps.agents)}
          >
            Explore Knowledge Search
          </Button>
        </Group>
      </Stack>

      <Divider />

      {/* Footer */}
      <Stack gap="xs" align="center">
        <Text size="sm" c="dimmed" ta="center">
          Built with ❤️ for RAG system builders and knowledge management
        </Text>
        <Text size="xs" c="dimmed" ta="center">
          DataPilotFlow - AI-Powered RAG Management & Knowledge System
        </Text>
      </Stack>
    </Stack>
  );
}
