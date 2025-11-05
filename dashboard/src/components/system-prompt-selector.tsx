/**
 * System Prompt Selector Component
 *
 * Phase 2: Integrated into query input
 *
 * Allows users to:
 * - Select a system prompt before sending a query
 * - See currently selected prompt
 * - Quick access to prompt manager
 * - Tag-based filtering
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
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Edit2,
  X,
  ChevronDown,
  BarChart3,
  Clock,
  Tag,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface SystemPrompt {
  id: string;
  name: string;
  description?: string;
  system_prompt: string;
  tags: string[];
  is_active: boolean;
  usage_count: number;
  created_at?: string;
  updated_at?: string;
  version: number;
}

interface SystemPromptSelectorProps {
  conversationId: string;
  selectedPromptId?: string;
  onPromptSelected?: (promptId: string) => void;
  onOpenManager?: () => void;
  compact?: boolean;
}

export const SystemPromptSelector: React.FC<SystemPromptSelectorProps> = ({
  conversationId,
  selectedPromptId,
  onPromptSelected,
  onOpenManager,
  compact = false,
}) => {
  const [prompts, setPrompts] = useState<SystemPrompt[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState<SystemPrompt | null>(null);
  const [filterTags, setFilterTags] = useState<string[]>([]);
  const { toast } = useToast();

  // Load prompts
  useEffect(() => {
    if (conversationId) {
      loadPrompts();
    }
  }, [conversationId]);

  // Update selected prompt when ID changes
  useEffect(() => {
    if (selectedPromptId && prompts.length > 0) {
      const prompt = prompts.find((p) => p.id === selectedPromptId);
      setSelectedPrompt(prompt || null);
    }
  }, [selectedPromptId, prompts]);

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
    const prompt = prompts.find((p) => p.id === promptId);
    if (prompt) {
      setSelectedPrompt(prompt);
      onPromptSelected?.(promptId);
      toast({
        title: 'Success',
        description: `Selected: ${prompt.name}`,
      });
    }
  };

  const handleClearSelection = () => {
    setSelectedPrompt(null);
    onPromptSelected?.('');
  };

  const allTags = Array.from(new Set(prompts.flatMap((p) => p.tags)));
  const filteredPrompts =
    filterTags.length === 0
      ? prompts
      : prompts.filter((p) => filterTags.some((tag) => p.tags.includes(tag)));

  if (compact) {
    return (
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
          >
            <Edit2 className="h-4 w-4" />
            {selectedPrompt ? selectedPrompt.name : 'System Prompt'}
            {selectedPrompt && (
              <Badge variant="secondary" className="text-xs">
                {selectedPrompt.usage_count > 0 && `${selectedPrompt.usage_count} uses`}
              </Badge>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80">
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">System Prompt</h4>
              {selectedPrompt && (
                <div className="mb-4 p-3 bg-accent rounded-lg">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <p className="font-medium text-sm">{selectedPrompt.name}</p>
                      {selectedPrompt.description && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {selectedPrompt.description}
                        </p>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleClearSelection}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </div>

            <ScrollArea className="h-64">
              <div className="space-y-2 pr-4">
                {filteredPrompts.length === 0 ? (
                  <div className="text-center py-8 text-sm text-muted-foreground">
                    {prompts.length === 0
                      ? 'No prompts available'
                      : 'No prompts match filter'}
                  </div>
                ) : (
                  filteredPrompts.map((prompt) => (
                    <button
                      key={prompt.id}
                      onClick={() => handleSelectPrompt(prompt.id)}
                      className={`w-full text-left p-3 rounded-lg border transition-colors ${
                        selectedPrompt?.id === prompt.id
                          ? 'bg-primary/10 border-primary'
                          : 'hover:bg-accent border-transparent'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="font-medium text-sm">{prompt.name}</p>
                          {prompt.description && (
                            <p className="text-xs text-muted-foreground mt-1">
                              {prompt.description}
                            </p>
                          )}
                        </div>
                        {selectedPrompt?.id === prompt.id && (
                          <div className="text-primary ml-2">✓</div>
                        )}
                      </div>
                    </button>
                  ))
                )}
              </div>
            </ScrollArea>

            <Button
              variant="outline"
              className="w-full"
              size="sm"
              onClick={onOpenManager}
            >
              <Edit2 className="h-4 w-4 mr-2" />
              Manage Prompts
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    );
  }

  // Full view
  return (
    <div className="space-y-4">
      <div>
        <label className="text-sm font-medium mb-2 block">System Prompt</label>
        <div className="flex gap-2">
          <Select
            value={selectedPrompt?.id || ''}
            onValueChange={handleSelectPrompt}
          >
            <SelectTrigger>
              <SelectValue
                placeholder={
                  loading ? 'Loading prompts...' : 'Select a system prompt...'
                }
              />
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
          {selectedPrompt && (
            <Button
              variant="outline"
              size="icon"
              onClick={handleClearSelection}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {selectedPrompt && (
        <div className="p-3 bg-accent rounded-lg space-y-2">
          <h4 className="font-semibold text-sm">{selectedPrompt.name}</h4>
          {selectedPrompt.description && (
            <p className="text-sm text-muted-foreground">
              {selectedPrompt.description}
            </p>
          )}
          {selectedPrompt.tags.length > 0 && (
            <div className="flex gap-2 flex-wrap">
              {selectedPrompt.tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
          {(selectedPrompt.usage_count > 0 || selectedPrompt.created_at) && (
            <div className="flex gap-4 text-xs text-muted-foreground mt-2">
              {selectedPrompt.usage_count > 0 && (
                <div className="flex items-center gap-1">
                  <BarChart3 className="h-3 w-3" />
                  {selectedPrompt.usage_count} uses
                </div>
              )}
              {selectedPrompt.created_at && (
                <div className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  Created {new Date(selectedPrompt.created_at).toLocaleDateString()}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {allTags.length > 0 && (
        <div className="space-y-2">
          <label className="text-sm font-medium">Filter by tags</label>
          <div className="flex gap-2 flex-wrap">
            {allTags.map((tag) => (
              <Badge
                key={tag}
                variant={filterTags.includes(tag) ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => {
                  setFilterTags((prev) =>
                    prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
                  );
                }}
              >
                {tag}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <Button
        variant="outline"
        className="w-full"
        onClick={onOpenManager}
      >
        <Edit2 className="h-4 w-4 mr-2" />
        Manage Prompts
      </Button>
    </div>
  );
};

export default SystemPromptSelector;
