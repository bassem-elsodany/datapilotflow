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
  IconDotsVertical,
  IconDownload,
  IconEdit,
  IconEye,
  IconPlus,
  IconSearch,
  IconTrash
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

interface Resume {
  candidate_id: string;
  name: string;
  total_experience_years: number;
  calculated_experience_years?: number;
  current_role?: string;
  current_company?: string;
  technical_skills_count: number;
  projects_count: number;
  education_count: number;
  certifications_count: number;
  analysis_timestamp: string;
  resume_source?: string;  // Legacy field
  // Metadata fields
  original_filename?: string;
  file_size?: number;
  file_type?: string;
  upload_timestamp?: string;
  source_type?: string;
  processing_status?: string;
}

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Management', href: paths.dashboard.management.root },
  { label: 'Interview Data', href: paths.dashboard.management.interviewData.root },
  { label: 'Resumes' },
];

export default function ResumesManagement() {
  const navigate = useNavigate();
  const location = useLocation();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [filteredResumes, setFilteredResumes] = useState<Resume[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [viewModalOpen, setViewModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  useEffect(() => {
    loadResumes();
  }, []);

  useEffect(() => {
    filterResumes();
  }, [resumes, searchTerm]);

  const loadResumes = async () => {
    setIsLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('jwt_token');

      if (!token) {
        setError('No authentication token found. Please log in again.');
        setIsLoading(false);
        return;
      }

      const response = await apiUtils.apiRequest('/management/interview/resumes');

      if (response.ok) {
        const data = await response.json();
        const resumesList = data.resumes || [];
        setResumes(resumesList);

        if (resumesList.length === 0) {
          // Don't show error for empty list, just clear any existing error
          setError('');
        }
      } else {
        const errorData = await response.json().catch(() => ({}));

        if (response.status === 401) {
          setError('Authentication failed. Please log in again.');
        } else if (response.status === 403) {
          setError('Access denied. You do not have permission to view resumes.');
        } else {
          setError(`Failed to load resumes: ${errorData.detail || response.statusText}`);
        }
      }
    } catch (error) {
      setError(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const filterResumes = () => {
    if (!searchTerm.trim()) {
      setFilteredResumes(resumes);
      return;
    }

    const filtered = resumes.filter(resume =>
      resume.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      resume.current_role?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      resume.current_company?.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredResumes(filtered);
  };

  const handleDeleteResume = async (candidateId: string) => {
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await apiUtils.apiRequest(`/management/interview/resumes/${candidateId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setResumes(resumes.filter(r => r.candidate_id !== candidateId));
        setDeleteModalOpen(false);
        setSelectedResume(null);
      } else {
        setError('Failed to delete resume');
      }
    } catch (error) {
      setError('Failed to delete resume');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleDateString();
  };

  const getSkillLevelColor = (years: number) => {
    if (years >= 8) return 'green';
    if (years >= 5) return 'blue';
    if (years >= 3) return 'yellow';
    return 'gray';
  };

  // Pagination
  const totalPages = Math.ceil(filteredResumes.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentResumes = filteredResumes.slice(startIndex, endIndex);

  return (
    <Page title="Resumes Management">
      <PageHeader title="Resumes Management" breadcrumbs={breadcrumbs} />

      <LoadingOverlay visible={isLoading} />

      {error && (
        <Alert color="red" title="Error" mb="lg">
          {error}
        </Alert>
      )}

      <Stack gap="lg">
        {/* Header Actions */}
        <Card withBorder>
          <CardSection p="xl">
            <Group justify="space-between" mb="lg">
              <Box>
                <Title order={4}>📄 Candidate Resumes</Title>
                <Text size="sm" c="dimmed">
                  Manage and organize candidate resume data
                </Text>
              </Box>
              <Button
                leftSection={<IconPlus size={16} />}
                onClick={() => navigate(paths.dashboard.apps.interviewCreate + '?step=2')}
              >
                Upload New Resume
              </Button>
            </Group>

            {/* Search and Filters */}
            <Group gap="md">
              <TextInput
                placeholder="Search by name, role, or company..."
                leftSection={<IconSearch size={16} />}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ flex: 1 }}
              />
              <Badge color="blue" variant="light">
                {filteredResumes.length} resumes
              </Badge>
            </Group>
          </CardSection>
        </Card>

        {/* Resumes Table */}
        <Card withBorder>
          <CardSection p="xl">
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Candidate</Table.Th>
                  <Table.Th>Experience</Table.Th>
                  <Table.Th>Current Role</Table.Th>
                  <Table.Th>Skills</Table.Th>
                  <Table.Th>Projects</Table.Th>
                  <Table.Th>File Type</Table.Th>
                  <Table.Th>Last Updated</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {currentResumes.map((resume) => (
                  <Table.Tr key={resume.candidate_id}>
                    <Table.Td>
                      <Box>
                        <Text fw={500}>{resume.name}</Text>
                        {resume.current_company && (
                          <Text size="sm" c="dimmed">
                            {resume.current_company}
                          </Text>
                        )}
                      </Box>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        color={getSkillLevelColor(resume.calculated_experience_years || resume.total_experience_years)}
                        variant="light"
                      >
                        {resume.calculated_experience_years || resume.total_experience_years} years
                        {resume.calculated_experience_years && resume.calculated_experience_years !== resume.total_experience_years && (
                          <Text size="xs" c="dimmed" mt={2}>
                            (stated: {resume.total_experience_years})
                          </Text>
                        )}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">
                        {resume.current_role || 'Not specified'}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <Badge size="sm" variant="light">
                          {resume.technical_skills_count} skills
                        </Badge>
                        <Badge size="sm" variant="light">
                          {resume.education_count} education
                        </Badge>
                        <Badge size="sm" variant="light">
                          {resume.certifications_count} certs
                        </Badge>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Badge size="sm" variant="light">
                        {resume.projects_count} projects
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      {resume.file_type ? (
                        <Badge size="sm" color="blue" variant="light">
                          {resume.file_type.toUpperCase()}
                        </Badge>
                      ) : (
                        <Text size="sm" c="dimmed">Unknown</Text>
                      )}
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">
                        {formatDate(resume.analysis_timestamp)}
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
                              setSelectedResume(resume);
                              setViewModalOpen(true);
                            }}
                          >
                            View Details
                          </Menu.Item>
                          <Menu.Item
                            leftSection={<IconEdit size={16} />}
                            onClick={() => navigate(paths.dashboard.apps.interviewDetails(resume.candidate_id))}
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
                              setSelectedResume(resume);
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

            {currentResumes.length === 0 && !isLoading && (
              <Box ta="center" py="xl">
                <Stack gap="md" align="center">
                  <Text size="lg" c="dimmed">No resumes found</Text>
                  <Text size="sm" c="dimmed">Upload your first resume to get started</Text>
                  <Button
                    leftSection={<IconPlus size={16} />}
                    onClick={() => navigate(paths.dashboard.apps.interviewCreate + '?step=2')}
                    variant="light"
                  >
                    Upload Resume
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

      {/* View Resume Modal */}
      <Modal
        opened={viewModalOpen}
        onClose={() => setViewModalOpen(false)}
        title="Resume Details"
        size="lg"
      >
        {selectedResume && (
          <Stack gap="md">
            <Group>
              <Text fw={500}>Name:</Text>
              <Text>{selectedResume.name}</Text>
            </Group>
            <Group>
              <Text fw={500}>Experience:</Text>
              <Badge color={getSkillLevelColor(selectedResume.calculated_experience_years || selectedResume.total_experience_years)}>
                {selectedResume.calculated_experience_years || selectedResume.total_experience_years} years
                {selectedResume.calculated_experience_years && selectedResume.calculated_experience_years !== selectedResume.total_experience_years && (
                  <Text size="xs" c="dimmed" mt={2}>
                    (stated: {selectedResume.total_experience_years})
                  </Text>
                )}
              </Badge>
            </Group>
            <Group>
              <Text fw={500}>Current Role:</Text>
              <Text>{selectedResume.current_role || 'Not specified'}</Text>
            </Group>
            <Group>
              <Text fw={500}>Company:</Text>
              <Text>{selectedResume.current_company || 'Not specified'}</Text>
            </Group>
            <Group>
              <Text fw={500}>Skills:</Text>
              <Text>{selectedResume.technical_skills_count} technical skills</Text>
            </Group>
            <Group>
              <Text fw={500}>Projects:</Text>
              <Text>{selectedResume.projects_count} projects</Text>
            </Group>
            <Group>
              <Text fw={500}>Education:</Text>
              <Text>{selectedResume.education_count} entries</Text>
            </Group>
            <Group>
              <Text fw={500}>Certifications:</Text>
              <Text>{selectedResume.certifications_count} certifications</Text>
            </Group>
            <Group>
              <Text fw={500}>Last Updated:</Text>
              <Text>{formatDate(selectedResume.analysis_timestamp)}</Text>
            </Group>
            <Group>
              <Text fw={500}>Source:</Text>
              <Text>{selectedResume.resume_source || 'Upload'}</Text>
            </Group>

            {/* File Information Section */}
            <Card withBorder>
              <CardSection p="md">
                <Title order={6} mb="md">📄 File Information</Title>
                <Stack gap="sm">
                  {selectedResume.original_filename && (
                    <Group>
                      <Text size="sm" fw={500} style={{ minWidth: '120px' }}>File Name:</Text>
                      <Text size="sm">{selectedResume.original_filename}</Text>
                    </Group>
                  )}
                  {selectedResume.file_size && (
                    <Group>
                      <Text size="sm" fw={500} style={{ minWidth: '120px' }}>File Size:</Text>
                      <Text size="sm">{`${(selectedResume.file_size / 1024).toFixed(1)} KB`}</Text>
                    </Group>
                  )}
                  {selectedResume.file_type && (
                    <Group>
                      <Text size="sm" fw={500} style={{ minWidth: '120px' }}>File Type:</Text>
                      <Text size="sm">{selectedResume.file_type.toUpperCase()}</Text>
                    </Group>
                  )}
                  {selectedResume.upload_timestamp && (
                    <Group>
                      <Text size="sm" fw={500} style={{ minWidth: '120px' }}>Upload Date:</Text>
                      <Text size="sm">{formatDate(selectedResume.upload_timestamp)}</Text>
                    </Group>
                  )}
                  {selectedResume.source_type && (
                    <Group>
                      <Text size="sm" fw={500} style={{ minWidth: '120px' }}>Source Type:</Text>
                      <Badge size="sm" color="blue" variant="light">
                        {selectedResume.source_type}
                      </Badge>
                    </Group>
                  )}
                  {selectedResume.processing_status && (
                    <Group>
                      <Text size="sm" fw={500} style={{ minWidth: '120px' }}>Status:</Text>
                      <Badge
                        size="sm"
                        color={selectedResume.processing_status === 'completed' ? 'green' : 'yellow'}
                        variant="light"
                      >
                        {selectedResume.processing_status}
                      </Badge>
                    </Group>
                  )}
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
        title="Delete Resume"
        size="sm"
      >
        <Stack gap="md">
          <Text>
            Are you sure you want to delete the resume for{' '}
            <strong>{selectedResume?.name}</strong>?
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
              onClick={() => selectedResume && handleDeleteResume(selectedResume.candidate_id)}
            >
              Delete
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Page>
  );
}
