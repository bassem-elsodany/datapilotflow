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
        <Title order={2} ta="center">🚀 Core Capabilities</Title>

        <Grid gutter="md">
          {/* Knowledge Source Management */}
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="blue">
                  <IconFileText size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Knowledge Sources</Text>
                  <Badge color="blue" variant="light">Multi-Source</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Ingest knowledge from multiple sources including web crawling, local files, and Confluence integration.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ Web Crawling & Scraping</Text>
                <Text size="xs" fw={500}>✓ File Upload (PDF, DOCX, HTML)</Text>
                <Text size="xs" fw={500}>✓ Confluence Integration</Text>
                <Text size="xs" fw={500}>✓ Content Extraction</Text>
              </Stack>
            </Card>
          </Grid.Col>

          {/* Knowledge Jobs & Processing */}
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="orange">
                  <IconSettings size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Knowledge Jobs</Text>
                  <Badge color="orange" variant="light">Automated</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Execute knowledge ingestion jobs with automated processing, chunking, and vector embedding.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ Batch Processing</Text>
                <Text size="xs" fw={500}>✓ Text Chunking</Text>
                <Text size="xs" fw={500}>✓ Vector Embedding</Text>
                <Text size="xs" fw={500}>✓ Job Monitoring</Text>
              </Stack>
            </Card>
          </Grid.Col>

          {/* Agents & Conversations */}
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="green">
                  <IconMessageCircle size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Agents & Conversations</Text>
                  <Badge color="green" variant="light">RAG-Powered</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Create intelligent agents and have context-aware conversations backed by your knowledge base.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ Agent Management</Text>
                <Text size="xs" fw={500}>✓ RAG Conversations</Text>
                <Text size="xs" fw={500}>✓ Semantic Search</Text>
                <Text size="xs" fw={500}>✓ Conversation History</Text>
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
                  <Badge color="red" variant="light">Multi-Provider</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Configure and manage multiple LLM providers for embeddings, chat completions, and AI workflows.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ OpenAI, Claude, & More</Text>
                <Text size="xs" fw={500}>✓ Embedding Models</Text>
                <Text size="xs" fw={500}>✓ Local Model Support</Text>
                <Text size="xs" fw={500}>✓ Provider Management</Text>
              </Stack>
            </Card>
          </Grid.Col>

          {/* System Management */}
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="purple">
                  <IconChartBar size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">System Management</Text>
                  <Badge color="purple" variant="light">Admin</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Manage users, roles, tools, and system configuration for enterprise RAG deployments.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ User & Role Management</Text>
                <Text size="xs" fw={500}>✓ Knowledge Status Monitoring</Text>
                <Text size="xs" fw={500}>✓ Vector Database Status</Text>
                <Text size="xs" fw={500}>✓ Tool Management</Text>
              </Stack>
            </Card>
          </Grid.Col>

          {/* Knowledge Base Analytics */}
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="indigo">
                  <IconTarget size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Knowledge Analytics</Text>
                  <Badge color="indigo" variant="light">Monitoring</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Monitor knowledge base health, vector storage metrics, and ingestion performance.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ Knowledge Status</Text>
                <Text size="xs" fw={500}>✓ Vector DB Metrics</Text>
                <Text size="xs" fw={500}>✓ Ingestion Monitoring</Text>
                <Text size="xs" fw={500}>✓ Performance Analytics</Text>
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
                    <IconFileText size={20} />
                  </ThemeIcon>
                  <Text fw={600}>1. Add Knowledge Sources</Text>
                </Group>
                <Text size="sm" c="dimmed">
                  Configure knowledge sources from web URLs, Confluence spaces, or upload local files (PDF, DOCX, etc.).
                </Text>
              </Stack>
            </Card>
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
              <Stack gap="md" h="100%" justify="space-between">
                <Group mb="md">
                  <ThemeIcon size="lg" variant="light" color="orange">
                    <IconSettings size={20} />
                  </ThemeIcon>
                  <Text fw={600}>2. Create & Run Jobs</Text>
                </Group>
                <Text size="sm" c="dimmed">
                  Execute knowledge ingestion jobs to process, chunk, and embed your content into the vector database.
                </Text>
              </Stack>
            </Card>
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
              <Stack gap="md" h="100%" justify="space-between">
                <Group mb="md">
                  <ThemeIcon size="lg" variant="light" color="green">
                    <IconMessageCircle size={20} />
                  </ThemeIcon>
                  <Text fw={600}>3. Chat with Agents</Text>
                </Group>
                <Text size="sm" c="dimmed">
                  Create agents and have intelligent conversations powered by your knowledge base with RAG capabilities.
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
            onClick={() => navigate(paths.dashboard.management.knowledgeSources.configs)}
          >
            Manage Knowledge Sources
          </Button>
          <Button
            leftSection={<IconMessageCircle size={16} />}
            size="lg"
            variant="light"
            onClick={() => navigate(paths.dashboard.apps.conversations)}
          >
            Start Conversations
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
