import { client } from '@/api/axios';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Card,
  CardSection,
  Grid,
  Group,
  LoadingOverlay,
  Modal,
  MultiSelect,
  NumberInput,
  Pagination,
  Select,
  SimpleGrid,
  Stack,
  Switch,
  Tabs,
  Text,
  TextInput,
  Textarea,
  Title,
  Tooltip
} from '@mantine/core';
import {
  IconBrain,
  IconCalendar,
  IconCategory,
  IconClock,
  IconEdit,
  IconEye,
  IconPlus,
  IconSearch,
  IconTrash
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

interface InterviewQuestion {
  question_id: string;
  domain_id: string;
  domain_name: string;
  question_text: string;
  rationale?: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  answer_criteria: Array<{
    level: number;
    criteria: string;
  }>;
  sample_answers?: Record<string, string>;
  metadata: {
    tags: string[];
    category?: string;
    subcategory?: string;
    estimated_time?: number;
    is_active: boolean;
    version: string;
  };
  source: 'library' | 'custom' | 'generated';
  created_at: string;
  updated_at: string;
}

interface Domain {
  domain_id: string;
  name: string;
  description?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export default function QuestionsPage() {
  const [questions, setQuestions] = useState<InterviewQuestion[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [questionModalOpened, setQuestionModalOpened] = useState(false);
  const [domainModalOpened, setDomainModalOpened] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<InterviewQuestion | null>(null);
  const [editingDomain, setEditingDomain] = useState<Domain | null>(null);

  // Delete confirmation modal state
  const [deleteModalOpened, setDeleteModalOpened] = useState(false);
  const [questionToDelete, setQuestionToDelete] = useState<InterviewQuestion | null>(null);

  // Details modal state
  const [detailsModalOpened, setDetailsModalOpened] = useState(false);
  const [selectedQuestion, setSelectedQuestion] = useState<InterviewQuestion | null>(null);

  // Form states
  const [questionForm, setQuestionForm] = useState({
    question_id: '',
    domain_id: '',
    domain_name: '',
    question_text: '',
    rationale: '',
    difficulty: 'intermediate' as const,
    answer_criteria: [{ level: 1, criteria: '' }, { level: 3, criteria: '' }, { level: 5, criteria: '' }],
    tags: [] as string[],
    category: '',
    subcategory: '',
    estimated_time: 5,
    is_active: true,
    source: 'custom' as const,
  });

  const [domainForm, setDomainForm] = useState({
    domain_id: '',
    name: '',
    description: '',
    tags: [] as string[],
  });

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDomain, setSelectedDomain] = useState<string>('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('');
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [activeTab, setActiveTab] = useState('questions');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const itemsPerPage = 10;

  // Fetch questions and domains using React Query
  const { data: questionsData, isLoading: questionsLoading, refetch: refetchQuestions } = useQuery({
    queryKey: ['questions'],
    queryFn: () => client.get('/management/interview/questions'),
  });

  const { data: domainsData, isLoading: domainsLoading, refetch: refetchDomains } = useQuery({
    queryKey: ['domains'],
    queryFn: () => client.get('/management/interview/domains'),
  });

  // Update local state when data is fetched
  useEffect(() => {
    if (questionsData?.data?.questions) {
      setQuestions(questionsData.data.questions);
    }
  }, [questionsData]);

  useEffect(() => {
    if (domainsData?.data?.domains) {
      setDomains(domainsData.data.domains);
    }
  }, [domainsData]);

  // Set loading state based on React Query loading
  useEffect(() => {
    setLoading(questionsLoading || domainsLoading);
  }, [questionsLoading, domainsLoading]);

  // Filter questions
  const filteredQuestions = questions.filter(question => {
    const matchesSearch = question.question_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      question.domain_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      question.metadata.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase())) ||
      question.rationale?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesDomain = !selectedDomain || question.domain_name === selectedDomain;
    const matchesDifficulty = !selectedDifficulty || question.difficulty === selectedDifficulty;
    const matchesSource = !selectedSource || question.source === selectedSource;
    const matchesStatus = !selectedStatus || question.metadata.is_active === (selectedStatus === 'active');

    return matchesSearch && matchesDomain && matchesDifficulty && matchesSource && matchesStatus;
  });

  // Pagination
  const paginatedQuestions = filteredQuestions.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Update pagination when filters change
  useEffect(() => {
    const newTotalPages = Math.ceil(filteredQuestions.length / itemsPerPage);
    setTotalPages(newTotalPages);
    // Reset to page 1 when filters change, but only if current page is out of bounds
    if (currentPage > newTotalPages && newTotalPages > 0) {
      setCurrentPage(1);
    }
  }, [filteredQuestions, currentPage]);

  // Create new question
  const handleCreateQuestion = async (questionForm: any) => {
    try {
      await client.post('/management/interview/questions', questionForm);
      setQuestionModalOpened(false);
      setQuestionForm({
        question_text: '',
        rationale: '',
        difficulty: 'intermediate' as const,
        domain_name: '',
        source: 'custom' as const,
        answer_criteria: [],
        metadata: {
          tags: [],
          category: '',
          subcategory: '',
          estimated_time: 5,
          is_active: true,
          version: '1.0.0'
        }
      });
      // Refresh data using React Query
      refetchQuestions();
    } catch (error) {
      // Handle error silently or show user notification
    }
  };

  // Update question
  const handleUpdateQuestion = async (questionForm: any) => {
    try {
      await client.put(`/management/interview/questions/${editingQuestion?.question_id}`, questionForm);
      setQuestionModalOpened(false);
      setEditingQuestion(null);
      setQuestionForm({
        question_text: '',
        rationale: '',
        difficulty: 'intermediate' as const,
        domain_name: '',
        source: 'custom' as const,
        answer_criteria: [],
        metadata: {
          tags: [],
          category: '',
          subcategory: '',
          estimated_time: 5,
          is_active: true,
          version: '1.0.0'
        }
      });
      // Refresh data using React Query
      refetchQuestions();
    } catch (error) {
      // Handle error silently or show user notification
    }
  };

  // Show delete confirmation modal
  const showDeleteConfirmation = (question: InterviewQuestion) => {
    setQuestionToDelete(question);
    setDeleteModalOpened(true);
  };

  const showQuestionDetails = (question: InterviewQuestion) => {
    setSelectedQuestion(question);
    setDetailsModalOpened(true);
  };

  // Delete question after confirmation
  const handleDeleteQuestion = async () => {
    if (!questionToDelete) return;

    try {
      await client.delete(`/management/interview/questions/${questionToDelete.question_id}`);
      setDeleteModalOpened(false);
      setQuestionToDelete(null);
      // Refresh data using React Query
      refetchQuestions();
    } catch (error) {
      // Handle error silently or show user notification
    }
  };

  // Domain CRUD operations
  const handleCreateDomain = async (domainForm: any) => {
    try {
      await client.post('/management/interview/domains', domainForm);
      setDomainModalOpened(false);
      setDomainForm({ domain_id: '', name: '', description: '', tags: [] });
      // Refresh data
      refetchDomains();
    } catch (error) {
      // Handle error silently or show user notification
    }
  };

  const handleUpdateDomain = async (domainForm: any) => {
    try {
      if (!editingDomain) return;
      await client.put(`/management/interview/domains/${editingDomain.domain_id}`, domainForm);
      setDomainModalOpened(false);
      setEditingDomain(null);
      setDomainForm({ domain_id: '', name: '', description: '', tags: [] });
      // Refresh data
      refetchDomains();
    } catch (error) {
      // Handle error silently or show user notification
    }
  };

  const handleDeleteDomain = async (domainId: string) => {
    try {
      await client.delete(`/management/interview/domains/${domainId}`);
      // Refresh data
      refetchDomains();
    } catch (error) {
      // Handle error silently or show user notification
    }
  };

  // Form helpers
  const resetQuestionForm = () => {
    setQuestionForm({
      question_id: '',
      domain_id: '',
      domain_name: '',
      question_text: '',
      rationale: '',
      difficulty: 'beginner' as const,
      answer_criteria: [{ level: 1, criteria: '' }, { level: 3, criteria: '' }, { level: 5, criteria: '' }],
      tags: [],
      category: '',
      subcategory: '',
      estimated_time: 5,
      is_active: true,
      source: 'library' as const,
    });
  };

  const resetDomainForm = () => {
    setDomainForm({
      domain_id: '',
      name: '',
      description: '',
      tags: [],
    });
  };

  const openEditQuestion = (question: InterviewQuestion) => {
    setEditingQuestion(question);
    setQuestionForm({
      question_id: question.question_id || '',
      domain_id: question.domain_id || '',
      domain_name: question.domain_name || '',
      question_text: question.question_text || '',
      rationale: question.rationale || '',
      difficulty: question.difficulty || 'intermediate',
      answer_criteria: question.answer_criteria || [{ level: 1, criteria: '' }, { level: 3, criteria: '' }, { level: 5, criteria: '' }],
      tags: question.metadata?.tags || [],
      category: question.metadata?.category || '',
      subcategory: question.metadata?.subcategory || '',
      estimated_time: question.metadata?.estimated_time || 5,
      is_active: question.metadata?.is_active ?? true,
      source: question.source || 'custom',
    });
    setQuestionModalOpened(true);
  };

  const openEditDomain = (domain: Domain) => {
    setEditingDomain(domain);
    setDomainForm({
      domain_id: domain.domain_id || '',
      name: domain.name || '',
      description: domain.description || '',
      tags: domain.tags || [],
    });
    setDomainModalOpened(true);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'green';
      case 'intermediate': return 'blue';
      case 'advanced': return 'orange';
      case 'expert': return 'red';
      default: return 'gray';
    }
  };

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'library': return 'blue';
      case 'custom': return 'green';
      case 'generated': return 'purple';
      default: return 'gray';
    }
  };

  return (
    <Page title="Interview Questions Administration">
      <PageHeader
        title="Interview Questions & Domains"
        breadcrumbs={[
          { label: 'Dashboard', href: paths.dashboard.root },
          { label: 'Management', href: paths.dashboard.management.root },
          { label: 'Interview Data', href: paths.dashboard.management.interviewData.root },
          { label: 'Questions & Domains' },
        ]}
      >
        <Group>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => {
              resetQuestionForm();
              setEditingQuestion(null);
              setQuestionModalOpened(true);
            }}
          >
            Add Question
          </Button>
          <Button
            leftSection={<IconPlus size={16} />}
            variant="light"
            onClick={() => {
              resetDomainForm();
              setEditingDomain(null);
              setDomainModalOpened(true);
            }}
          >
            Add Domain
          </Button>
        </Group>
      </PageHeader>

      {error && (
        <Alert color="red" mb="md" withCloseButton onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'questions')}>
        <Tabs.List>
          <Tabs.Tab value="questions" leftSection={<IconBrain size={16} />}>
            Questions ({questions.length})
          </Tabs.Tab>
          <Tabs.Tab value="domains" leftSection={<IconCategory size={16} />}>
            Domains ({domains.length})
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="questions" pt="md">
          {/* Enhanced Filter Bar */}
          <Card withBorder mb="md">
            <CardSection p="md">
              <Grid gutter="md">
                <Grid.Col span={{ base: 12, md: 4 }}>
                  <TextInput
                    placeholder="Search questions by text, tags, or rationale..."
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.currentTarget.value)}
                    leftSection={<IconSearch size={16} />}
                    description="Search across question text, tags, and rationale"
                  />
                </Grid.Col>
                <Grid.Col span={{ base: 12, md: 2 }}>
                  <Select
                    placeholder="All domains"
                    value={selectedDomain}
                    onChange={setSelectedDomain}
                    data={domains.map(d => ({ value: d.name, label: d.name }))}
                    clearable
                    description="Filter by domain"
                  />
                </Grid.Col>
                <Grid.Col span={{ base: 12, md: 2 }}>
                  <Select
                    placeholder="All difficulties"
                    value={selectedDifficulty}
                    onChange={setSelectedDifficulty}
                    data={[
                      { value: 'beginner', label: '🟢 Beginner' },
                      { value: 'intermediate', label: '🔵 Intermediate' },
                      { value: 'advanced', label: '🟠 Advanced' },
                      { value: 'expert', label: '🔴 Expert' },
                    ]}
                    clearable
                    description="Filter by difficulty"
                  />
                </Grid.Col>
                <Grid.Col span={{ base: 12, md: 2 }}>
                  <Select
                    placeholder="All sources"
                    value={selectedSource}
                    onChange={setSelectedSource}
                    data={[
                      { value: 'library', label: '📚 Library' },
                      { value: 'custom', label: '✏️ Custom' },
                      { value: 'generated', label: '🤖 Generated' },
                    ]}
                    clearable
                    description="Filter by source"
                  />
                </Grid.Col>
                <Grid.Col span={{ base: 12, md: 2 }}>
                  <Select
                    placeholder="All status"
                    value={selectedStatus}
                    onChange={setSelectedStatus}
                    data={[
                      { value: 'active', label: '✅ Active' },
                      { value: 'inactive', label: '❌ Inactive' },
                    ]}
                    clearable
                    description="Filter by status"
                  />
                </Grid.Col>
              </Grid>

              {/* Quick Stats */}
              <Group justify="space-between" mt="md" pt="md" style={{ borderTop: '1px solid var(--mantine-color-gray-3)' }}>
                <Group gap="lg">
                  <Text size="sm" c="dimmed">
                    Showing {paginatedQuestions.length} of {filteredQuestions.length} questions
                  </Text>
                  {selectedDomain && (
                    <Badge variant="light" color="blue">
                      Domain: {selectedDomain}
                    </Badge>
                  )}
                  {selectedDifficulty && (
                    <Badge variant="light" color={getDifficultyColor(selectedDifficulty)}>
                      Difficulty: {selectedDifficulty}
                    </Badge>
                  )}
                </Group>
                <Group gap="xs">
                  <Button
                    variant="light"
                    size="xs"
                    onClick={() => {
                      setSearchQuery('');
                      setSelectedDomain(null);
                      setSelectedDifficulty(null);
                      setSelectedSource(null);
                      setSelectedStatus(null);
                    }}
                  >
                    Clear Filters
                  </Button>
                  <Button
                    leftSection={<IconPlus size={16} />}
                    size="sm"
                    onClick={() => {
                      resetQuestionForm();
                      setEditingQuestion(null);
                      setQuestionModalOpened(true);
                    }}
                  >
                    Create Question
                  </Button>
                </Group>
              </Group>
            </CardSection>
          </Card>

          {/* Enhanced Question List */}
          <Card withBorder>
            <CardSection p="md">
              <LoadingOverlay visible={loading} />

              <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} spacing="lg">
                {paginatedQuestions.map((question) => (
                  <Card
                    key={question.question_id}
                    withBorder
                    p="md"
                    style={{
                      transition: 'all 0.2s ease',
                      cursor: 'pointer',
                      height: 'fit-content',
                      display: 'flex',
                      flexDirection: 'column',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: 'var(--mantine-shadow-md)'
                      }
                    }}
                  >
                    {/* Question Header */}
                    <Group justify="space-between" align="flex-start" mb="sm">
                      <Group gap="xs" wrap="wrap">
                        <Badge
                          color={getDifficultyColor(question.difficulty)}
                          variant="filled"
                          size="xs"
                        >
                          {question.difficulty.toUpperCase()}
                        </Badge>
                        <Badge
                          color={getSourceColor(question.source)}
                          variant="light"
                          size="xs"
                        >
                          {question.source}
                        </Badge>
                      </Group>

                      <Group gap="xs">
                        <Tooltip label="Edit question">
                          <ActionIcon
                            variant="light"
                            size="xs"
                            color="orange"
                            onClick={() => openEditQuestion(question)}
                          >
                            <IconEdit size={14} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="Delete question">
                          <ActionIcon
                            variant="light"
                            color="red"
                            size="xs"
                            onClick={() => showDeleteConfirmation(question)}
                          >
                            <IconTrash size={14} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                    </Group>

                    {/* Question Content */}
                    <Box mb="sm" style={{ flex: 1 }}>
                      <Text
                        fw={600}
                        size="sm"
                        mb="xs"
                        style={{ lineHeight: 1.4 }}
                        lineClamp={3}
                      >
                        {question.question_text}
                      </Text>

                      {question.rationale && (
                        <Text
                          size="xs"
                          c="dimmed"
                          mb="xs"
                          lineClamp={2}
                          style={{
                            fontStyle: 'italic',
                            backgroundColor: 'var(--mantine-color-gray-0)',
                            padding: '6px 8px',
                            borderRadius: '4px',
                            borderLeft: '2px solid var(--mantine-color-blue-5)'
                          }}
                        >
                          💡 {question.rationale}
                        </Text>
                      )}
                    </Box>

                    {/* Domain and Time */}
                    <Group gap="xs" mb="sm" wrap="wrap">
                      <Badge
                        color="blue"
                        variant="light"
                        size="xs"
                        leftSection={<IconCategory size={10} />}
                      >
                        {question.domain_name}
                      </Badge>
                      {question.metadata.estimated_time && (
                        <Badge
                          color="gray"
                          variant="light"
                          size="xs"
                          leftSection={<IconClock size={10} />}
                        >
                          {question.metadata.estimated_time}m
                        </Badge>
                      )}
                      {!question.metadata.is_active && (
                        <Badge color="red" variant="light" size="xs">
                          Inactive
                        </Badge>
                      )}
                    </Group>

                    {/* Tags */}
                    {question.metadata.tags.length > 0 && (
                      <Group gap="xs" wrap="wrap" mb="sm">
                        {question.metadata.tags.slice(0, 3).map((tag) => (
                          <Badge
                            key={tag}
                            size="xs"
                            variant="dot"
                            color="blue"
                          >
                            {tag}
                          </Badge>
                        ))}
                        {question.metadata.tags.length > 3 && (
                          <Badge size="xs" variant="light" color="gray">
                            +{question.metadata.tags.length - 3}
                          </Badge>
                        )}
                      </Group>
                    )}

                    {/* Footer */}
                    <Group justify="space-between" align="center" style={{ marginTop: 'auto' }}>
                      <Text size="xs" c="dimmed">
                        <IconCalendar size={10} style={{ marginRight: 4 }} />
                        {(() => {
                          const date = new Date(question.created_at);
                          return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleDateString();
                        })()}
                      </Text>

                      <Tooltip label="View full details">
                        <ActionIcon
                          variant="light"
                          size="xs"
                          color="blue"
                          onClick={() => {
                            setSelectedQuestion(question);
                            setDetailsModalOpened(true);
                          }}
                        >
                          <IconEye size={12} />
                        </ActionIcon>
                      </Tooltip>
                    </Group>
                  </Card>
                ))}

                {paginatedQuestions.length === 0 && !loading && (
                  <Card withBorder p="xl" style={{ gridColumn: '1 / -1' }}>
                    <Stack align="center" gap="md">
                      <IconBrain size={48} color="var(--mantine-color-gray-4)" />
                      <Text size="lg" fw={500} c="dimmed">
                        No questions found
                      </Text>
                      <Text size="sm" c="dimmed" ta="center">
                        {searchQuery || selectedDomain || selectedDifficulty || selectedSource || selectedStatus
                          ? 'Try adjusting your filters or search terms.'
                          : 'Create your first question to get started with interview preparation.'
                        }
                      </Text>
                      <Button
                        leftSection={<IconPlus size={16} />}
                        onClick={() => {
                          resetQuestionForm();
                          setEditingQuestion(null);
                          setQuestionModalOpened(true);
                        }}
                      >
                        Create First Question
                      </Button>
                    </Stack>
                  </Card>
                )}
              </SimpleGrid>

              {/* Enhanced Pagination */}
              {totalPages > 1 && (
                <Card withBorder mt="md">
                  <Group justify="space-between" p="md">
                    <Text size="sm" c="dimmed">
                      Page {currentPage} of {totalPages} • {filteredQuestions.length} total questions
                    </Text>
                    <Pagination
                      value={currentPage}
                      onChange={setCurrentPage}
                      total={totalPages}
                      size="sm"
                    />
                  </Group>
                </Card>
              )}
            </CardSection>
          </Card>

          {/* Floating Create Button - Context Aware */}
          <ActionIcon
            size="xl"
            radius="xl"
            variant="filled"
            color={activeTab === 'questions' ? 'blue' : 'green'}
            style={{
              position: 'fixed',
              bottom: '2rem',
              right: '2rem',
              zIndex: 1000,
              boxShadow: 'var(--mantine-shadow-lg)',
            }}
            onClick={() => {
              if (activeTab === 'questions') {
                resetQuestionForm();
                setEditingQuestion(null);
                setQuestionModalOpened(true);
              } else {
                resetDomainForm();
                setEditingDomain(null);
                setDomainModalOpened(true);
              }
            }}
          >
            <IconPlus size={24} />
          </ActionIcon>
        </Tabs.Panel>

        <Tabs.Panel value="domains" pt="md">
          {/* Domains Header with Create Button */}
          <Card withBorder mb="md">
            <CardSection p="md">
              <Group justify="space-between" align="center">
                <Box>
                  <Text fw={600} size="lg" mb="xs">
                    Interview Domains
                  </Text>
                  <Text size="sm" c="dimmed">
                    Manage domains and categories for organizing interview questions
                  </Text>
                </Box>
                <Button
                  leftSection={<IconPlus size={16} />}
                  onClick={() => {
                    resetDomainForm();
                    setEditingDomain(null);
                    setDomainModalOpened(true);
                  }}
                >
                  Create Domain
                </Button>
              </Group>
            </CardSection>
          </Card>

          {/* Domains Grid */}
          <Card withBorder>
            <CardSection p="md">
              <LoadingOverlay visible={loading} />

              <SimpleGrid cols={{ base: 1, md: 2, lg: 3 }} spacing="md">
                {domains.map((domain) => (
                  <Card
                    key={domain.domain_id}
                    withBorder
                    p="md"
                    style={{
                      transition: 'all 0.2s ease',
                      cursor: 'pointer',
                      '&:hover': {
                        transform: 'translateY(-1px)',
                        boxShadow: 'var(--mantine-shadow-sm)'
                      }
                    }}
                  >
                    <Group justify="space-between" align="flex-start">
                      <Box style={{ flex: 1 }}>
                        <Group mb="xs">
                          <Badge color="blue" variant="light" size="sm">
                            Domain
                          </Badge>
                          <Badge color="gray" variant="light" size="sm">
                            {domain.tags.length} tags
                          </Badge>
                        </Group>

                        <Text fw={600} size="lg" mb="xs">
                          {domain.name}
                        </Text>

                        {domain.description && (
                          <Text size="sm" c="dimmed" mb="xs" lineClamp={2}>
                            {domain.description}
                          </Text>
                        )}

                        {domain.tags.length > 0 && (
                          <Group gap="xs" wrap="wrap">
                            {domain.tags.slice(0, 3).map((tag) => (
                              <Badge key={tag} size="xs" variant="dot" color="blue">
                                {tag}
                              </Badge>
                            ))}
                            {domain.tags.length > 3 && (
                              <Badge size="xs" variant="light" color="gray">
                                +{domain.tags.length - 3} more
                              </Badge>
                            )}
                          </Group>
                        )}
                      </Box>

                      <Group gap="xs">
                        <Tooltip label="Edit domain">
                          <ActionIcon
                            variant="light"
                            size="sm"
                            color="orange"
                            onClick={() => openEditDomain(domain)}
                          >
                            <IconEdit size={14} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="Delete domain">
                          <ActionIcon
                            variant="light"
                            color="red"
                            size="sm"
                            onClick={() => handleDeleteDomain(domain.domain_id)}
                          >
                            <IconTrash size={14} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                    </Group>
                  </Card>
                ))}

                {domains.length === 0 && !loading && (
                  <Card withBorder p="xl" style={{ gridColumn: '1 / -1' }}>
                    <Stack align="center" gap="md">
                      <IconCategory size={48} color="var(--mantine-color-gray-4)" />
                      <Text size="lg" fw={500} c="dimmed">
                        No domains found
                      </Text>
                      <Text size="sm" c="dimmed" ta="center">
                        Create your first domain to organize interview questions by category.
                      </Text>
                      <Button
                        leftSection={<IconPlus size={16} />}
                        onClick={() => {
                          resetDomainForm();
                          setEditingDomain(null);
                          setDomainModalOpened(true);
                        }}
                      >
                        Create First Domain
                      </Button>
                    </Stack>
                  </Card>
                )}
              </SimpleGrid>
            </CardSection>
          </Card>
        </Tabs.Panel>
      </Tabs>

      {/* Question Modal */}
      <Modal
        opened={questionModalOpened}
        onClose={() => setQuestionModalOpened(false)}
        title={editingQuestion ? 'Edit Question' : 'Create New Question'}
        size="xl"
      >
        <Stack gap="md">
          <Grid>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <TextInput
                label="Question ID"
                value={questionForm.question_id}
                onChange={(e) => setQuestionForm({ ...questionForm, question_id: e.target.value })}
                placeholder="Q001"
                required
              />
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Select
                label="Domain"
                value={questionForm.domain_name}
                onChange={(value) => {
                  const domain = domains.find(d => d.name === value);
                  setQuestionForm({
                    ...questionForm,
                    domain_name: value || '',
                    domain_id: domain?.domain_id || '',
                  });
                }}
                data={domains.map(d => ({ value: d.name, label: d.name }))}
                required
              />
            </Grid.Col>
          </Grid>

          <Textarea
            label="Question Text"
            value={questionForm.question_text}
            onChange={(e) => setQuestionForm({ ...questionForm, question_text: e.target.value })}
            placeholder="Enter the interview question..."
            minRows={3}
            required
          />

          <Textarea
            label="Rationale"
            value={questionForm.rationale}
            onChange={(e) => setQuestionForm({ ...questionForm, rationale: e.target.value })}
            placeholder="Why is this question important?"
            minRows={2}
          />

          <Grid>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Select
                label="Difficulty Level"
                value={questionForm.difficulty}
                onChange={(value) => setQuestionForm({ ...questionForm, difficulty: value as any })}
                data={[
                  { value: 'beginner', label: 'Beginner' },
                  { value: 'intermediate', label: 'Intermediate' },
                  { value: 'advanced', label: 'Advanced' },
                  { value: 'expert', label: 'Expert' },
                ]}
                required
              />
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <NumberInput
                label="Estimated Time (minutes)"
                value={questionForm.estimated_time}
                onChange={(value) => setQuestionForm({ ...questionForm, estimated_time: value || 5 })}
                min={1}
                max={60}
              />
            </Grid.Col>
          </Grid>

          <MultiSelect
            label="Tags"
            value={questionForm.tags}
            onChange={(value) => setQuestionForm({ ...questionForm, tags: value })}
            data={[]}
            placeholder="Add tags..."
            searchable
            creatable={true}
          />

          <Grid>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <TextInput
                label="Category"
                value={questionForm.category}
                onChange={(e) => setQuestionForm({ ...questionForm, category: e.target.value })}
                placeholder="e.g., API Design"
              />
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <TextInput
                label="Subcategory"
                value={questionForm.subcategory}
                onChange={(e) => setQuestionForm({ ...questionForm, subcategory: e.target.value })}
                placeholder="e.g., Architecture"
              />
            </Grid.Col>
          </Grid>

          <Switch
            label="Active"
            checked={questionForm.is_active}
            onChange={(e) => setQuestionForm({ ...questionForm, is_active: e.currentTarget.checked })}
          />

          <Group justify="flex-end">
            <Button variant="light" onClick={() => setQuestionModalOpened(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => editingQuestion ? handleUpdateQuestion(questionForm) : handleCreateQuestion(questionForm)}
            >
              {editingQuestion ? 'Update' : 'Create'} Question
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Domain Modal */}
      <Modal
        opened={domainModalOpened}
        onClose={() => setDomainModalOpened(false)}
        title={editingDomain ? 'Edit Domain' : 'Create New Domain'}
        size="md"
      >
        <Stack gap="md">
          <TextInput
            label="Domain ID"
            value={domainForm.domain_id}
            onChange={(e) => setDomainForm({ ...domainForm, domain_id: e.target.value })}
            placeholder="D001"
            required
          />

          <TextInput
            label="Domain Name"
            value={domainForm.name}
            onChange={(e) => setDomainForm({ ...domainForm, name: e.target.value })}
            placeholder="e.g., API Led Connectivity"
            required
          />

          <Textarea
            label="Description"
            value={domainForm.description}
            onChange={(e) => setDomainForm({ ...domainForm, description: e.target.value })}
            placeholder="Description of this domain..."
            minRows={3}
          />

          <MultiSelect
            label="Tags"
            value={domainForm.tags}
            onChange={(value) => setDomainForm({ ...domainForm, tags: value })}
            data={[]}
            placeholder="Add tags..."
            searchable
            creatable={true}
          />

          <Group justify="flex-end">
            <Button variant="light" onClick={() => setDomainModalOpened(false)}>
              Cancel
            </Button>
            <Button
              onClick={editingDomain ? handleUpdateDomain : handleCreateDomain}
            >
              {editingDomain ? 'Update' : 'Create'} Domain
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        opened={deleteModalOpened}
        onClose={() => {
          setDeleteModalOpened(false);
          setQuestionToDelete(null);
        }}
        title="Delete Question"
        size="md"
      >
        <Stack gap="md">
          <Alert color="red" icon={<IconTrash size={16} />}>
            <Text fw={500} mb="xs">Are you sure you want to delete this question?</Text>
            <Text size="sm" c="dimmed">
              This action cannot be undone. The question will be permanently removed from the system.
            </Text>
          </Alert>

          {questionToDelete && (
            <Card withBorder p="md">
              <Text size="sm" fw={500} mb="xs">Question to delete:</Text>
              <Text size="sm" c="dimmed" mb="xs">
                {questionToDelete.question_text}
              </Text>
              <Group gap="xs">
                <Badge color={getDifficultyColor(questionToDelete.difficulty)} size="xs">
                  {questionToDelete.difficulty}
                </Badge>
                <Badge color="blue" variant="light" size="xs">
                  {questionToDelete.domain_name}
                </Badge>
                <Badge color={getSourceColor(questionToDelete.source)} variant="light" size="xs">
                  {questionToDelete.source}
                </Badge>
              </Group>
            </Card>
          )}

          <Group justify="flex-end">
            <Button
              variant="light"
              onClick={() => {
                setDeleteModalOpened(false);
                setQuestionToDelete(null);
              }}
            >
              Cancel
            </Button>
            <Button
              color="red"
              onClick={handleDeleteQuestion}
              leftSection={<IconTrash size={16} />}
            >
              Delete Question
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Question Details Modal */}
      <Modal
        opened={detailsModalOpened}
        onClose={() => {
          setDetailsModalOpened(false);
          setSelectedQuestion(null);
        }}
        title="Question Details"
        size="xl"
      >
        {selectedQuestion && (
          <Stack gap="lg">
            {/* Basic Information */}
            <Card withBorder p="md">
              <Title order={5} mb="md">Basic Information</Title>
              <Stack gap="md">
                <Group>
                  <Text fw={500} size="sm">Question ID:</Text>
                  <Text size="sm" style={{ fontFamily: 'monospace' }}>{selectedQuestion.question_id}</Text>
                </Group>
                <Group>
                  <Text fw={500} size="sm">Domain:</Text>
                  <Badge color="blue" variant="light">{selectedQuestion.domain_name}</Badge>
                </Group>
                <Group>
                  <Text fw={500} size="sm">Difficulty:</Text>
                  <Badge color={getDifficultyColor(selectedQuestion.difficulty)}>
                    {selectedQuestion.difficulty.toUpperCase()}
                  </Badge>
                </Group>
                <Group>
                  <Text fw={500} size="sm">Source:</Text>
                  <Badge color={getSourceColor(selectedQuestion.source)} variant="light">
                    {selectedQuestion.source}
                  </Badge>
                </Group>
                <Group>
                  <Text fw={500} size="sm">Status:</Text>
                  <Badge color={selectedQuestion.metadata.is_active ? 'green' : 'red'}>
                    {selectedQuestion.metadata.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </Group>
              </Stack>
            </Card>

            {/* Question Text */}
            <Card withBorder p="md">
              <Title order={5} mb="md">Question Text</Title>
              <Text size="sm" style={{ lineHeight: 1.6 }}>
                {selectedQuestion.question_text}
              </Text>
            </Card>

            {/* Rationale */}
            {selectedQuestion.rationale && (
              <Card withBorder p="md">
                <Title order={5} mb="md">Rationale</Title>
                <Text size="sm" style={{ lineHeight: 1.6, fontStyle: 'italic' }}>
                  {selectedQuestion.rationale}
                </Text>
              </Card>
            )}

            {/* Answer Criteria */}
            <Card withBorder p="md">
              <Title order={5} mb="md">Answer Criteria</Title>
              <Stack gap="md">
                {selectedQuestion.answer_criteria.map((criteria, index) => (
                  <Card key={index} withBorder p="sm" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                    <Group justify="space-between" mb="xs">
                      <Badge color="blue" size="sm">Level {criteria.level}</Badge>
                    </Group>
                    <Text size="sm">{criteria.criteria}</Text>
                  </Card>
                ))}
              </Stack>
            </Card>

            {/* Sample Answers */}
            {selectedQuestion.sample_answers && Object.keys(selectedQuestion.sample_answers).length > 0 && (
              <Card withBorder p="md">
                <Title order={5} mb="md">Sample Answers</Title>
                <Stack gap="md">
                  {Object.entries(selectedQuestion.sample_answers).map(([level, answer]) => (
                    <Card key={level} withBorder p="sm" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                      <Group justify="space-between" mb="xs">
                        <Badge color="green" size="sm">Level {level}</Badge>
                      </Group>
                      <Text size="sm">{answer}</Text>
                    </Card>
                  ))}
                </Stack>
              </Card>
            )}

            {/* Metadata */}
            <Card withBorder p="md">
              <Title order={5} mb="md">Metadata</Title>
              <Stack gap="md">
                <Group>
                  <Text fw={500} size="sm">Tags:</Text>
                  <Group gap="xs">
                    {selectedQuestion.metadata.tags.map((tag, index) => (
                      <Badge key={index} color="gray" variant="light" size="xs">
                        {tag}
                      </Badge>
                    ))}
                  </Group>
                </Group>
                {selectedQuestion.metadata.category && (
                  <Group>
                    <Text fw={500} size="sm">Category:</Text>
                    <Text size="sm">{selectedQuestion.metadata.category}</Text>
                  </Group>
                )}
                {selectedQuestion.metadata.subcategory && (
                  <Group>
                    <Text fw={500} size="sm">Subcategory:</Text>
                    <Text size="sm">{selectedQuestion.metadata.subcategory}</Text>
                  </Group>
                )}
                <Group>
                  <Text fw={500} size="sm">Estimated Time:</Text>
                  <Text size="sm">{selectedQuestion.metadata.estimated_time} minutes</Text>
                </Group>
                <Group>
                  <Text fw={500} size="sm">Version:</Text>
                  <Text size="sm">{selectedQuestion.metadata.version}</Text>
                </Group>
              </Stack>
            </Card>

            {/* Timestamps */}
            <Card withBorder p="md">
              <Title order={5} mb="md">Timestamps</Title>
              <Stack gap="sm">
                <Group>
                  <Text fw={500} size="sm">Created:</Text>
                  <Text size="sm">{new Date(selectedQuestion.created_at).toLocaleString()}</Text>
                </Group>
                <Group>
                  <Text fw={500} size="sm">Last Updated:</Text>
                  <Text size="sm">{new Date(selectedQuestion.updated_at).toLocaleString()}</Text>
                </Group>
              </Stack>
            </Card>

            <Group justify="flex-end">
              <Button
                variant="light"
                onClick={() => {
                  setDetailsModalOpened(false);
                  setSelectedQuestion(null);
                }}
              >
                Close
              </Button>
              <Button
                onClick={() => {
                  setDetailsModalOpened(false);
                  setSelectedQuestion(null);
                  openEditQuestion(selectedQuestion);
                }}
                leftSection={<IconEdit size={16} />}
              >
                Edit Question
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>
    </Page>
  );
}
