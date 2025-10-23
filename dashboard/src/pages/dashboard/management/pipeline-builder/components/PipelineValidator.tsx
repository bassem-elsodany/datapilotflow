/**
 * Pipeline Validator Component
 * 
 * Shows validation results, errors, warnings, and suggestions for the current pipeline.
 * Helps users understand what's missing or incorrect in their pipeline design.
 */

import React from 'react';
import { Paper, Title, Text, Stack, Group, Alert, List, ThemeIcon } from '@mantine/core';
import { 
  IconCheck, 
  IconX, 
  IconAlertTriangle, 
  IconBulb,
  IconInfoCircle 
} from '@tabler/icons-react';
import { PipelineValidationResult } from '../utils/pipelineRules';

interface PipelineValidatorProps {
  validation: PipelineValidationResult;
}

export function PipelineValidator({ validation }: PipelineValidatorProps) {
  const { isValid, errors, warnings, suggestions } = validation;

  return (
    <Paper shadow="sm" p="md" withBorder>
      <Stack gap="md">
        <Group>
          <Title order={4}>Pipeline Validation</Title>
          {isValid ? (
            <ThemeIcon color="green" size="sm">
              <IconCheck size={16} />
            </ThemeIcon>
          ) : (
            <ThemeIcon color="red" size="sm">
              <IconX size={16} />
            </ThemeIcon>
          )}
        </Group>

        {/* Errors */}
        {errors.length > 0 && (
          <Alert color="red" icon={<IconX size={16} />}>
            <Text fw={600} mb="xs">Errors:</Text>
            <List size="sm">
              {errors.map((error, index) => (
                <List.Item key={index}>{error}</List.Item>
              ))}
            </List>
          </Alert>
        )}

        {/* Warnings */}
        {warnings.length > 0 && (
          <Alert color="yellow" icon={<IconAlertTriangle size={16} />}>
            <Text fw={600} mb="xs">Warnings:</Text>
            <List size="sm">
              {warnings.map((warning, index) => (
                <List.Item key={index}>{warning}</List.Item>
              ))}
            </List>
          </Alert>
        )}

        {/* Suggestions */}
        {suggestions.length > 0 && (
          <Alert color="blue" icon={<IconBulb size={16} />}>
            <Text fw={600} mb="xs">Suggestions:</Text>
            <List size="sm">
              {suggestions.map((suggestion, index) => (
                <List.Item key={index}>{suggestion}</List.Item>
              ))}
            </List>
          </Alert>
        )}

        {/* Success message */}
        {isValid && errors.length === 0 && warnings.length === 0 && (
          <Alert color="green" icon={<IconCheck size={16} />}>
            <Text fw={600}>Pipeline is valid and ready to run!</Text>
            <Text size="sm" c="dimmed">
              Your pipeline follows RAG best practices and should work correctly.
            </Text>
          </Alert>
        )}

        {/* Pipeline flow info */}
        <Alert color="blue" icon={<IconInfoCircle size={16} />}>
          <Text fw={600} mb="xs">RAG Pipeline Flow:</Text>
          <Text size="sm">
            <strong>Data Sources</strong> → <strong>Document Splitter</strong> → <strong>AI Tools</strong> → <strong>Vector Database</strong>
          </Text>
          <Text size="xs" c="dimmed" mt="xs">
            Ensure your pipeline follows this flow for optimal RAG performance.
          </Text>
        </Alert>
      </Stack>
    </Paper>
  );
}
