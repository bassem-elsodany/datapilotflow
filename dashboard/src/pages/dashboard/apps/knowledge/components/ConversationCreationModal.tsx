/**
 * Conversation Creation Modal
 *
 * Allows users to choose between two methods for creating a new conversation:
 * 1. Quick Wizard - Step-by-step guided wizard for fast configuration
 * 2. Visual Pipeline - Visual graph-based interface for advanced configuration
 */

import { Modal, Stack, Group, Button, Card, Text, ThemeIcon, Badge } from '@mantine/core';
import { IconWand, IconGitBranch, IconArrowRight } from '@tabler/icons-react';

interface ConversationCreationModalProps {
  opened: boolean;
  onClose: () => void;
  onSelectWizard: () => void;
  onSelectPipeline: () => void;
}

export function ConversationCreationModal({
  opened,
  onClose,
  onSelectWizard,
  onSelectPipeline,
}: ConversationCreationModalProps) {
  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Create New Conversation Session"
      size="lg"
      centered
      radius="md"
    >
      <Stack gap="lg">
        <Text size="sm" c="dimmed">
          Choose how you'd like to configure your conversation session:
        </Text>

        {/* Quick Wizard Option */}
        <Card
          withBorder
          padding="lg"
          radius="md"
          style={{
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            border: '2px solid transparent',
            '&:hover': {
              borderColor: 'var(--mantine-color-blue-5)',
              backgroundColor: 'var(--mantine-color-blue-0)',
            },
          }}
          onClick={onSelectWizard}
        >
          <Group justify="space-between" align="flex-start">
            <div>
              <Group gap="sm" mb="xs">
                <ThemeIcon
                  size={32}
                  radius="md"
                  variant="light"
                  color="blue"
                >
                  <IconWand size={18} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="md">Quick Wizard</Text>
                  <Badge size="sm" variant="light" color="blue">
                    Recommended for most users
                  </Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mt="sm">
                Step-by-step guided wizard to quickly configure your conversation with sensible defaults. Perfect for getting started fast.
              </Text>
              <Group gap="xs" mt="md">
                <Badge variant="dot" size="sm">Fast Setup</Badge>
                <Badge variant="dot" size="sm">Guided Steps</Badge>
                <Badge variant="dot" size="sm">Defaults Included</Badge>
              </Group>
            </div>
            <IconArrowRight size={20} color="var(--mantine-color-blue-6)" style={{ marginTop: 8 }} />
          </Group>
        </Card>

        {/* Visual Pipeline Option */}
        <Card
          withBorder
          padding="lg"
          radius="md"
          style={{
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            border: '2px solid transparent',
            '&:hover': {
              borderColor: 'var(--mantine-color-teal-5)',
              backgroundColor: 'var(--mantine-color-teal-0)',
            },
          }}
          onClick={onSelectPipeline}
        >
          <Group justify="space-between" align="flex-start">
            <div>
              <Group gap="sm" mb="xs">
                <ThemeIcon
                  size={32}
                  radius="md"
                  variant="light"
                  color="teal"
                >
                  <IconGitBranch size={18} />
                </ThemeIcon>
                <div>
                  <Text fw={600} size="md">Visual Pipeline</Text>
                  <Badge size="sm" variant="light" color="teal">
                    For advanced users
                  </Badge>
                </div>
              </Group>
              <Text size="sm" c="dimmed" mt="sm">
                Visual graph-based interface for advanced configuration. Design your conversation pipeline with full control over each component.
              </Text>
              <Group gap="xs" mt="md">
                <Badge variant="dot" size="sm">Full Control</Badge>
                <Badge variant="dot" size="sm">Visual Design</Badge>
                <Badge variant="dot" size="sm">Advanced Options</Badge>
              </Group>
            </div>
            <IconArrowRight size={20} color="var(--mantine-color-teal-6)" style={{ marginTop: 8 }} />
          </Group>
        </Card>

        {/* Footer Note */}
        <Text size="xs" c="dimmed" ta="center">
          You can switch between methods or modify your configuration later.
        </Text>
      </Stack>
    </Modal>
  );
}
