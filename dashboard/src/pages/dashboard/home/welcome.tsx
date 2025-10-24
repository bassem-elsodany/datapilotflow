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
  IconSearch,
  IconSettings,
  IconTarget,
  IconUsers
} from '@tabler/icons-react';
import classes from './welcome.module.css';

export function Welcome() {
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
          Upload documents, configure RAG injections, and have intelligent conversations with your knowledge sources.
          Build and manage comprehensive RAG systems with advanced AI workflows.
        </Text>
      </Stack>

      <Divider />

      {/* Core Features Overview */}
      <Stack gap="lg">
        <Title order={2} ta="center">🚀 Core Features</Title>

        <Grid gutter="md">
          {/* Interview Process removed - focusing on knowledge management */}

          {/* Knowledge Management */}
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="green">
                  <IconSearch size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Knowledge Conversations</Text>
                  <Badge color="green" variant="light">RAG System</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Advanced RAG (Retrieval-Augmented Generation) system with semantic search,
                context-aware conversations, and knowledge graph integration.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ Semantic Search</Text>
                <Text size="xs" fw={500}>✓ Context-Aware Chat</Text>
                <Text size="xs" fw={500}>✓ Knowledge Graph</Text>
                <Text size="xs" fw={500}>✓ Conversation History</Text>
              </Stack>
            </Card>
          </Grid.Col>

          {/* Document Management */}
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="orange">
                  <IconFileText size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Document Ingest</Text>
                  <Badge color="orange" variant="light">Processing</Badge>
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
                <Text size="xs" fw={500}>✓ Metadata Extraction</Text>
              </Stack>
            </Card>
          </Grid.Col>

          {/* Analytics & Insights */}
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="purple">
                  <IconChartBar size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Skills Analytics</Text>
                  <Badge color="purple" variant="light">Analytics</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Comprehensive analytics dashboard with skills overview, performance trends,
                coverage reports, and gap analysis for data-driven hiring decisions.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ Skills Overview</Text>
                <Text size="xs" fw={500}>✓ Performance Trends</Text>
                <Text size="xs" fw={500}>✓ Coverage Reports</Text>
                <Text size="xs" fw={500}>✓ Gap Analysis</Text>
              </Stack>
            </Card>
          </Grid.Col>

          {/* Interview Data section removed - focusing on knowledge management */}

          {/* Smart Features */}
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="red">
                  <IconTarget size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Smart Features</Text>
                  <Badge color="red" variant="light">AI-Powered</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Advanced AI features including query enhancement, document retrieval,
                intelligent recommendations, and adaptive knowledge strategies.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ Custom Questions</Text>
                <Text size="xs" fw={500}>✓ Time-Aware Selection</Text>
                <Text size="xs" fw={500}>✓ Smart Recommendations</Text>
                <Text size="xs" fw={500}>✓ Adaptive Strategies</Text>
                <Text size="xs" fw={500}>✓ Project-Based Experience</Text>
                <Text size="xs" fw={500}>✓ Role-Specific Questions</Text>
              </Stack>
            </Card>
          </Grid.Col>
        </Grid>
      </Stack>

      <Divider />

      {/* Enhanced Features */}
      <Stack gap="lg">
        <Title order={2} ta="center">🎯 Enhanced Analysis Features</Title>

        <Grid gutter="md">
          <Grid.Col span={{ base: 12, md: 6 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="indigo">
                  <IconTarget size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Dual Experience Analysis</Text>
                  <Badge color="indigo" variant="light">Enhanced</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Distinguish between stated experience and calculated experience from project dates.
                Provides more accurate assessment and transparency in candidate evaluation.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ Stated vs Calculated Experience</Text>
                <Text size="xs" fw={500}>✓ Project Date Analysis</Text>
                <Text size="xs" fw={500}>✓ Overlap Detection</Text>
                <Text size="xs" fw={500}>✓ Smart Experience Selection</Text>
              </Stack>
            </Card>
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 6 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="violet">
                  <IconBrain size={24} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="lg">Project Role Extraction</Text>
                  <Badge color="violet" variant="light">Advanced</Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                Extract detailed project information including roles, locations, assignment types,
                responsibilities, contributions, challenges, and measurable outcomes.
              </Text>
              <Stack gap="xs">
                <Text size="xs" fw={500}>✓ Role-Specific Analysis</Text>
                <Text size="xs" fw={500}>✓ Location & Assignment Type</Text>
                <Text size="xs" fw={500}>✓ Responsibilities & Contributions</Text>
                <Text size="xs" fw={500}>✓ Challenges & Outcomes</Text>
              </Stack>
            </Card>
          </Grid.Col>
        </Grid>
      </Stack>

      <Divider />

      {/* Technology Stack */}
      <Stack gap="lg">
        <Title order={2} ta="center">🛠️ Technology Stack</Title>

        <Grid gutter="md">
          <Grid.Col span={{ base: 12, md: 6 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Text fw={600} size="lg" mb="md">Backend & AI</Text>
              <Stack gap="xs">
                <Group>
                  <Badge color="blue" variant="light">FastAPI</Badge>
                  <Text size="sm">High-performance API framework</Text>
                </Group>
                <Group>
                  <Badge color="green" variant="light">LangGraph</Badge>
                  <Text size="sm">AI workflow orchestration</Text>
                </Group>
                <Group>
                  <Badge color="purple" variant="light">Weaviate</Badge>
                  <Text size="sm">Vector database & semantic search</Text>
                </Group>
                <Group>
                  <Badge color="orange" variant="light">MongoDB</Badge>
                  <Text size="sm">Document storage & session data</Text>
                </Group>
                <Group>
                  <Badge color="red" variant="light">LLMs</Badge>
                  <Text size="sm">OpenAI, Anthropic, Local models</Text>
                </Group>
              </Stack>
            </Card>
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 6 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Text fw={600} size="lg" mb="md">Frontend & UI</Text>
              <Stack gap="xs">
                <Group>
                  <Badge color="blue" variant="light">React</Badge>
                  <Text size="sm">Modern UI framework</Text>
                </Group>
                <Group>
                  <Badge color="cyan" variant="light">Mantine UI</Badge>
                  <Text size="sm">Component library & theming</Text>
                </Group>
                <Group>
                  <Badge color="grape" variant="light">TypeScript</Badge>
                  <Text size="sm">Type-safe development</Text>
                </Group>
                <Group>
                  <Badge color="yellow" variant="light">Vite</Badge>
                  <Text size="sm">Fast build tool</Text>
                </Group>
                <Group>
                  <Badge color="lime" variant="light">React Query</Badge>
                  <Text size="sm">State management & caching</Text>
                </Group>
              </Stack>
            </Card>
          </Grid.Col>
        </Grid>
      </Stack>

      <Divider />

      {/* Getting Started */}
      <Stack gap="lg" align="center">
        <Title order={2} ta="center">🚀 Getting Started</Title>

        <Text c="dimmed" ta="center" size="lg" maw={600}>
          Ready to build your RAG system? Here's how to get started:
        </Text>

        <Grid gutter="md" w="100%" maw={800}>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="blue">
                  <IconFileText size={20} />
                </ThemeIcon>
                <Text fw={600}>1. Ingest Knowledge</Text>
              </Group>
              <Text size="sm" c="dimmed">
                Start by uploading documents or crawling websites to build your knowledge base.
              </Text>
            </Card>
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="green">
                  <IconMessageCircle size={20} />
                </ThemeIcon>
                <Text fw={600}>2. Start Conversations</Text>
              </Group>
              <Text size="sm" c="dimmed">
                Explore your knowledge base through intelligent conversations and semantic search.
              </Text>
            </Card>
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group mb="md">
                <ThemeIcon size="lg" variant="light" color="orange">
                  <IconUsers size={20} />
                </ThemeIcon>
                <Text fw={600}>3. Configure RAG</Text>
              </Group>
              <Text size="sm" c="dimmed">
                Configure RAG systems and start intelligent conversations with your knowledge base.
              </Text>
            </Card>
          </Grid.Col>
        </Grid>

        <Group mt="md">
          <Button
            leftSection={<IconRocket size={16} />}
            size="lg"
            variant="gradient"
            gradient={{ from: 'blue', to: 'cyan' }}
          >
            Start Your First RAG System
          </Button>
          <Button
            leftSection={<IconSettings size={16} />}
            size="lg"
            variant="light"
          >
            Explore Features
          </Button>
        </Group>
      </Stack>

      <Divider />

      {/* Footer */}
      <Stack gap="xs" align="center">
        <Text size="sm" c="dimmed" ta="center">
          Built with ❤️ for knowledge management and RAG system builders
        </Text>
        <Text size="xs" c="dimmed" ta="center">
          dataPilotFlow - AI-Powered RAG Management & Knowledge System
        </Text>
      </Stack>
    </Stack>
  );
}
