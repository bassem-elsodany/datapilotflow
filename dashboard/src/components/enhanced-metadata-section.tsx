import { ActionIcon, Anchor, Badge, Box, Card, Collapse, Divider, Group, Stack, Text, ThemeIcon } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconBrain, IconChevronDown, IconDatabase, IconExternalLink, IconHash, IconInfoCircle, IconScale, IconSparkles } from '@tabler/icons-react';

interface Source {
  url: string;
  chunkIds: string[];
}

interface EnhancedMetadataSectionProps {
  documentCount?: number;
  enhancementStrategy?: string;
  enhancedQueries?: string[];
  sources?: Source[];
  rerankingEnabled?: boolean;
  collapsedByDefault?: boolean;
}

export function EnhancedMetadataSection({
  documentCount,
  enhancementStrategy,
  enhancedQueries = [],
  sources = [],
  rerankingEnabled = false,
  collapsedByDefault = false,
}: EnhancedMetadataSectionProps) {
  // Safety: ensure arrays are never null
  const safeEnhancedQueries = enhancedQueries || [];
  const safeSources = sources || [];

  const [opened, { toggle }] = useDisclosure(!collapsedByDefault);

  const getStrategyLabel = (strategy?: string): string => {
    if (!strategy) return 'Native RAG';
    const labels: { [key: string]: string } = {
      native: 'Native RAG',
      augmented: 'Augmented',
      multi_query: 'Multi-Query',
      hyde: 'HyDE',
      decomposition: 'Decomposition',
    };
    return labels[strategy] || strategy;
  };

  return (
    <Box mt="xs">
      <Card
        withBorder
        padding="xs"
        radius="sm"
        style={{
          backgroundColor: 'var(--mantine-color-gray-0)',
          border: '1px solid var(--mantine-color-gray-3)',
        }}
      >
        {/* Always visible summary */}
        <Group justify="space-between" wrap="nowrap">
          <Group gap="xs" wrap="wrap">
            <Group gap={4}>
              <ThemeIcon size="xs" variant="light" color="gray">
                <IconInfoCircle size={12} />
              </ThemeIcon>
              <Text size="xs" fw={600} c="dimmed">
                METADATA
              </Text>
            </Group>

            {documentCount !== undefined && (
              <Badge
                size="xs"
                variant="light"
                color="blue"
                leftSection={<IconDatabase size={10} />}
              >
                {documentCount} {documentCount === 1 ? 'Doc' : 'Docs'}
              </Badge>
            )}

            {enhancementStrategy && enhancementStrategy !== 'native' && (
              <Badge
                size="xs"
                variant="light"
                color="violet"
                leftSection={<IconBrain size={10} />}
              >
                {getStrategyLabel(enhancementStrategy)}
              </Badge>
            )}

            {rerankingEnabled && (
              <Badge
                size="xs"
                variant="light"
                color="green"
                leftSection={<IconScale size={10} />}
              >
                Reranked
              </Badge>
            )}
          </Group>

          {safeSources.length > 0 && (
            <ActionIcon
              variant="subtle"
              color="gray"
              onClick={toggle}
              size="xs"
            >
              <IconChevronDown
                size={14}
                style={{
                  transform: opened ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.2s ease',
                }}
              />
            </ActionIcon>
          )}
        </Group>

        {/* Expandable sources section */}
        {safeSources.length > 0 && (
          <Collapse in={opened}>
            <Divider my="xs" />

            {/* Query Variants Section */}
            {safeEnhancedQueries.length > 0 && (
              <Box mb="xs">
                <Group gap={4} mb={4}>
                  <ThemeIcon size="xs" variant="light" color="violet">
                    <IconSparkles size={10} />
                  </ThemeIcon>
                  <Text size="xs" fw={600} c="dimmed">
                    QUERY VARIANTS ({safeEnhancedQueries.length})
                  </Text>
                  {enhancementStrategy &&
                    (enhancementStrategy === 'augmented' ||
                      enhancementStrategy === 'multi_query' ||
                      enhancementStrategy === 'decomposition') && (
                      <Badge size="xs" color="blue" variant="light">RRF Fusion</Badge>
                    )}
                </Group>
                <Box
                  p="xs"
                  style={{
                    backgroundColor: 'var(--mantine-color-gray-0)',
                    borderRadius: '4px',
                    border: '1px solid var(--mantine-color-gray-2)',
                    lineHeight: 1.4
                  }}
                >
                  {safeEnhancedQueries.map((query, qIdx) => (
                    <Group key={qIdx} gap={4} mb={qIdx < safeEnhancedQueries.length - 1 ? 6 : 0}>
                      <Badge size="xs" color="grape" variant="dot">
                        {qIdx + 1}
                      </Badge>
                      <Text size="xs" c="dimmed" style={{ flex: 1 }}>
                        {query}
                      </Text>
                    </Group>
                  ))}
                </Box>
              </Box>
            )}

            <Box>
              <Group gap={4} mb={4}>
                <ThemeIcon size="xs" variant="light" color="green">
                  <IconExternalLink size={10} />
                </ThemeIcon>
                <Text size="xs" fw={600} c="dimmed">
                  SOURCES ({safeSources.length})
                </Text>
              </Group>

              <Stack gap={4}>
                {safeSources.map((source, index) => (
                  <Card
                    key={index}
                    padding="xs"
                    radius="sm"
                    withBorder
                    style={{
                      backgroundColor: 'var(--mantine-color-gray-0)',
                      border: '1px solid var(--mantine-color-gray-2)',
                    }}
                  >
                    <Stack gap={4}>
                      <Group gap="xs" wrap="nowrap">
                        <Text size="xs" fw={500} c="dimmed" style={{ minWidth: '20px' }}>
                          {index + 1}.
                        </Text>
                        <Anchor
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          size="xs"
                          c="blue.7"
                          style={{
                            flex: 1,
                            wordBreak: 'break-all',
                            textDecoration: 'none',
                          }}
                        >
                          {source.url}
                        </Anchor>
                        <ActionIcon
                          variant="subtle"
                          color="blue"
                          size="xs"
                          component="a"
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <IconExternalLink size={12} />
                        </ActionIcon>
                      </Group>

                      {source.chunkIds && source.chunkIds.length > 0 && (
                        <Group gap={4} ml="xl">
                          <IconHash size={10} color="var(--mantine-color-gray-6)" />
                          <Text
                            size="xs"
                            c="dimmed"
                            style={{
                              fontFamily: 'monospace',
                              fontSize: '10px',
                            }}
                          >
                            {source.chunkIds.join(', ')}
                          </Text>
                        </Group>
                      )}
                    </Stack>
                  </Card>
                ))}
              </Stack>
            </Box>
          </Collapse>
        )}
      </Card>
    </Box>
  );
}
