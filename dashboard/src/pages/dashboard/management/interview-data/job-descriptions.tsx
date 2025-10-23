import { useDeleteJob, useGetJobs } from '@/api/resources';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { apiUtils } from '@/config';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Card,
  CardSection,
  Flex,
  Group,
  LoadingOverlay,
  Menu,
  Modal,
  Pagination,
  Stack,
  Table,
  Text,
  TextInput,
  Title
} from '@mantine/core';
import {
  IconBriefcase,
  IconBuilding,
  IconDotsVertical,
  IconDownload,
  IconEdit,
  IconEye,
  IconPlus,
  IconSearch,
  IconTarget,
  IconTrash,
  IconUsers,
  IconX
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

interface JobDescription {
  job_id: string;
  title: string;
  department?: string;
  location?: string;
  experience_level: string;
  min_experience_years: number;
  max_experience_years?: number;
  required_skills_count: number;
  preferred_skills_count: number;
  nice_to_have_skills_count: number;
  responsibilities_count: number;
  company_name?: string;
  analysis_timestamp: string;
  job_source?: string;
  // File metadata fields
  metadata?: {
    original_filename?: string;
    file_size?: number;
    file_type?: string;
    upload_timestamp?: string;
    content_type?: string;
    source_type?: string;
    source_url?: string;
    scraping_timestamp?: string;
    processing_status?: string;
    processing_errors?: string[];
    version?: string;
  };
  // Enhanced fields for detailed view
  summary?: string;
  required_skills?: string[];
  preferred_skills?: string[];
  nice_to_have_skills?: string[];
  responsibilities?: string[];
  requirements?: string[];
  skill_priorities?: string[];
  assessment_focus_areas?: string[];
  company_context?: {
    company_name?: string;
    company_description?: string;
    company_location?: string;
    company_website?: string;
    funding_status?: string;
    founded_year?: number;
    employee_count?: number;
    work_culture?: string;
    benefits?: string[];
    growth_opportunities?: string;
    company_values?: string;
    industry?: string;
    company_size?: string;
    tech_stack?: string[];
    team_size?: number;
    reporting_structure?: string;
    remote_policy?: string;
  };
  expected_role_responsibilities?: string[] | string;
  expected_profile?: string[] | string;
}

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Management', href: paths.dashboard.management.root },
  { label: 'Interview Data', href: paths.dashboard.management.interviewData.root },
  { label: 'Job Descriptions' },
];

export default function JobDescriptionsManagement() {
  const navigate = useNavigate();
  const location = useLocation();
  const [filteredJobs, setFilteredJobs] = useState<JobDescription[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedJob, setSelectedJob] = useState<JobDescription | null>(null);

  // Check for job_id in URL parameters for filtering
  const urlParams = new URLSearchParams(location.search);
  const jobIdFilter = urlParams.get('job_id');
  const [viewModalOpen, setViewModalOpen] = useState(false);
  const [analysisModalOpen, setAnalysisModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [originalJobData, setOriginalJobData] = useState<any>(null);
  const [analysisJobData, setAnalysisJobData] = useState<any>(null);
  const [originalFileData, setOriginalFileData] = useState<any>(null);
  const [isLoadingOriginal, setIsLoadingOriginal] = useState(false);
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  // Use the new REST API hooks
  const { data: jobsData, isLoading, error } = useGetJobs();
  const deleteJobMutation = useDeleteJob();

  const jobs = jobsData?.jobs || [];

  useEffect(() => {
    filterJobs();
  }, [jobs, searchTerm, jobIdFilter]);

  // Transform jobs data to match our interface
  const transformJobs = (jobsData: any[]) => {
    return jobsData?.map((job: any) => {
      return {
        job_id: job.id,
        title: job.title,
        department: job.department,
        location: job.location,
        experience_level: job.experience_level || 'Not specified',
        min_experience_years: job.min_experience_years || 0,
        max_experience_years: job.max_experience_years,
        required_skills_count: job.required_skills?.length || 0,
        preferred_skills_count: job.preferred_skills?.length || 0,
        nice_to_have_skills_count: job.nice_to_have_skills?.length || 0,
        responsibilities_count: job.responsibilities?.length || 0,
        company_name: job.company,
        analysis_timestamp: job.created_at || new Date().toISOString(),
        job_source: 'Upload',
        // Enhanced fields
        summary: job.summary,
        required_skills: Array.isArray(job.required_skills)
          ? job.required_skills.map((skill: any) => typeof skill === 'string' ? skill : skill.name || skill.text || JSON.stringify(skill))
          : [],
        preferred_skills: Array.isArray(job.preferred_skills)
          ? job.preferred_skills.map((skill: any) => typeof skill === 'string' ? skill : skill.name || skill.text || JSON.stringify(skill))
          : [],
        nice_to_have_skills: Array.isArray(job.nice_to_have_skills)
          ? job.nice_to_have_skills.map((skill: any) => typeof skill === 'string' ? skill : skill.name || skill.text || JSON.stringify(skill))
          : [],
        responsibilities: Array.isArray(job.responsibilities)
          ? job.responsibilities.map((resp: any) => typeof resp === 'string' ? resp : resp.text || resp.description || JSON.stringify(resp))
          : [],
        requirements: Array.isArray(job.requirements)
          ? job.requirements.map((req: any) => typeof req === 'string' ? req : req.text || req.description || JSON.stringify(req))
          : [],
        skill_priorities: Array.isArray(job.skill_priorities)
          ? job.skill_priorities.map((priority: any) => typeof priority === 'string' ? priority : priority.name || priority.text || JSON.stringify(priority))
          : [],
        assessment_focus_areas: Array.isArray(job.assessment_focus_areas)
          ? job.assessment_focus_areas.map((area: any) => typeof area === 'string' ? area : area.name || area.text || JSON.stringify(area))
          : [],
        company_context: job.company_context
      };
    }) || [];
  };

  const transformedJobs = transformJobs(jobs);

  const filterJobs = () => {
    let filtered = transformedJobs;

    // Apply job_id filter if present in URL
    if (jobIdFilter) {
      filtered = filtered.filter(job => job.job_id === jobIdFilter);
    }

    // Apply search term filter
    if (searchTerm.trim()) {
      filtered = filtered.filter(job =>
        job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.department?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.company_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.location?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredJobs(filtered);
  };

  const loadOriginalJobData = async (jobId: string) => {
    setIsLoadingOriginal(true);
    try {
      // Get the full job data from the main endpoint
      const response = await apiUtils.apiRequest(`/management/interview/jobs/${jobId}`);

      if (response.ok) {
        const data = await response.json();
        console.log('Job data response:', data);
        // The API returns { success: true, job_description: {...} }
        if (data.success && data.job_description) {
          console.log('Setting job description data:', data.job_description);
          setOriginalJobData(data.job_description);

          // Also fetch original file data for file information
          const originalResponse = await apiUtils.apiRequest(`/management/interview/jobs/${jobId}/original`);
          if (originalResponse.ok) {
            const originalData = await originalResponse.json();
            console.log('Original file data:', originalData);
            setOriginalFileData(originalData);
          }
        } else {
          console.log('No job_description in response, falling back to original endpoint');
          // Fallback to original endpoint for basic file info
          const originalResponse = await apiUtils.apiRequest(`/management/interview/jobs/${jobId}/original`);
          if (originalResponse.ok) {
            const originalData = await originalResponse.json();
            console.log('Original endpoint data:', originalData);
            setOriginalJobData(originalData);
            setOriginalFileData(originalData);
          }
        }
      } else {
        // Fallback to original endpoint for basic file info
        const originalResponse = await apiUtils.apiRequest(`/management/interview/jobs/${jobId}/original`);
        if (originalResponse.ok) {
          const originalData = await originalResponse.json();
          setOriginalJobData(originalData);
          setOriginalFileData(originalData);
        }
      }
    } catch (error) {
      console.error('Error loading job data:', error);
    } finally {
      setIsLoadingOriginal(false);
    }
  };

  const loadAnalysisJobData = async (jobId: string) => {
    setIsLoadingAnalysis(true);
    try {
      const response = await apiUtils.apiRequest(`/management/interview/jobs/${jobId}`);

      if (response.ok) {
        const data = await response.json();
        // The API returns { success: true, job_description: {...} }
        if (data.success && data.job_description) {
          setAnalysisJobData(data.job_description);
        }
      }
    } catch (error) {
      console.error('Error loading analysis data:', error);
    } finally {
      setIsLoadingAnalysis(false);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    try {
      await deleteJobMutation.mutateAsync({
        model: { id: jobId },
        route: { job_id: jobId }
      });

      setDeleteModalOpen(false);
      setSelectedJob(null);
    } catch (error) {
      // Silently handle error
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleDateString();
  };

  const getExperienceLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'senior':
      case 'expert':
        return 'green';
      case 'mid':
      case 'intermediate':
        return 'blue';
      case 'junior':
      case 'entry':
        return 'yellow';
      default:
        return 'gray';
    }
  };

  // Pagination
  const totalPages = Math.ceil(filteredJobs.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentJobs = filteredJobs.slice(startIndex, endIndex);

  return (
    <Page title="Job Descriptions Management">
      <PageHeader title="Job Descriptions Management" breadcrumbs={breadcrumbs} />

      <LoadingOverlay visible={isLoading} />

      {error && (
        <Alert color="red" title="Error" mb="lg">
          {error instanceof Error ? error.message : String(error)}
        </Alert>
      )}

      <Stack gap="lg">
        {/* Header Actions */}
        <Card withBorder>
          <CardSection p="xl">
            <Group justify="space-between" mb="lg">
              <Box>
                <Title order={4}>💼 Job Descriptions</Title>
                <Text size="sm" c="dimmed">
                  Manage and organize job description data
                </Text>
              </Box>
              <Button
                leftSection={<IconPlus size={16} />}
                onClick={() => navigate(paths.dashboard.apps.interviewCreate + '?step=1')}
              >
                Upload New Job
              </Button>
            </Group>

            {/* Search and Filters */}
            <Group gap="md">
              <TextInput
                placeholder="Search by title, department, company, or location..."
                leftSection={<IconSearch size={16} />}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ flex: 1 }}
              />
              <Badge color="green" variant="light">
                {filteredJobs.length} jobs
              </Badge>
              {jobIdFilter && (
                <Badge
                  color="blue"
                  variant="light"
                  rightSection={
                    <ActionIcon
                      size="xs"
                      variant="subtle"
                      onClick={() => navigate(location.pathname)}
                    >
                      <IconX size={10} />
                    </ActionIcon>
                  }
                >
                  Filtered by Job ID: {jobIdFilter.substring(0, 8)}...
                </Badge>
              )}
            </Group>
          </CardSection>
        </Card>

        {/* Jobs Table */}
        <Card withBorder>
          <CardSection p="xl">
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Job Title</Table.Th>
                  <Table.Th>Company</Table.Th>
                  <Table.Th>Department</Table.Th>
                  <Table.Th>Experience Level</Table.Th>
                  <Table.Th>Skills</Table.Th>
                  <Table.Th>Location</Table.Th>
                  <Table.Th>Last Updated</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {currentJobs.map((job) => (
                  <Table.Tr key={job.job_id}>
                    <Table.Td>
                      <Box>
                        <Text fw={500}>{job.title}</Text>
                        <Text size="sm" c="dimmed">
                          {job.min_experience_years}-{job.max_experience_years || job.min_experience_years} years
                        </Text>
                      </Box>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">
                        {job.company_name || 'Not specified'}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">
                        {job.department || 'Not specified'}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        color={getExperienceLevelColor(job.experience_level)}
                        variant="light"
                      >
                        {job.experience_level}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <Badge size="sm" variant="light" color="red">
                          {job.required_skills_count} required
                        </Badge>
                        <Badge size="sm" variant="light" color="blue">
                          {job.preferred_skills_count} preferred
                        </Badge>
                        <Badge size="sm" variant="light" color="gray">
                          {job.nice_to_have_skills_count} nice-to-have
                        </Badge>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">
                        {job.location || 'Not specified'}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">
                        {formatDate(job.analysis_timestamp)}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Menu>
                        <Menu.Target>
                          <ActionIcon variant="subtle" size="sm">
                            <IconDotsVertical size={16} />
                          </ActionIcon>
                        </Menu.Target>
                        <Menu.Dropdown>
                          <Menu.Item
                            leftSection={<IconEye size={16} />}
                            onClick={() => {
                              setSelectedJob(job);
                              loadOriginalJobData(job.job_id);
                              setViewModalOpen(true);
                            }}
                          >
                            View Details
                          </Menu.Item>
                          <Menu.Item
                            leftSection={<IconEdit size={16} />}
                            onClick={() => {
                              setSelectedJob(job);
                              loadAnalysisJobData(job.job_id);
                              setAnalysisModalOpen(true);
                            }}
                          >
                            View Analysis
                          </Menu.Item>
                          <Menu.Item
                            leftSection={<IconDownload size={16} />}
                            onClick={() => {
                              // TODO: Implement download functionality
                            }}
                          >
                            Download
                          </Menu.Item>
                          <Menu.Divider />
                          <Menu.Item
                            leftSection={<IconTrash size={16} />}
                            color="red"
                            onClick={() => {
                              setSelectedJob(job);
                              setDeleteModalOpen(true);
                            }}
                          >
                            Delete
                          </Menu.Item>
                        </Menu.Dropdown>
                      </Menu>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>

            {currentJobs.length === 0 && !isLoading && (
              <Box ta="center" py="xl">
                <Stack gap="md" align="center">
                  <Text size="lg" c="dimmed">No job descriptions found</Text>
                  <Text size="sm" c="dimmed">Upload your first job description to get started</Text>
                  <Button
                    leftSection={<IconPlus size={16} />}
                    onClick={() => navigate(paths.dashboard.apps.interviewCreate + '?step=1')}
                    variant="light"
                  >
                    Upload Job Description
                  </Button>
                </Stack>
              </Box>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <Flex justify="center" mt="lg">
                <Pagination
                  value={currentPage}
                  onChange={setCurrentPage}
                  total={totalPages}
                  size="sm"
                />
              </Flex>
            )}
          </CardSection>
        </Card>
      </Stack>

      {/* View Job Modal */}
      <Modal
        opened={viewModalOpen}
        onClose={() => setViewModalOpen(false)}
        title={
          <Group gap="sm">
            <IconBriefcase size={20} />
            <Text>Job Description Details</Text>
          </Group>
        }
        size="xl"
        styles={{
          body: { maxHeight: '80vh', overflowY: 'auto' }
        }}
      >
        <LoadingOverlay visible={isLoadingOriginal} />
        {selectedJob && originalJobData && (
          <Stack gap="lg">
            {/* Header with Key Info */}
            <Card withBorder style={{ background: 'linear-gradient(135deg, var(--mantine-color-blue-0) 0%, var(--mantine-color-cyan-0) 100%)' }}>
              <CardSection p="xl">
                <Group justify="space-between" align="flex-start" mb="md">
                  <Box style={{ flex: 1 }}>
                    <Title order={3} mb="xs" style={{ color: 'var(--mantine-color-blue-8)' }}>
                      {originalJobData.title || selectedJob.title}
                    </Title>
                    <Group gap="lg" mb="md">
                      <Group gap="xs">
                        <IconBuilding size={16} color="var(--mantine-color-gray-6)" />
                        <Text size="sm" fw={500}>
                          {originalJobData.company || selectedJob.company_name || 'Company not specified'}
                        </Text>
                      </Group>
                      <Group gap="xs">
                        <IconTarget size={16} color="var(--mantine-color-gray-6)" />
                        <Text size="sm" fw={500}>
                          {originalJobData.department || selectedJob.department || 'Department not specified'}
                        </Text>
                      </Group>
                      <Group gap="xs">
                        <IconUsers size={16} color="var(--mantine-color-gray-6)" />
                        <Text size="sm" fw={500}>
                          {originalJobData.location || selectedJob.location || 'Location not specified'}
                        </Text>
                      </Group>
                    </Group>
                    <Group gap="md">
                      <Badge
                        size="lg"
                        color={getExperienceLevelColor(originalJobData.experience_level || selectedJob.experience_level)}
                        variant="filled"
                        leftSection={<IconTarget size={14} />}
                      >
                        {originalJobData.experience_level || selectedJob.experience_level}
                      </Badge>
                      <Badge
                        size="lg"
                        color="blue"
                        variant="light"
                        leftSection={<IconUsers size={14} />}
                      >
                        {originalJobData.min_experience_years || selectedJob.min_experience_years}-
                        {originalJobData.max_experience_years || selectedJob.max_experience_years || selectedJob.min_experience_years} years
                      </Badge>
                    </Group>
                  </Box>
                </Group>
              </CardSection>
            </Card>

            {/* Company Context */}
            {originalJobData.company_context && (
              <Card withBorder>
                <CardSection p="xl">
                  <Group gap="sm" mb="lg">
                    <IconBuilding size={20} color="var(--mantine-color-blue-6)" />
                    <Title order={5}>🏢 Company Information</Title>
                  </Group>

                  <Stack gap="lg">
                    {/* Company Overview */}
                    {(originalJobData.company_context.company_name || originalJobData.company_context.company_description) && (
                      <Box>
                        <Text fw={600} size="sm" c="dimmed" mb="xs" tt="uppercase" lts={1}>Company Overview</Text>
                        <Stack gap="sm">
                          {originalJobData.company_context.company_name && (
                            <Group>
                              <Text fw={500} size="sm" w={140}>Company Name:</Text>
                              <Text size="sm">{originalJobData.company_context.company_name}</Text>
                            </Group>
                          )}
                          {originalJobData.company_context.company_description && (
                            <Box>
                              <Text fw={500} size="sm" mb="xs">Description:</Text>
                              <Text size="sm" style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5', color: 'var(--mantine-color-gray-7)' }}>
                                {originalJobData.company_context.company_description}
                              </Text>
                            </Box>
                          )}
                        </Stack>
                      </Box>
                    )}

                    {/* Company Details Grid */}
                    <Box>
                      <Text fw={600} size="sm" c="dimmed" mb="xs" tt="uppercase" lts={1}>Company Details</Text>
                      <Group gap="lg" wrap="wrap">
                        {originalJobData.company_context.company_location && (
                          <Box>
                            <Text size="xs" c="dimmed" mb={4}>📍 Location</Text>
                            <Text size="sm" fw={500}>{originalJobData.company_context.company_location}</Text>
                          </Box>
                        )}
                        {originalJobData.company_context.founded_year && (
                          <Box>
                            <Text size="xs" c="dimmed" mb={4}>📅 Founded</Text>
                            <Text size="sm" fw={500}>{originalJobData.company_context.founded_year}</Text>
                          </Box>
                        )}
                        {originalJobData.company_context.employee_count && (
                          <Box>
                            <Text size="xs" c="dimmed" mb={4}>👥 Employees</Text>
                            <Text size="sm" fw={500}>{originalJobData.company_context.employee_count.toLocaleString()}</Text>
                          </Box>
                        )}
                        {originalJobData.company_context.team_size && (
                          <Box>
                            <Text size="xs" c="dimmed" mb={4}>👨‍💼 Team Size</Text>
                            <Text size="sm" fw={500}>{originalJobData.company_context.team_size} members</Text>
                          </Box>
                        )}
                        {originalJobData.company_context.industry && (
                          <Box>
                            <Text size="xs" c="dimmed" mb={4}>🏭 Industry</Text>
                            <Text size="sm" fw={500}>{originalJobData.company_context.industry}</Text>
                          </Box>
                        )}
                        {originalJobData.company_context.company_size && (
                          <Box>
                            <Text size="xs" c="dimmed" mb={4}>📊 Company Size</Text>
                            <Text size="sm" fw={500}>{originalJobData.company_context.company_size}</Text>
                          </Box>
                        )}
                        {originalJobData.company_context.funding_status && (
                          <Box>
                            <Text size="xs" c="dimmed" mb={4}>💰 Funding</Text>
                            <Text size="sm" fw={500}>{originalJobData.company_context.funding_status}</Text>
                          </Box>
                        )}
                        {originalJobData.company_context.remote_policy && (
                          <Box>
                            <Text size="xs" c="dimmed" mb={4}>🏠 Remote Policy</Text>
                            <Text size="sm" fw={500}>{originalJobData.company_context.remote_policy}</Text>
                          </Box>
                        )}
                      </Group>
                    </Box>

                    {/* Company Website */}
                    {originalJobData.company_context.company_website && (
                      <Box>
                        <Text fw={600} size="sm" c="dimmed" mb="xs" tt="uppercase" lts={1}>Website</Text>
                        <Button
                          variant="light"
                          leftSection={<IconBuilding size={14} />}
                          component="a"
                          href={originalJobData.company_context.company_website}
                          target="_blank"
                          rel="noopener noreferrer"
                          size="sm"
                        >
                          Visit Company Website
                        </Button>
                      </Box>
                    )}

                    {/* Benefits */}
                    {originalJobData.company_context.benefits && originalJobData.company_context.benefits.length > 0 && (
                      <Box>
                        <Text fw={600} size="sm" c="dimmed" mb="xs" tt="uppercase" lts={1}>Benefits & Perks</Text>
                        <Group gap="xs">
                          {originalJobData.company_context.benefits.map((benefit: string, index: number) => (
                            <Badge key={index} size="sm" variant="light" color="green">
                              {benefit}
                            </Badge>
                          ))}
                        </Group>
                      </Box>
                    )}

                    {/* Tech Stack */}
                    {originalJobData.company_context.tech_stack && originalJobData.company_context.tech_stack.length > 0 && (
                      <Box>
                        <Text fw={600} size="sm" c="dimmed" mb="xs" tt="uppercase" lts={1}>Technology Stack</Text>
                        <Group gap="xs">
                          {originalJobData.company_context.tech_stack.map((tech: string, index: number) => (
                            <Badge key={index} size="sm" variant="light" color="blue">
                              {tech}
                            </Badge>
                          ))}
                        </Group>
                      </Box>
                    )}

                    {/* Culture & Values */}
                    {(originalJobData.company_context.work_culture || originalJobData.company_context.company_values || originalJobData.company_context.growth_opportunities) && (
                      <Box>
                        <Text fw={600} size="sm" c="dimmed" mb="xs" tt="uppercase" lts={1}>Culture & Values</Text>
                        <Stack gap="sm">
                          {originalJobData.company_context.work_culture && (
                            <Box>
                              <Text size="sm" fw={500} mb="xs">Work Culture:</Text>
                              <Text size="sm" style={{ color: 'var(--mantine-color-gray-7)' }}>
                                {originalJobData.company_context.work_culture}
                              </Text>
                            </Box>
                          )}
                          {originalJobData.company_context.company_values && (
                            <Box>
                              <Text size="sm" fw={500} mb="xs">Company Values:</Text>
                              <Text size="sm" style={{ color: 'var(--mantine-color-gray-7)' }}>
                                {originalJobData.company_context.company_values}
                              </Text>
                            </Box>
                          )}
                          {originalJobData.company_context.growth_opportunities && (
                            <Box>
                              <Text size="sm" fw={500} mb="xs">Growth Opportunities:</Text>
                              <Text size="sm" style={{ color: 'var(--mantine-color-gray-7)' }}>
                                {originalJobData.company_context.growth_opportunities}
                              </Text>
                            </Box>
                          )}
                        </Stack>
                      </Box>
                    )}
                  </Stack>
                </CardSection>
              </Card>
            )}

            {/* Original Text */}
            {originalJobData.original_text && (
              <Card withBorder>
                <CardSection p="xl">
                  <Group gap="sm" mb="lg">
                    <IconDownload size={20} color="var(--mantine-color-gray-6)" />
                    <Title order={5}>📄 Original Job Description Text</Title>
                  </Group>

                  <Card
                    withBorder
                    style={{
                      background: 'var(--mantine-color-gray-0)',
                      border: '1px solid var(--mantine-color-gray-3)'
                    }}
                  >
                    <CardSection p="lg">
                      <Box
                        style={{
                          fontSize: '13px',
                          lineHeight: '1.6',
                          color: 'var(--mantine-color-gray-8)',
                          whiteSpace: 'pre-wrap',
                          fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace',
                          maxHeight: '400px',
                          overflowY: 'auto'
                        }}
                      >
                        {originalJobData.original_text}
                      </Box>
                    </CardSection>
                  </Card>
                </CardSection>
              </Card>
            )}

            {/* Expected Role */}
            {originalJobData.expected_role_responsibilities && originalJobData.expected_role_responsibilities.length > 0 && (
              <Card withBorder>
                <CardSection p="xl">
                  <Group gap="sm" mb="lg">
                    <IconTarget size={20} color="var(--mantine-color-purple-6)" />
                    <Title order={5}>🎯 Expected Role & Responsibilities</Title>
                    <Badge size="sm" color="purple" variant="light">
                      {Array.isArray(originalJobData.expected_role_responsibilities) ? originalJobData.expected_role_responsibilities.length : 1} item(s)
                    </Badge>
                  </Group>

                  <Stack gap="md">
                    {Array.isArray(originalJobData.expected_role_responsibilities) ? (
                      originalJobData.expected_role_responsibilities.map((role: string, index: number) => (
                        <Card
                          key={index}
                          withBorder
                          style={{
                            borderLeft: '4px solid var(--mantine-color-purple-4)',
                            backgroundColor: 'var(--mantine-color-purple-0)'
                          }}
                        >
                          <CardSection p="md">
                            <Group gap="md" align="flex-start">
                              <Badge
                                size="sm"
                                color="purple"
                                variant="filled"
                                style={{ minWidth: '24px', height: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                              >
                                {index + 1}
                              </Badge>
                              <Text size="sm" style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5', flex: 1 }}>
                                {role}
                              </Text>
                            </Group>
                          </CardSection>
                        </Card>
                      ))
                    ) : (
                      <Card
                        withBorder
                        style={{
                          borderLeft: '4px solid var(--mantine-color-purple-4)',
                          backgroundColor: 'var(--mantine-color-purple-0)'
                        }}
                      >
                        <CardSection p="md">
                          <Text size="sm" style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>
                            {originalJobData.expected_role}
                          </Text>
                        </CardSection>
                      </Card>
                    )}
                  </Stack>
                </CardSection>
              </Card>
            )}

            {/* Expected Profile */}
            {originalJobData.expected_profile && originalJobData.expected_profile.length > 0 && (
              <Card withBorder>
                <CardSection p="xl">
                  <Group gap="sm" mb="lg">
                    <IconUsers size={20} color="var(--mantine-color-indigo-6)" />
                    <Title order={5}>👤 Expected Profile</Title>
                    <Badge size="sm" color="indigo" variant="light">
                      {Array.isArray(originalJobData.expected_profile) ? originalJobData.expected_profile.length : 1} profile(s)
                    </Badge>
                  </Group>

                  <Stack gap="md">
                    {Array.isArray(originalJobData.expected_profile) ? (
                      originalJobData.expected_profile.map((profile: string, index: number) => (
                        <Card
                          key={index}
                          withBorder
                          style={{
                            borderLeft: '4px solid var(--mantine-color-indigo-4)',
                            backgroundColor: 'var(--mantine-color-indigo-0)'
                          }}
                        >
                          <CardSection p="md">
                            <Group gap="md" align="flex-start">
                              <Badge
                                size="sm"
                                color="indigo"
                                variant="filled"
                                style={{ minWidth: '24px', height: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                              >
                                {index + 1}
                              </Badge>
                              <Text size="sm" style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5', flex: 1 }}>
                                {profile}
                              </Text>
                            </Group>
                          </CardSection>
                        </Card>
                      ))
                    ) : (
                      <Card
                        withBorder
                        style={{
                          borderLeft: '4px solid var(--mantine-color-indigo-4)',
                          backgroundColor: 'var(--mantine-color-indigo-0)'
                        }}
                      >
                        <CardSection p="md">
                          <Text size="sm" style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>
                            {originalJobData.expected_profile}
                          </Text>
                        </CardSection>
                      </Card>
                    )}
                  </Stack>
                </CardSection>
              </Card>
            )}

            {/* Job Summary */}
            {originalJobData.summary && (
              <Card withBorder>
                <CardSection p="xl">
                  <Group gap="sm" mb="lg">
                    <IconBriefcase size={20} color="var(--mantine-color-teal-6)" />
                    <Title order={5}>📝 Job Summary</Title>
                  </Group>

                  <Card
                    withBorder
                    style={{
                      background: 'var(--mantine-color-teal-0)',
                      border: '1px solid var(--mantine-color-teal-3)'
                    }}
                  >
                    <CardSection p="lg">
                      <Text
                        style={{
                          fontSize: '14px',
                          lineHeight: '1.6',
                          color: 'var(--mantine-color-gray-8)',
                          whiteSpace: 'pre-wrap'
                        }}
                      >
                        {originalJobData.summary}
                      </Text>
                    </CardSection>
                  </Card>
                </CardSection>
              </Card>
            )}



            {/* Skills */}
            <Card withBorder>
              <CardSection p="xl">
                <Group gap="sm" mb="lg">
                  <IconTarget size={20} color="var(--mantine-color-orange-6)" />
                  <Title order={5}>🛠️ Skills & Requirements</Title>
                </Group>

                <Stack gap="lg">
                  {/* Required Skills */}
                  {originalJobData.required_skills && originalJobData.required_skills.length > 0 && (
                    <Box>
                      <Group gap="xs" mb="md">
                        <Badge size="sm" color="red" variant="filled">Required</Badge>
                        <Text size="sm" c="dimmed">({originalJobData.required_skills.length} skills)</Text>
                      </Group>
                      <Group gap="xs" wrap="wrap">
                        {originalJobData.required_skills.map((skill: string, index: number) => (
                          <Badge
                            key={index}
                            size="md"
                            variant="light"
                            color="red"
                            style={{
                              border: '1px solid var(--mantine-color-red-3)',
                              backgroundColor: 'var(--mantine-color-red-0)'
                            }}
                          >
                            {skill}
                          </Badge>
                        ))}
                      </Group>
                    </Box>
                  )}

                  {/* Preferred Skills */}
                  {originalJobData.preferred_skills && originalJobData.preferred_skills.length > 0 && (
                    <Box>
                      <Group gap="xs" mb="md">
                        <Badge size="sm" color="blue" variant="filled">Preferred</Badge>
                        <Text size="sm" c="dimmed">({originalJobData.preferred_skills.length} skills)</Text>
                      </Group>
                      <Group gap="xs" wrap="wrap">
                        {originalJobData.preferred_skills.map((skill: string, index: number) => (
                          <Badge
                            key={index}
                            size="md"
                            variant="light"
                            color="blue"
                            style={{
                              border: '1px solid var(--mantine-color-blue-3)',
                              backgroundColor: 'var(--mantine-color-blue-0)'
                            }}
                          >
                            {skill}
                          </Badge>
                        ))}
                      </Group>
                    </Box>
                  )}

                  {/* Nice-to-Have Skills */}
                  {originalJobData.nice_to_have_skills && originalJobData.nice_to_have_skills.length > 0 && (
                    <Box>
                      <Group gap="xs" mb="md">
                        <Badge size="sm" color="gray" variant="filled">Nice-to-Have</Badge>
                        <Text size="sm" c="dimmed">({originalJobData.nice_to_have_skills.length} skills)</Text>
                      </Group>
                      <Group gap="xs" wrap="wrap">
                        {originalJobData.nice_to_have_skills.map((skill: string, index: number) => (
                          <Badge
                            key={index}
                            size="md"
                            variant="light"
                            color="gray"
                            style={{
                              border: '1px solid var(--mantine-color-gray-3)',
                              backgroundColor: 'var(--mantine-color-gray-0)'
                            }}
                          >
                            {skill}
                          </Badge>
                        ))}
                      </Group>
                    </Box>
                  )}

                  {/* Skills Summary */}
                  <Card withBorder style={{ background: 'var(--mantine-color-gray-0)' }}>
                    <CardSection p="md">
                      <Group justify="space-between">
                        <Text size="sm" fw={500}>Total Skills:</Text>
                        <Text size="sm" fw={600}>
                          {(originalJobData.required_skills?.length || 0) +
                            (originalJobData.preferred_skills?.length || 0) +
                            (originalJobData.nice_to_have_skills?.length || 0)} skills
                        </Text>
                      </Group>
                      <Group justify="space-between" mt="xs">
                        <Text size="sm" c="dimmed">Required:</Text>
                        <Text size="sm" c="red" fw={500}>{originalJobData.required_skills?.length || 0}</Text>
                      </Group>
                      <Group justify="space-between">
                        <Text size="sm" c="dimmed">Preferred:</Text>
                        <Text size="sm" c="blue" fw={500}>{originalJobData.preferred_skills?.length || 0}</Text>
                      </Group>
                      <Group justify="space-between">
                        <Text size="sm" c="dimmed">Nice-to-Have:</Text>
                        <Text size="sm" c="gray" fw={500}>{originalJobData.nice_to_have_skills?.length || 0}</Text>
                      </Group>
                    </CardSection>
                  </Card>
                </Stack>
              </CardSection>
            </Card>

            {/* Job Information */}
            <Card withBorder>
              <CardSection p="xl">
                <Group gap="sm" mb="lg">
                  <IconDownload size={20} color="var(--mantine-color-gray-6)" />
                  <Title order={5}>📁 Job Information</Title>
                </Group>

                <Group gap="lg" wrap="wrap">
                  <Box>
                    <Text size="xs" c="dimmed" mb={4}>📅 Analysis Date</Text>
                    <Text size="sm" fw={500}>{formatDate(originalJobData.analysis_timestamp)}</Text>
                  </Box>
                  <Box>
                    <Text size="xs" c="dimmed" mb={4}>🔗 Source</Text>
                    <Badge size="sm" color="blue" variant="light">
                      {originalJobData.job_source || 'Upload'}
                    </Badge>
                  </Box>
                  {originalJobData.posting_date && (
                    <Box>
                      <Text size="xs" c="dimmed" mb={4}>📋 Posting Date</Text>
                      <Text size="sm" fw={500}>{formatDate(originalJobData.posting_date)}</Text>
                    </Box>
                  )}
                  <Box>
                    <Text size="xs" c="dimmed" mb={4}>🆔 Job ID</Text>
                    <Text size="sm" fw={500} style={{ fontFamily: 'monospace' }}>
                      {originalJobData.job_id || selectedJob.job_id}
                    </Text>
                  </Box>
                </Group>
              </CardSection>
            </Card>

            {/* File Information - Only show if we have file data */}
            {originalFileData && (
              <Card withBorder>
                <CardSection p="xl">
                  <Group gap="sm" mb="lg">
                    <IconDownload size={20} color="var(--mantine-color-gray-6)" />
                    <Title order={5}>📄 File Information</Title>
                  </Group>

                  <Group gap="lg" wrap="wrap">
                    {originalFileData.file_name && (
                      <Box>
                        <Text size="xs" c="dimmed" mb={4}>📄 File Name</Text>
                        <Text size="sm" fw={500}>{originalFileData.file_name}</Text>
                      </Box>
                    )}
                    {originalFileData.file_size && (
                      <Box>
                        <Text size="xs" c="dimmed" mb={4}>📏 File Size</Text>
                        <Text size="sm" fw={500}>
                          {originalFileData.file_size ? `${(originalFileData.file_size / 1024).toFixed(1)} KB` : 'Not specified'}
                        </Text>
                      </Box>
                    )}
                    {originalFileData.file_type && (
                      <Box>
                        <Text size="xs" c="dimmed" mb={4}>📋 File Type</Text>
                        <Text size="sm" fw={500}>{originalFileData.file_type.toUpperCase()}</Text>
                      </Box>
                    )}
                    {originalFileData.upload_timestamp && (
                      <Box>
                        <Text size="xs" c="dimmed" mb={4}>📅 Upload Date</Text>
                        <Text size="sm" fw={500}>{formatDate(originalFileData.upload_timestamp)}</Text>
                      </Box>
                    )}
                    {originalFileData.source_type && (
                      <Box>
                        <Text size="xs" c="dimmed" mb={4}>🔗 Source Type</Text>
                        <Badge size="sm" color="blue" variant="light">
                          {originalFileData.source_type}
                        </Badge>
                      </Box>
                    )}
                    {originalFileData.source_url && (
                      <Box>
                        <Text size="xs" c="dimmed" mb={4}>🌐 Source URL</Text>
                        <Text size="sm" fw={500} style={{ wordBreak: 'break-all' }}>
                          {originalFileData.source_url}
                        </Text>
                      </Box>
                    )}
                    {originalFileData.processing_status && (
                      <Box>
                        <Text size="xs" c="dimmed" mb={4}>⚙️ Processing Status</Text>
                        <Badge size="sm" color={originalFileData.processing_status === 'completed' ? 'green' : 'yellow'} variant="light">
                          {originalFileData.processing_status}
                        </Badge>
                      </Box>
                    )}
                    {originalFileData.original_text && (
                      <Box>
                        <Text size="xs" c="dimmed" mb={4}>📝 Original Text</Text>
                        <Text size="sm" fw={500} c="dimmed">
                          {originalFileData.original_text.length > 100
                            ? `${originalFileData.original_text.substring(0, 100)}...`
                            : originalFileData.original_text}
                        </Text>
                      </Box>
                    )}
                  </Group>
                </CardSection>
              </Card>
            )}
          </Stack>
        )}
      </Modal>

      {/* Analysis Modal */}
      <Modal
        opened={analysisModalOpen}
        onClose={() => setAnalysisModalOpen(false)}
        title="AI Analysis Results"
        size="xl"
        styles={{
          body: { maxHeight: '80vh', overflowY: 'auto' }
        }}
      >
        <LoadingOverlay visible={isLoadingAnalysis} />
        {selectedJob && analysisJobData && (
          <Stack gap="lg">
            {/* Analysis Header */}
            <Card withBorder>
              <CardSection p="md">
                <Title order={5} mb="md">🤖 AI Analysis Results</Title>
                <Text size="sm" c="dimmed">
                  This shows the AI's analysis of the job description, including extracted skills,
                  responsibilities, and assessment recommendations.
                </Text>
              </CardSection>
            </Card>

            {/* Basic Information */}
            <Card withBorder>
              <CardSection p="md">
                <Title order={5} mb="md">📋 Job Information</Title>
                <Stack gap="sm">
                  <Group>
                    <Text fw={500} w={120}>Title:</Text>
                    <Text>{analysisJobData.title || selectedJob.title}</Text>
                  </Group>
                  <Group>
                    <Text fw={500} w={120}>Company:</Text>
                    <Text>{analysisJobData.company || selectedJob.company_name || 'Not specified'}</Text>
                  </Group>
                  <Group>
                    <Text fw={500} w={120}>Department:</Text>
                    <Text>{analysisJobData.department || selectedJob.department || 'Not specified'}</Text>
                  </Group>
                  <Group>
                    <Text fw={500} w={120}>Location:</Text>
                    <Text>{analysisJobData.location || selectedJob.location || 'Not specified'}</Text>
                  </Group>
                  <Group>
                    <Text fw={500} w={120}>Experience Level:</Text>
                    <Badge color={getExperienceLevelColor(analysisJobData.experience_level || selectedJob.experience_level)}>
                      {analysisJobData.experience_level || selectedJob.experience_level}
                    </Badge>
                  </Group>
                  <Group>
                    <Text fw={500} w={120}>Experience Years:</Text>
                    <Text>
                      {analysisJobData.min_experience_years || selectedJob.min_experience_years}-
                      {analysisJobData.max_experience_years || selectedJob.max_experience_years || selectedJob.min_experience_years} years
                    </Text>
                  </Group>
                </Stack>
              </CardSection>
            </Card>

            {/* AI Extracted Skills */}
            {analysisJobData.required_skills && analysisJobData.required_skills.length > 0 && (
              <Card withBorder>
                <CardSection p="md">
                  <Title order={4} mb="md">🛠️ AI Extracted Skills</Title>
                  <Stack gap="md">
                    {/* Required Skills */}
                    <Box>
                      <Text fw={500} size="sm" mb="xs" c="red">Required Skills:</Text>
                      <Group gap="xs">
                        {analysisJobData.required_skills.map((skill: any, index: number) => (
                          <Badge key={index} size="sm" variant="light" color="red">
                            {typeof skill === 'string' ? skill : skill.name || skill}
                          </Badge>
                        ))}
                      </Group>
                    </Box>

                    {/* Preferred Skills */}
                    {analysisJobData.preferred_skills && analysisJobData.preferred_skills.length > 0 && (
                      <Box>
                        <Text fw={500} size="sm" mb="xs" c="blue">Preferred Skills:</Text>
                        <Group gap="xs">
                          {analysisJobData.preferred_skills.map((skill: any, index: number) => (
                            <Badge key={index} size="sm" variant="light" color="blue">
                              {typeof skill === 'string' ? skill : skill.name || skill}
                            </Badge>
                          ))}
                        </Group>
                      </Box>
                    )}

                    {/* Nice-to-Have Skills */}
                    {analysisJobData.nice_to_have_skills && analysisJobData.nice_to_have_skills.length > 0 && (
                      <Box>
                        <Text fw={500} size="sm" mb="xs" c="gray">Nice-to-Have Skills:</Text>
                        <Group gap="xs">
                          {analysisJobData.nice_to_have_skills.map((skill: any, index: number) => (
                            <Badge key={index} size="sm" variant="light" color="gray">
                              {typeof skill === 'string' ? skill : skill.name || skill}
                            </Badge>
                          ))}
                        </Group>
                      </Box>
                    )}
                  </Stack>
                </CardSection>
              </Card>
            )}

            {/* AI Extracted Responsibilities */}
            {analysisJobData.responsibilities && analysisJobData.responsibilities.length > 0 && (
              <Card withBorder>
                <CardSection p="md">
                  <Title order={4} mb="md">🎯 AI Extracted Responsibilities</Title>
                  <Stack gap="xs">
                    {analysisJobData.responsibilities.map((responsibility: string, index: number) => (
                      <Group key={index} align="flex-start">
                        <Text size="sm" c="dimmed" style={{ minWidth: '20px' }}>
                          {index + 1}.
                        </Text>
                        <Text size="sm">{responsibility}</Text>
                      </Group>
                    ))}
                  </Stack>
                </CardSection>
              </Card>
            )}

            {/* Assessment Strategy */}
            {analysisJobData.assessment_strategy && (
              <Card withBorder>
                <CardSection p="md">
                  <Title order={4} mb="md">📊 Assessment Strategy</Title>
                  <Box
                    dangerouslySetInnerHTML={{ __html: analysisJobData.assessment_strategy }}
                    style={{
                      fontSize: '14px',
                      lineHeight: '1.6',
                      color: 'var(--mantine-color-text)'
                    }}
                  />
                </CardSection>
              </Card>
            )}

            {/* Focus Areas */}
            {analysisJobData.focus_areas && analysisJobData.focus_areas.length > 0 && (
              <Card withBorder>
                <CardSection p="md">
                  <Title order={4} mb="md">🔍 Assessment Focus Areas</Title>
                  <Stack gap="xs">
                    {analysisJobData.focus_areas.map((area: any, index: number) => (
                      <Group key={index} align="flex-start">
                        <Text size="sm" c="dimmed" style={{ minWidth: '20px' }}>
                          {index + 1}.
                        </Text>
                        <Text size="sm">{typeof area === 'string' ? area : area.description || area}</Text>
                      </Group>
                    ))}
                  </Stack>
                </CardSection>
              </Card>
            )}

            {/* Risk Areas */}
            {analysisJobData.risk_areas && analysisJobData.risk_areas.length > 0 && (
              <Card withBorder>
                <CardSection p="md">
                  <Title order={4} mb="md">⚠️ Risk Areas</Title>
                  <Stack gap="xs">
                    {analysisJobData.risk_areas.map((risk: any, index: number) => (
                      <Group key={index} align="flex-start">
                        <Text size="sm" c="dimmed" style={{ minWidth: '20px' }}>
                          {index + 1}.
                        </Text>
                        <Text size="sm">{typeof risk === 'string' ? risk : risk.description || risk}</Text>
                      </Group>
                    ))}
                  </Stack>
                </CardSection>
              </Card>
            )}

            {/* Skill Gaps */}
            {analysisJobData.skill_gaps && analysisJobData.skill_gaps.length > 0 && (
              <Card withBorder>
                <CardSection p="md">
                  <Title order={4} mb="md">📉 Identified Skill Gaps</Title>
                  <Stack gap="xs">
                    {analysisJobData.skill_gaps.map((gap: any, index: number) => (
                      <Group key={index} align="flex-start">
                        <Text size="sm" c="dimmed" style={{ minWidth: '20px' }}>
                          {index + 1}.
                        </Text>
                        <Text size="sm">{typeof gap === 'string' ? gap : gap.description || gap}</Text>
                      </Group>
                    ))}
                  </Stack>
                </CardSection>
              </Card>
            )}

            {/* Strengths */}
            {analysisJobData.strengths && analysisJobData.strengths.length > 0 && (
              <Card withBorder>
                <CardSection p="md">
                  <Title order={4} mb="md">💪 Candidate Strengths</Title>
                  <Stack gap="xs">
                    {analysisJobData.strengths.map((strength: any, index: number) => (
                      <Group key={index} align="flex-start">
                        <Text size="sm" c="dimmed" style={{ minWidth: '20px' }}>
                          {index + 1}.
                        </Text>
                        <Text size="sm">{typeof strength === 'string' ? strength : strength.description || strength}</Text>
                      </Group>
                    ))}
                  </Stack>
                </CardSection>
              </Card>
            )}

            {/* Experience Gap Analysis */}
            {analysisJobData.experience_gap_analysis && (
              <Card withBorder>
                <CardSection p="md">
                  <Title order={4} mb="md">📈 Experience Gap Analysis</Title>
                  <Box
                    dangerouslySetInnerHTML={{ __html: analysisJobData.experience_gap_analysis }}
                    style={{
                      fontSize: '14px',
                      lineHeight: '1.6',
                      color: 'var(--mantine-color-text)'
                    }}
                  />
                </CardSection>
              </Card>
            )}

            {/* Metadata */}
            <Card withBorder>
              <CardSection p="md">
                <Title order={4} mb="md">📊 Analysis Metadata</Title>
                <Stack gap="sm">
                  <Group>
                    <Text fw={500} w={120}>Analysis Date:</Text>
                    <Text>{formatDate(analysisJobData.analysis_timestamp || selectedJob.analysis_timestamp)}</Text>
                  </Group>
                  <Group>
                    <Text fw={500} w={120}>Total Skills:</Text>
                    <Text>
                      {(analysisJobData.required_skills?.length || 0) +
                        (analysisJobData.preferred_skills?.length || 0) +
                        (analysisJobData.nice_to_have_skills?.length || 0)} skills
                    </Text>
                  </Group>
                  <Group>
                    <Text fw={500} w={120}>Responsibilities:</Text>
                    <Text>{analysisJobData.responsibilities?.length || 0} items</Text>
                  </Group>
                  <Group>
                    <Text fw={500} w={120}>Focus Areas:</Text>
                    <Text>{analysisJobData.focus_areas?.length || 0} areas</Text>
                  </Group>
                  <Group>
                    <Text fw={500} w={120}>Risk Areas:</Text>
                    <Text>{analysisJobData.risk_areas?.length || 0} risks</Text>
                  </Group>
                </Stack>
              </CardSection>
            </Card>
          </Stack>
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        opened={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Delete Job Description"
        size="sm"
      >
        <Stack gap="md">
          <Text>
            Are you sure you want to delete the job description for{' '}
            <strong>{selectedJob?.title}</strong>?
          </Text>
          <Text size="sm" c="dimmed">
            This action cannot be undone. All analysis data will be permanently removed.
          </Text>
          <Group justify="flex-end" gap="sm">
            <Button variant="light" onClick={() => setDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button
              color="red"
              onClick={() => selectedJob && handleDeleteJob(selectedJob.job_id)}
            >
              Delete
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Page>
  );
}
