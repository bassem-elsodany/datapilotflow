/**
 * System Prompt Selector Component
 *
 * Simple selector for choosing a system prompt
 * Shown only when "Enable Knowledge Assistant" is enabled
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { X, Edit2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface SystemPrompt {
  id: string;
  name: string;
  description?: string;
  tags: string[];
  is_active: boolean;
}

interface SystemPromptSelectorProps {
  conversationId: string;
  selectedPromptId?: string;
  onPromptSelected?: (promptId: string) => void;
  onOpenManager?: () => void;
}

export const SystemPromptSelector: React.FC<SystemPromptSelectorProps> = ({
  conversationId,
  selectedPromptId,
  onPromptSelected,
  onOpenManager,
}) => {
  const [prompts, setPrompts] = useState<SystemPrompt[]>([]);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  // Load prompts on mount
  useEffect(() => {
    if (conversationId) {
      loadPrompts();
    }
  }, [conversationId]);

  const loadPrompts = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/conversations/${conversationId}/system-prompts?active_only=true`,
        {
          headers: { 'Content-Type': 'application/json' },
        }
      );
      if (response.ok) {
        const data = await response.json();
        setPrompts(data.data || []);
      }
    } catch (error) {
      console.error('Failed to load system prompts:', error);
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  const handleSelectPrompt = (promptId: string) => {
    onPromptSelected?.(promptId);
    const prompt = prompts.find((p) => p.id === promptId);
    if (prompt) {
      toast({
        title: 'Success',
        description: `Selected: ${prompt.name}`,
      });
    }
  };

  const handleClearSelection = () => {
    onPromptSelected?.('');
  };

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">System Prompt (Optional)</label>
      <div className="flex gap-2">
        <Select
          value={selectedPromptId || ''}
          onValueChange={handleSelectPrompt}
          disabled={loading}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select a system prompt..." />
          </SelectTrigger>
          <SelectContent>
            {prompts.map((prompt) => (
              <SelectItem key={prompt.id} value={prompt.id}>
                {prompt.name}
                {prompt.description && ` - ${prompt.description}`}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {selectedPromptId && (
          <Button
            variant="outline"
            size="icon"
            onClick={handleClearSelection}
            title="Clear selection"
          >
            <X className="h-4 w-4" />
          </Button>
        )}

        <Button
          variant="outline"
          size="icon"
          onClick={onOpenManager}
          title="Manage prompts"
        >
          <Edit2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

export default SystemPromptSelector;
