/**
 * Reusable footer for node configuration forms
 */

import { Button, Group } from '@mantine/core';
import { IconCheck } from '@tabler/icons-react';

interface NodeConfigFooterProps {
  onSave: () => void;
  onClose: () => void;
}

export function NodeConfigFooter({ onSave, onClose }: NodeConfigFooterProps) {
  return (
    <Group justify="flex-end" mt="md">
      <Button variant="default" onClick={onClose}>
        Cancel
      </Button>
      <Button
        color="green"
        leftSection={<IconCheck size={16} />}
        onClick={onSave}
      >
        Save Configuration
      </Button>
    </Group>
  );
}
