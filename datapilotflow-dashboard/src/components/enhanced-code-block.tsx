import { ActionIcon, Box, Code, Group, Text, Tooltip } from '@mantine/core';
import { useClipboard } from '@mantine/hooks';
import { IconCheck, IconCopy } from '@tabler/icons-react';

interface EnhancedCodeBlockProps {
  code: string;
  language?: string;
  inline?: boolean;
  showLineNumbers?: boolean;
}

export function EnhancedCodeBlock({
  code,
  language,
  inline = false,
  showLineNumbers = false,
}: EnhancedCodeBlockProps) {
  const clipboard = useClipboard({ timeout: 2000 });

  if (inline) {
    return (
      <Code
        style={{
          backgroundColor: 'var(--mantine-color-gray-1)',
          padding: '2px 6px',
          borderRadius: '4px',
          fontFamily: 'var(--mantine-font-family-monospace)',
          fontSize: '0.9em',
          color: 'var(--mantine-color-indigo-9)',
          border: '1px solid var(--mantine-color-gray-3)',
        }}
      >
        {code}
      </Code>
    );
  }

  const lines = code.split('\n');

  return (
    <Box
      style={{
        position: 'relative',
        margin: '8px 0',
      }}
    >
      {/* Header with language and copy button */}
      <Group
        justify="space-between"
        p={6}
        style={{
          backgroundColor: 'var(--mantine-color-dark-6)',
          borderTopLeftRadius: '6px',
          borderTopRightRadius: '6px',
          borderBottom: '1px solid var(--mantine-color-dark-4)',
        }}
      >
        {language && (
          <Text size="xs" c="gray.4" fw={500} tt="uppercase">
            {language}
          </Text>
        )}
        <Tooltip label={clipboard.copied ? 'Copied!' : 'Copy code'}>
          <ActionIcon
            variant="subtle"
            color={clipboard.copied ? 'green' : 'gray'}
            onClick={() => clipboard.copy(code)}
            size="sm"
          >
            {clipboard.copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
          </ActionIcon>
        </Tooltip>
      </Group>

      {/* Code content */}
      <Box
        style={{
          backgroundColor: 'var(--mantine-color-dark-7)',
          padding: '12px',
          borderBottomLeftRadius: '6px',
          borderBottomRightRadius: '6px',
          overflowX: 'auto',
        }}
      >
        <Code
          block
          style={{
            backgroundColor: 'transparent',
            color: 'var(--mantine-color-gray-1)',
            fontFamily: 'var(--mantine-font-family-monospace)',
            fontSize: '12px',
            lineHeight: '1.5',
            border: 'none',
            padding: 0,
          }}
        >
          {showLineNumbers ? (
            <Box component="table" style={{ borderSpacing: 0, width: '100%' }}>
              <tbody>
                {lines.map((line, i) => (
                  <tr key={i}>
                    <td
                      style={{
                        color: 'var(--mantine-color-gray-6)',
                        paddingRight: '16px',
                        textAlign: 'right',
                        userSelect: 'none',
                        minWidth: '40px',
                        borderRight: '1px solid var(--mantine-color-dark-5)',
                      }}
                    >
                      {i + 1}
                    </td>
                    <td style={{ paddingLeft: '16px' }}>
                      {line || ' '}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Box>
          ) : (
            code
          )}
        </Code>
      </Box>
    </Box>
  );
}
