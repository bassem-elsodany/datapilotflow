/**
 * Vector Status Page
 *
 * This page provides a monitoring interface for vector database collections,
 * allowing users to inspect schemas, view statistics, and browse records
 * without the high-dimensional vector embeddings.
 */

import {
  useGetCollectionRecords,
  useGetCollections,
  useGetCollectionSchema,
  useGetCollectionStats,
  type CollectionInfo,
  type VectorRecord,
} from '@/api/resources/vectordb';
import {
  Alert,
  Badge,
  Box,
  Button,
  Card,
  Center,
  Grid,
  Group,
  Loader,
  Modal,
  NumberInput,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  ThemeIcon,
  Title,
  Tooltip
} from '@mantine/core';
import {
  IconAlertCircle,
  IconDatabase,
  IconEye,
  IconFileText,
  IconFilter,
  IconInfoCircle,
  IconRefresh,
  IconSearch
} from '@tabler/icons-react';
import { DataTable, DataTableColumn, DataTableSortStatus } from 'mantine-datatable';
import React, { useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from 'recharts';

const VectorStatusPage: React.FC = () => {
  const [selectedCollectionId, setSelectedCollectionId] = useState<string | null>(null);
  const [schemaModalOpened, setSchemaModalOpened] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  // Filter input states (user is typing)
  const [jobIdFilter, setJobIdFilter] = useState('');
  const [sourceUrlFilter, setSourceUrlFilter] = useState('');

  // Applied filter states (after clicking "Apply Filters")
  const [appliedJobIdFilter, setAppliedJobIdFilter] = useState('');
  const [appliedSourceUrlFilter, setAppliedSourceUrlFilter] = useState('');
  const [appliedPageSize, setAppliedPageSize] = useState(50);
  const [filterTimestamp, setFilterTimestamp] = useState(Date.now());

  // Sort state
  const [sortStatus, setSortStatus] = useState<DataTableSortStatus<VectorRecord>>({
    columnAccessor: 'id',
    direction: 'asc',
  });

  const [recordDetailModal, setRecordDetailModal] = useState<{
    opened: boolean;
    record: VectorRecord | null;
  }>({ opened: false, record: null });

  // Fetch collections
  const {
    data: collections,
    isLoading: collectionsLoading,
    error: collectionsError,
    refetch: refetchCollections,
  } = useGetCollections();

  // Fetch selected collection details
  const { data: collectionSchema } = useGetCollectionSchema(
    selectedCollectionId || '',
    !!selectedCollectionId
  );

  const { data: collectionStats, refetch: refetchStats } = useGetCollectionStats(
    selectedCollectionId || '',
    !!selectedCollectionId
  );

  const queryParams = useMemo(() => ({
    limit: appliedPageSize,
    offset: (page - 1) * appliedPageSize,
    job_id: appliedJobIdFilter || undefined,
    source_url: appliedSourceUrlFilter || undefined,
    sort_by: 'created_at',
    sort_order: 'desc' as const,
    _t: filterTimestamp, // Add timestamp to force cache invalidation
  }), [appliedPageSize, page, appliedJobIdFilter, appliedSourceUrlFilter, filterTimestamp]);

  console.log('Query params for records:', queryParams);

  const {
    data: recordsResponse,
    isLoading: recordsLoading,
    refetch: refetchRecords,
  } = useGetCollectionRecords(
    selectedCollectionId || '',
    queryParams,
    !!selectedCollectionId
  );

  // Get selected collection info
  const selectedCollection = collections?.find((c) => c.id === selectedCollectionId);

  // Calculate total pages
  const totalPages = recordsResponse
    ? Math.ceil(recordsResponse.total / appliedPageSize)
    : 0;

  // Sort records based on sortStatus
  const sortedRecords = useMemo(() => {
    if (!recordsResponse?.records) return [];

    const records = [...recordsResponse.records];
    const { columnAccessor, direction } = sortStatus;

    records.sort((a, b) => {
      const aValue = a[columnAccessor as keyof VectorRecord];
      const bValue = b[columnAccessor as keyof VectorRecord];

      // Handle null/undefined values
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return direction === 'asc' ? 1 : -1;
      if (bValue == null) return direction === 'asc' ? -1 : 1;

      // Compare values
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return direction === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return direction === 'asc' ? aValue - bValue : bValue - aValue;
      }

      return 0;
    });

    return records;
  }, [recordsResponse?.records, sortStatus]);

  // Handle collection change
  const handleCollectionChange = (value: string | null) => {
    setSelectedCollectionId(value);
    setPage(1);
    setJobIdFilter('');
    setSourceUrlFilter('');
  };

  // Handle refresh
  const handleRefresh = () => {
    refetchCollections();
    if (selectedCollectionId) {
      refetchStats();
      refetchRecords();
    }
  };

  // Handle filter apply
  const handleApplyFilters = () => {
    console.log('Applying filters:', {
      jobIdFilter,
      sourceUrlFilter,
      pageSize
    });
    // Always reset to page 1 when applying filters
    setPage(1);
    setAppliedJobIdFilter(jobIdFilter);
    setAppliedSourceUrlFilter(sourceUrlFilter);
    setAppliedPageSize(pageSize);

    // Update timestamp to force cache invalidation
    setFilterTimestamp(Date.now());
  };

  // Handle clear filters
  const handleClearFilters = () => {
    setJobIdFilter('');
    setSourceUrlFilter('');
    setPage(1);
    setAppliedJobIdFilter('');
    setAppliedSourceUrlFilter('');
    // Update timestamp to force cache invalidation
    setFilterTimestamp(Date.now());
  };

  // Calculate overview statistics
  const overviewStats = useMemo(() => {
    if (!collections) return null;

    const totalCollections = collections.length;
    const totalRecords = collections.reduce((sum, c) => sum + c.record_count, 0);
    const avgRecordsPerCollection = totalCollections > 0 ? Math.round(totalRecords / totalCollections) : 0;
    const largestCollection = collections.reduce((max, c) => (c.record_count > max.record_count ? c : max), collections[0] || { record_count: 0 });

    return {
      totalCollections,
      totalRecords,
      avgRecordsPerCollection,
      largestCollection,
    };
  }, [collections]);

  // Prepare chart data
  const collectionsChartData = useMemo(() => {
    if (!collections) return [];

    // Sort by record count and take top 10
    return [...collections]
      .sort((a, b) => b.record_count - a.record_count)
      .slice(0, 10)
      .map((c) => ({
        name: c.name.length > 20 ? c.name.substring(0, 20) + '...' : c.name,
        fullName: c.name,
        records: c.record_count,
      }));
  }, [collections]);

  // Job distribution chart data
  const jobDistributionData = useMemo(() => {
    if (!collectionStats?.records_by_job) return [];

    return Object.entries(collectionStats.records_by_job)
      .map(([jobId, count]) => ({
        name: jobId.substring(0, 8) + '...',
        fullJobId: jobId,
        value: count,
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8);
  }, [collectionStats]);

  const COLORS = ['#228be6', '#12b886', '#fab005', '#fa5252', '#be4bdb', '#fd7e14', '#15aabf', '#82c91e'];

  // Define table columns
  const columns: DataTableColumn<VectorRecord>[] = useMemo(
    () => [
      {
        accessor: 'source_url',
        title: 'Source URL',
        width: 350,
        resizable: true,
        sortable: true,
        ellipsis: true,
        render: (record) => (
          <Tooltip label={record.source_url || 'N/A'} openDelay={500}>
            <Text size="xs" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {record.source_url || 'N/A'}
            </Text>
          </Tooltip>
        ),
      },
      {
        accessor: 'title',
        title: 'Title',
        width: 300,
        resizable: true,
        sortable: true,
        ellipsis: true,
        render: (record) => (
          <Tooltip label={record.title || 'N/A'} openDelay={500}>
            <Text size="sm" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {record.title || 'N/A'}
            </Text>
          </Tooltip>
        ),
      },
      {
        accessor: 'chunk_index',
        title: 'Chunk',
        width: 120,
        resizable: true,
        sortable: true,
        textAlign: 'center',
        render: (record) => (
          <Badge size="sm" variant="light">
            {record.chunk_index ?? 'N/A'} / {record.total_chunks ?? 'N/A'}
          </Badge>
        ),
      },
      {
        accessor: 'created_at',
        title: 'Created',
        width: 150,
        resizable: true,
        sortable: true,
        render: (record) => (
          <Text size="xs" c="dimmed">
            {record.created_at ? new Date(record.created_at).toLocaleDateString() : 'N/A'}
          </Text>
        ),
      },
      {
        accessor: 'actions',
        title: 'Actions',
        width: 100,
        textAlign: 'center',
        render: (record) => (
          <Button
            size="xs"
            variant="light"
            leftSection={<IconEye size={14} />}
            onClick={() =>
              setRecordDetailModal({
                opened: true,
                record,
              })
            }
          >
            View
          </Button>
        ),
      },
    ],
    []
  );

  // Render loading state
  if (collectionsLoading) {
    return (
      <Center h={400}>
        <Stack align="center" gap="md">
          <Loader size="lg" />
          <Text c="dimmed">Loading vector collections...</Text>
        </Stack>
      </Center>
    );
  }

  // Render error state
  if (collectionsError) {
    return (
      <Alert icon={<IconAlertCircle size={16} />} title="Error" color="red">
        Failed to load collections: {collectionsError.message}
      </Alert>
    );
  }

  // Render empty state
  if (!collections || collections.length === 0) {
    return (
      <Alert icon={<IconInfoCircle size={16} />} title="No Collections" color="blue">
        No vector collections found. Create a knowledge source configuration and run a job
        to populate collections.
      </Alert>
    );
  }

  return (
    <Stack gap="lg">
      {/* Header */}
      <Group justify="space-between">
        <div>
          <Title order={3}>Vector Status</Title>
          <Text size="sm" c="dimmed">
            Monitor vector collections, schemas, and data
          </Text>
        </div>
        <Button
          leftSection={<IconRefresh size={16} />}
          onClick={handleRefresh}
          variant="light"
        >
          Refresh
        </Button>
      </Group>

      {/* Charts and Statistics */}
      {collections && collections.length > 0 && (
        <Grid>
          {/* Left Side: Charts */}
          <Grid.Col span={{ base: 12, lg: 8 }}>
            <Grid>
              {/* Bar Chart */}
              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card shadow="sm" padding="md" radius="md" withBorder h="100%">
                  <Text fw={500} size="sm" mb="sm">
                    Collections by Record Count (Top 10)
                  </Text>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={collectionsChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e9ecef" />
                      <XAxis
                        dataKey="name"
                        angle={-45}
                        textAnchor="end"
                        height={60}
                        fontSize={11}
                      />
                      <YAxis fontSize={11} />
                      <RechartsTooltip
                        content={({ active, payload }: any) => {
                          if (active && payload && payload.length) {
                            return (
                              <Paper p="xs" withBorder shadow="sm">
                                <Text size="xs" fw={500}>
                                  {payload[0].payload.fullName}
                                </Text>
                                <Text size="xs" c="dimmed">
                                  Records: {payload[0].value?.toLocaleString()}
                                </Text>
                              </Paper>
                            );
                          }
                          return null;
                        }}
                      />
                      <Bar dataKey="records" fill="#228be6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Card>
              </Grid.Col>

              {/* Pie Chart */}
              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card shadow="sm" padding="md" radius="md" withBorder h="100%">
                  <Text fw={500} size="sm" mb="sm">
                    Records Distribution by Job
                  </Text>
                  {selectedCollection && jobDistributionData.length > 0 ? (
                    <>
                      <ResponsiveContainer width="100%" height={160}>
                        <PieChart>
                          <Pie
                            data={jobDistributionData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            outerRadius={60}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {jobDistributionData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <RechartsTooltip
                            content={({ active, payload }: any) => {
                              if (active && payload && payload.length) {
                                return (
                                  <Paper p="xs" withBorder shadow="sm">
                                    <Text size="xs" fw={500}>
                                      Job: {payload[0].payload.fullJobId}
                                    </Text>
                                    <Text size="xs" c="dimmed">
                                      Records: {payload[0].value?.toLocaleString()}
                                    </Text>
                                  </Paper>
                                );
                              }
                              return null;
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                      <Stack gap={4} mt="sm">
                        {jobDistributionData.slice(0, 5).map((item, index) => (
                          <Group key={index} justify="space-between" gap="xs">
                            <Group gap="xs">
                              <Box
                                w={10}
                                h={10}
                                style={{
                                  backgroundColor: COLORS[index % COLORS.length],
                                  borderRadius: 2,
                                }}
                              />
                              <Tooltip label={item.fullJobId}>
                                <Text size="xs" truncate style={{ maxWidth: 120 }}>
                                  {item.name}
                                </Text>
                              </Tooltip>
                            </Group>
                            <Text size="xs" fw={500}>
                              {item.value.toLocaleString()}
                            </Text>
                          </Group>
                        ))}
                        {jobDistributionData.length > 5 && (
                          <Text size="xs" c="dimmed" ta="center">
                            +{jobDistributionData.length - 5} more
                          </Text>
                        )}
                      </Stack>
                    </>
                  ) : (
                    <Center h={220}>
                      <Text size="xs" c="dimmed">
                        {selectedCollection ? 'No job distribution data available' : 'Select a collection to view job distribution'}
                      </Text>
                    </Center>
                  )}
                </Card>
              </Grid.Col>
            </Grid>
          </Grid.Col>

          {/* Right Side: Statistics Cards */}
          {overviewStats && (
            <Grid.Col span={{ base: 12, lg: 4 }}>
              <Stack gap="xs">
                <Card shadow="sm" padding="sm" radius="md" withBorder>
                  <Group justify="apart" mb={4}>
                    <Text size="xs" c="dimmed" fw={500}>
                      Total Collections
                    </Text>
                    <ThemeIcon color="blue" variant="light" radius="md" size="xs">
                      <IconDatabase size={14} />
                    </ThemeIcon>
                  </Group>
                  <Text size="lg" fw={700}>
                    {overviewStats.totalCollections}
                  </Text>
                </Card>

                <Card shadow="sm" padding="sm" radius="md" withBorder>
                  <Group justify="apart" mb={4}>
                    <Text size="xs" c="dimmed" fw={500}>
                      Total Records
                    </Text>
                    <ThemeIcon color="teal" variant="light" radius="md" size="xs">
                      <IconFileText size={14} />
                    </ThemeIcon>
                  </Group>
                  <Text size="lg" fw={700}>
                    {overviewStats.totalRecords.toLocaleString()}
                  </Text>
                </Card>

                <Card shadow="sm" padding="sm" radius="md" withBorder>
                  <Group justify="apart" mb={4}>
                    <Text size="xs" c="dimmed" fw={500}>
                      Largest Collection
                    </Text>
                    <ThemeIcon color="grape" variant="light" radius="md" size="xs">
                      <IconDatabase size={14} />
                    </ThemeIcon>
                  </Group>
                  <Tooltip label={overviewStats.largestCollection?.name || 'N/A'}>
                    <Text size="xs" c="dimmed" truncate mb={2}>
                      {overviewStats.largestCollection?.name || 'N/A'}
                    </Text>
                  </Tooltip>
                  <Text size="md" fw={700}>
                    {overviewStats.largestCollection?.record_count.toLocaleString() || 0}
                  </Text>
                </Card>
              </Stack>
            </Grid.Col>
          )}
        </Grid>
      )}

      {/* Collection Selector */}
      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Stack gap="md">
          <Group justify="space-between">
            <Text fw={500}>Select Collection</Text>
            <Badge variant="light" color="blue">
              {collections.length} {collections.length === 1 ? 'Collection' : 'Collections'}
            </Badge>
          </Group>

          <Select
            placeholder="Select a vector collection"
            data={collections.map((c: CollectionInfo) => ({
              value: c.id,
              label: `${c.name} (${c.record_count.toLocaleString()} records)`,
            }))}
            value={selectedCollectionId}
            onChange={handleCollectionChange}
            leftSection={<IconDatabase size={16} />}
            searchable
            clearable
          />
        </Stack>
      </Card>

      {/* Collection Details */}
      {selectedCollection && (
        <>
          {/* Stats Card */}
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Stack gap="md">
              <Group justify="space-between">
                <Text fw={500}>Collection Information</Text>
                <Button
                  size="xs"
                  variant="light"
                  onClick={() => setSchemaModalOpened(true)}
                >
                  View Schema
                </Button>
              </Group>

              <Group gap="xl">
                <Box>
                  <Text size="xs" c="dimmed">
                    Name
                  </Text>
                  <Text fw={500}>{selectedCollection.name}</Text>
                </Box>
                <Box>
                  <Text size="xs" c="dimmed">
                    Dimension
                  </Text>
                  <Text fw={500}>{selectedCollection.dimension}</Text>
                </Box>
                <Box>
                  <Text size="xs" c="dimmed">
                    Total Records
                  </Text>
                  <Text fw={500}>{selectedCollection.record_count.toLocaleString()}</Text>
                </Box>
                {collectionStats && collectionStats.records_by_job && (
                  <>
                    <Box>
                      <Text size="xs" c="dimmed">
                        Jobs Contributing
                      </Text>
                      <Text fw={500}>
                        {Object.keys(collectionStats.records_by_job).length}
                      </Text>
                    </Box>
                    <Box>
                      <Text size="xs" c="dimmed">
                        Records by Job
                      </Text>
                      <Group gap="xs">
                        {Object.entries(collectionStats.records_by_job).map(
                          ([jobId, count]) => (
                            <Tooltip key={jobId} label={`Job: ${jobId}`}>
                              <Badge variant="light" size="sm">
                                {count.toLocaleString()}
                              </Badge>
                            </Tooltip>
                          )
                        )}
                      </Group>
                    </Box>
                  </>
                )}
              </Group>
            </Stack>
          </Card>

          {/* Filters */}
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Stack gap="md">
              <Group justify="space-between">
                <Text fw={500}>Filters</Text>
                <Button
                  size="xs"
                  variant="subtle"
                  onClick={handleClearFilters}
                >
                  Clear All
                </Button>
              </Group>
              <Stack gap="sm">
                <Group grow>
                  <TextInput
                    label="Job ID"
                    placeholder="Filter by Job ID"
                    value={jobIdFilter}
                    onChange={(e) => setJobIdFilter(e.currentTarget.value)}
                    leftSection={<IconSearch size={16} />}
                  />
                  <TextInput
                    label="Source URL"
                    placeholder="Filter by exact Source URL"
                    description="Enter the complete URL to filter records"
                    value={sourceUrlFilter}
                    onChange={(e) => setSourceUrlFilter(e.currentTarget.value)}
                    leftSection={<IconSearch size={16} />}
                  />
                  <NumberInput
                    label="Page Size"
                    placeholder="Page size"
                    value={pageSize}
                    onChange={(val) => setPageSize(Number(val) || 50)}
                    min={10}
                    max={100}
                    step={10}
                  />
                </Group>
                <Button onClick={handleApplyFilters} fullWidth>
                  Apply Filters
                </Button>
              </Stack>
            </Stack>
          </Card>

          {/* Records Table */}
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            {/* Filter Status Indicator */}
            {(appliedJobIdFilter || appliedSourceUrlFilter) && (
              <Alert
                icon={<IconFilter size={16} />}
                title="Filters Applied"
                color="blue"
                mb="md"
                onClose={() => handleClearFilters()}
                withCloseButton
              >
                {appliedJobIdFilter && (
                  <Text size="sm">Job ID: <Badge variant="light">{appliedJobIdFilter}</Badge></Text>
                )}
                {appliedSourceUrlFilter && (
                  <Text size="sm">Source URL: <Badge variant="light">{appliedSourceUrlFilter}</Badge></Text>
                )}
              </Alert>
            )}

            <DataTable
              minHeight={400}
              withTableBorder
              borderRadius="sm"
              striped
              highlightOnHover
              records={sortedRecords}
              columns={columns}
              fetching={recordsLoading}
              noRecordsText="No records found"
              sortStatus={sortStatus}
              onSortStatusChange={setSortStatus}
              totalRecords={recordsResponse?.total || 0}
              recordsPerPage={appliedPageSize}
              page={page}
              onPageChange={setPage}
              recordsPerPageOptions={[10, 20, 50, 100]}
              onRecordsPerPageChange={(newPageSize) => {
                setPageSize(newPageSize);
                setAppliedPageSize(newPageSize);
                setPage(1);
              }}
              paginationText={({ from, to, totalRecords }) =>
                `Showing ${from} to ${to} of ${totalRecords.toLocaleString()} records`
              }
              recordsPerPageLabel="Records per page"
            />
          </Card>
        </>
      )}

      {/* Schema Modal */}
      <Modal
        opened={schemaModalOpened}
        onClose={() => setSchemaModalOpened(false)}
        title={
          <Group gap="sm">
            <IconDatabase size={20} color="var(--mantine-color-blue-6)" />
            <Text fw={600} size="lg">Collection Schema</Text>
          </Group>
        }
        centered
        size="lg"
        radius="md"
        shadow="xl"
        transitionProps={{
          transition: 'slide-up',
          duration: 300,
          timingFunction: 'ease-out',
        }}
        overlayProps={{
          backgroundOpacity: 0.55,
          blur: 3,
          transitionProps: {
            transition: 'fade',
            duration: 300,
            timingFunction: 'ease-in-out',
          },
        }}
        styles={{
          header: {
            backgroundColor: 'var(--mantine-color-blue-0)',
            borderBottom: '1px solid var(--mantine-color-blue-2)',
            paddingBottom: '16px',
            marginBottom: '16px',
          },
          body: {
            maxHeight: '85vh',
            overflowY: 'auto',
          },
        }}
      >
        {collectionSchema ? (
          <Stack gap="md">
            <Text size="sm" c="dimmed">
              Collection: {collectionSchema.collection_id}
            </Text>
            <Paper withBorder style={{ overflow: 'auto' }}>
              <Table striped>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Field Name</Table.Th>
                    <Table.Th>Type</Table.Th>
                    <Table.Th>Dimension</Table.Th>
                    <Table.Th>Max Length</Table.Th>
                    <Table.Th>Flags</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {collectionSchema.fields.map((field) => (
                    <Table.Tr key={field.name}>
                      <Table.Td>
                        <Text fw={field.is_primary ? 700 : 400}>{field.name}</Text>
                      </Table.Td>
                      <Table.Td>
                        <Badge variant="light" size="sm">
                          {field.type}
                        </Badge>
                      </Table.Td>
                      <Table.Td>{field.dimension ?? 'N/A'}</Table.Td>
                      <Table.Td>{field.max_length ?? 'N/A'}</Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          {field.is_primary && (
                            <Badge size="xs" color="blue">
                              Primary
                            </Badge>
                          )}
                          {field.auto_id && (
                            <Badge size="xs" color="cyan">
                              Auto ID
                            </Badge>
                          )}
                          {field.indexed && (
                            <Badge size="xs" color="green">
                              Indexed
                            </Badge>
                          )}
                        </Group>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Paper>
          </Stack>
        ) : (
          <Center h={200}>
            <Loader />
          </Center>
        )}
      </Modal>

      {/* Record Detail Modal */}
      <Modal
        opened={recordDetailModal.opened}
        onClose={() => setRecordDetailModal({ opened: false, record: null })}
        title={
          <Group gap="sm">
            <IconEye size={20} color="var(--mantine-color-blue-6)" />
            <Text fw={600} size="lg">Record Details</Text>
            {recordDetailModal.record && (
              <Text size="xs" c="dimmed" ff="monospace">
                ({recordDetailModal.record.id})
              </Text>
            )}
          </Group>
        }
        centered
        size="xl"
        radius="md"
        shadow="xl"
        transitionProps={{
          transition: 'slide-up',
          duration: 300,
          timingFunction: 'ease-out',
        }}
        overlayProps={{
          backgroundOpacity: 0.55,
          blur: 3,
          transitionProps: {
            transition: 'fade',
            duration: 300,
            timingFunction: 'ease-in-out',
          },
        }}
        styles={{
          header: {
            backgroundColor: 'var(--mantine-color-blue-0)',
            borderBottom: '1px solid var(--mantine-color-blue-2)',
            paddingBottom: '16px',
            marginBottom: '16px',
          },
          body: {
            maxHeight: '85vh',
            overflowY: 'auto',
          },
        }}
      >
        {recordDetailModal.record && (
          <Stack gap="md">
            {recordDetailModal.record.title && (
              <Box>
                <Text size="xs" c="dimmed" fw={600}>
                  Title
                </Text>
                <Text size="sm">{recordDetailModal.record.title}</Text>
              </Box>
            )}

            {recordDetailModal.record.source_url && (
              <Box>
                <Text size="xs" c="dimmed" fw={600}>
                  Source URL
                </Text>
                <Text size="sm" style={{ wordBreak: 'break-all' }}>
                  {recordDetailModal.record.source_url}
                </Text>
              </Box>
            )}

            {recordDetailModal.record.job_id && (
              <Box>
                <Text size="xs" c="dimmed" fw={600}>
                  Job ID
                </Text>
                <Text size="sm">{recordDetailModal.record.job_id}</Text>
              </Box>
            )}

            {recordDetailModal.record.chunk_index !== null &&
              recordDetailModal.record.chunk_index !== undefined && (
                <Box>
                  <Text size="xs" c="dimmed" fw={600}>
                    Chunk Index
                  </Text>
                  <Text size="sm">{recordDetailModal.record.chunk_index}</Text>
                </Box>
              )}

            {recordDetailModal.record.page_content && (
              <Box>
                <Text size="xs" c="dimmed" fw={600}>
                  Content
                </Text>
                <Paper withBorder p="md" style={{ maxHeight: 300, overflow: 'auto' }}>
                  <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
                    {recordDetailModal.record.page_content}
                  </Text>
                </Paper>
              </Box>
            )}

            {recordDetailModal.record.created_at && (
              <Box>
                <Text size="xs" c="dimmed" fw={600}>
                  Created At
                </Text>
                <Text size="sm">{recordDetailModal.record.created_at}</Text>
              </Box>
            )}

            {recordDetailModal.record.metadata &&
              Object.keys(recordDetailModal.record.metadata).length > 0 && (
                <Box>
                  <Text size="xs" c="dimmed" fw={600}>
                    Additional Metadata
                  </Text>
                  <Paper withBorder p="md">
                    <pre style={{ fontSize: '12px', overflow: 'auto' }}>
                      {JSON.stringify(recordDetailModal.record.metadata, null, 2)}
                    </pre>
                  </Paper>
                </Box>
              )}
          </Stack>
        )}
      </Modal>
    </Stack>
  );
};

export default VectorStatusPage;

