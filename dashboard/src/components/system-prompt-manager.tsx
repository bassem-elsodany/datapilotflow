/**
 * System Prompt Manager Component
 *
 * Phase 2: UI Manager & Integration
 *
 * Allows users to:
 * - Create new system prompts
 * - Edit existing prompts
 * - Delete prompts
 * - View and filter prompts by tags
 * - Use quick presets
 * - Track prompt usage statistics
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Plus,
  Edit2,
  Trash2,
  Copy,
  Check,
  X,
  ChevronDown,
  ChevronUp,
  Eye,
  EyeOff,
  Tag,
  BarChart3,
  Clock,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

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

interface SystemPromptManagerProps {
  conversationId: string;
  onPromptSelected?: (prompt: SystemPrompt) => void;
  selectedPromptId?: string;
}

const QUICK_PRESETS = [
  {
    name: 'Code Reviewer',
    description: 'Reviews code for quality, performance, and best practices',
    system_prompt: `You are an expert code reviewer with deep knowledge of multiple programming languages and design patterns. Your role is to:

1. **Code Quality**: Assess code clarity, maintainability, and adherence to best practices
2. **Performance**: Identify potential bottlenecks and optimization opportunities
3. **Security**: Flag potential security vulnerabilities and recommend fixes
4. **Testing**: Suggest improvements to test coverage and test quality
5. **Documentation**: Ensure code is well-documented

When reviewing code:
- Be constructive and educational
- Provide specific, actionable feedback
- Include code examples for improvements
- Explain the reasoning behind suggestions
- Acknowledge good practices and patterns

Format your review as:
## Summary
[1-2 sentence overview]

## Strengths
[What the code does well]

## Issues & Recommendations
[Organized by category: Performance, Security, Maintainability, etc.]

## Questions
[Any clarifications needed]`,
    tags: ['code-review', 'quality', 'performance'],
  },
  {
    name: 'Document Summarizer',
    description: 'Summarizes documents into concise, actionable summaries',
    system_prompt: `You are an expert document summarizer skilled at extracting key information and presenting it clearly.

Your task is to summarize documents by:

1. **Key Points**: Extract the most important information
2. **Context**: Provide necessary background information
3. **Actions**: Identify any recommended actions or next steps
4. **Decisions**: Highlight important decisions or conclusions

When summarizing:
- Be concise but comprehensive
- Preserve critical details
- Use clear structure with headers
- Include relevant metrics or data points
- Flag any ambiguities or unclear sections

Format your summary as:
## Executive Summary
[1 paragraph overview]

## Key Points
- [Point 1]
- [Point 2]
- [Point 3]

## Important Details
[Relevant specifics, data, or context]

## Recommended Actions
[Next steps or follow-up items]

## Questions/Clarifications Needed
[Any unclear sections]`,
    tags: ['summarization', 'documentation', 'analysis'],
  },
  {
    name: 'Technical Writer',
    description: 'Creates clear, professional technical documentation',
    system_prompt: `You are an expert technical writer skilled at creating clear, professional documentation.

Your role is to:

1. **Clarity**: Explain complex concepts in accessible language
2. **Structure**: Organize information logically with clear headings
3. **Examples**: Include practical examples and use cases
4. **Accessibility**: Consider audience knowledge level
5. **Completeness**: Cover all relevant aspects

When writing documentation:
- Use active voice and clear language
- Avoid unnecessary jargon
- Include code examples where relevant
- Provide links to related resources
- Format for easy scanning (bullets, headings, emphasis)

Format your documentation as:
## Overview
[What this is and why it matters]

## Prerequisites
[What users need to know/have]

## Step-by-Step Guide
[Clear numbered steps with examples]

## Common Issues & Troubleshooting
[FAQ and solutions]

## Next Steps
[What users can do next]

## Additional Resources
[Links to related docs]`,
    tags: ['documentation', 'technical-writing', 'guides'],
  },
];

export const SystemPromptManager: React.FC<SystemPromptManagerProps> = ({
  conversationId,
  onPromptSelected,
  selectedPromptId,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [prompts, setPrompts] = useState<SystemPrompt[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState<SystemPrompt | null>(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const [expandedPromptId, setExpandedPromptId] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [showPresets, setShowPresets] = useState(true);
  const [filterTags, setFilterTags] = useState<string[]>([]);
  const [showInactive, setShowInactive] = useState(false);
  const { toast } = useToast();

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    system_prompt: '',
    tags: [] as string[],
  });
  const [newTag, setNewTag] = useState('');

  // Load prompts
  useEffect(() => {
    if (isOpen && conversationId) {
      loadPrompts();
    }
  }, [isOpen, conversationId]);

  const loadPrompts = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/conversations/${conversationId}/system-prompts?active_only=${!showInactive}`,
        {
          headers: { 'Content-Type': 'application/json' },
        }
      );
      if (response.ok) {
        const data = await response.json();
        setPrompts(data.data || []);
      } else {
        toast({
          title: 'Error',
          description: 'Failed to load system prompts',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load system prompts',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [conversationId, showInactive, toast]);

  const handleCreateOrUpdate = async () => {
    if (!formData.name || !formData.system_prompt) {
      toast({
        title: 'Validation Error',
        description: 'Name and prompt content are required',
        variant: 'destructive',
      });
      return;
    }

    try {
      const url = selectedPrompt
        ? `/api/conversations/${conversationId}/system-prompts/${selectedPrompt.id}`
        : `/api/conversations/${conversationId}/system-prompts`;

      const method = selectedPrompt ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          description: formData.description,
          system_prompt: formData.system_prompt,
          tags: formData.tags,
        }),
      });

      if (response.ok) {
        toast({
          title: 'Success',
          description: selectedPrompt ? 'Prompt updated' : 'Prompt created',
        });
        setSelectedPrompt(null);
        setIsEditMode(false);
        setFormData({ name: '', description: '', system_prompt: '', tags: [] });
        loadPrompts();
      } else {
        throw new Error('Failed to save prompt');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to save prompt',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async (promptId: string) => {
    try {
      const response = await fetch(
        `/api/conversations/${conversationId}/system-prompts/${promptId}`,
        { method: 'DELETE' }
      );

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Prompt deleted',
        });
        loadPrompts();
        setDeleteConfirm(null);
      } else {
        throw new Error('Failed to delete prompt');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to delete prompt',
        variant: 'destructive',
      });
    }
  };

  const handleSelectPrompt = async (prompt: SystemPrompt) => {
    try {
      const response = await fetch(
        `/api/conversations/${conversationId}/system-prompts/${prompt.id}/select`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt_id: prompt.id }),
        }
      );

      if (response.ok) {
        toast({
          title: 'Success',
          description: `Selected prompt: ${prompt.name}`,
        });
        onPromptSelected?.(prompt);
        setIsOpen(false);
      } else {
        throw new Error('Failed to select prompt');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to select prompt',
        variant: 'destructive',
      });
    }
  };

  const handleAddPreset = async (preset: typeof QUICK_PRESETS[0]) => {
    try {
      const response = await fetch(
        `/api/conversations/${conversationId}/system-prompts`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: preset.name,
            description: preset.description,
            system_prompt: preset.system_prompt,
            tags: preset.tags,
          }),
        }
      );

      if (response.ok) {
        toast({
          title: 'Success',
          description: `Added preset: ${preset.name}`,
        });
        loadPrompts();
      } else {
        throw new Error('Failed to add preset');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to add preset',
        variant: 'destructive',
      });
    }
  };

  const handleEditPrompt = (prompt: SystemPrompt) => {
    setSelectedPrompt(prompt);
    setFormData({
      name: prompt.name,
      description: prompt.description || '',
      system_prompt: prompt.system_prompt,
      tags: prompt.tags,
    });
    setIsEditMode(true);
  };

  const handleAddTag = () => {
    if (newTag && !formData.tags.includes(newTag)) {
      setFormData({
        ...formData,
        tags: [...formData.tags, newTag],
      });
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter((tag) => tag !== tagToRemove),
    });
  };

  const filteredPrompts = prompts.filter((prompt) => {
    if (filterTags.length === 0) return true;
    return filterTags.some((tag) => prompt.tags.includes(tag));
  });

  const allTags = Array.from(new Set(prompts.flatMap((p) => p.tags)));

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(true)}
        className="gap-2"
      >
        <Edit2 className="h-4 w-4" />
        System Prompts
      </Button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>System Prompt Manager</DialogTitle>
            <DialogDescription>
              Create, edit, and manage system prompts for this conversation
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-hidden flex flex-col gap-4">
            {/* Tabs/Controls */}
            <div className="flex gap-2 items-center">
              <Button
                variant={isEditMode ? 'default' : 'outline'}
                size="sm"
                onClick={() => {
                  setIsEditMode(true);
                  setSelectedPrompt(null);
                  setFormData({
                    name: '',
                    description: '',
                    system_prompt: '',
                    tags: [],
                  });
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                New Prompt
              </Button>

              {isEditMode && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setIsEditMode(false);
                    setSelectedPrompt(null);
                    setFormData({
                      name: '',
                      description: '',
                      system_prompt: '',
                      tags: [],
                    });
                  }}
                >
                  <X className="h-4 w-4 mr-2" />
                  Cancel
                </Button>
              )}

              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowPresets(!showPresets)}
              >
                Presets ({QUICK_PRESETS.length})
              </Button>

              <div className="ml-auto flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowInactive(!showInactive)}
                >
                  {showInactive ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            {/* Filter Tags */}
            {allTags.length > 0 && (
              <div className="flex gap-2 flex-wrap items-center">
                <span className="text-sm text-muted-foreground flex items-center gap-1">
                  <Tag className="h-4 w-4" />
                  Filter:
                </span>
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
                {filterTags.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setFilterTags([])}
                  >
                    Clear
                  </Button>
                )}
              </div>
            )}

            <ScrollArea className="flex-1">
              <div className="space-y-4 pr-4">
                {/* Edit Form */}
                {isEditMode && (
                  <div className="border rounded-lg p-4 bg-accent/50">
                    <h3 className="font-semibold mb-4">
                      {selectedPrompt ? 'Edit Prompt' : 'Create New Prompt'}
                    </h3>

                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium">Name *</label>
                        <Input
                          value={formData.name}
                          onChange={(e) =>
                            setFormData({ ...formData, name: e.target.value })
                          }
                          placeholder="e.g., Code Reviewer"
                        />
                      </div>

                      <div>
                        <label className="text-sm font-medium">Description</label>
                        <Input
                          value={formData.description}
                          onChange={(e) =>
                            setFormData({ ...formData, description: e.target.value })
                          }
                          placeholder="What does this prompt do?"
                        />
                      </div>

                      <div>
                        <label className="text-sm font-medium">System Prompt *</label>
                        <Textarea
                          value={formData.system_prompt}
                          onChange={(e) =>
                            setFormData({ ...formData, system_prompt: e.target.value })
                          }
                          placeholder="Enter the system prompt instructions..."
                          rows={12}
                          className="font-mono text-sm"
                        />
                      </div>

                      <div>
                        <label className="text-sm font-medium">Tags</label>
                        <div className="flex gap-2 mb-2">
                          <Input
                            value={newTag}
                            onChange={(e) => setNewTag(e.target.value)}
                            placeholder="Add a tag..."
                            onKeyPress={(e) => {
                              if (e.key === 'Enter') {
                                e.preventDefault();
                                handleAddTag();
                              }
                            }}
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleAddTag}
                          >
                            Add
                          </Button>
                        </div>
                        {formData.tags.length > 0 && (
                          <div className="flex gap-2 flex-wrap">
                            {formData.tags.map((tag) => (
                              <Badge
                                key={tag}
                                variant="secondary"
                                className="gap-1"
                              >
                                {tag}
                                <button
                                  onClick={() => handleRemoveTag(tag)}
                                  className="ml-1 hover:text-destructive"
                                >
                                  ×
                                </button>
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>

                      <div className="flex gap-2">
                        <Button onClick={handleCreateOrUpdate} className="gap-2">
                          <Check className="h-4 w-4" />
                          {selectedPrompt ? 'Update Prompt' : 'Create Prompt'}
                        </Button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Quick Presets */}
                {showPresets && (
                  <div className="border rounded-lg p-4">
                    <h3 className="font-semibold mb-4">Quick Presets</h3>
                    <div className="space-y-2">
                      {QUICK_PRESETS.map((preset) => (
                        <div
                          key={preset.name}
                          className="border rounded p-3 hover:bg-accent/50 transition-colors"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="font-medium">{preset.name}</p>
                              <p className="text-sm text-muted-foreground">
                                {preset.description}
                              </p>
                              <div className="flex gap-2 mt-2 flex-wrap">
                                {preset.tags.map((tag) => (
                                  <Badge key={tag} variant="secondary" className="text-xs">
                                    {tag}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleAddPreset(preset)}
                            >
                              <Plus className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Prompts List */}
                <div className="space-y-2">
                  {filteredPrompts.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      {prompts.length === 0
                        ? 'No prompts yet. Create one or add a preset!'
                        : 'No prompts match your filter'}
                    </div>
                  ) : (
                    filteredPrompts.map((prompt) => (
                      <div
                        key={prompt.id}
                        className={cn(
                          'border rounded-lg p-4 hover:bg-accent/50 transition-colors',
                          selectedPromptId === prompt.id && 'border-primary bg-primary/5'
                        )}
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <p className="font-semibold">{prompt.name}</p>
                              {!prompt.is_active && (
                                <Badge variant="outline" className="text-xs">
                                  Inactive
                                </Badge>
                              )}
                            </div>
                            {prompt.description && (
                              <p className="text-sm text-muted-foreground mt-1">
                                {prompt.description}
                              </p>
                            )}
                            <div className="flex gap-2 mt-2 flex-wrap">
                              {prompt.tags.map((tag) => (
                                <Badge key={tag} variant="secondary" className="text-xs">
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                            {(prompt.usage_count > 0 || prompt.created_at) && (
                              <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                                {prompt.usage_count > 0 && (
                                  <div className="flex items-center gap-1">
                                    <BarChart3 className="h-3 w-3" />
                                    {prompt.usage_count} uses
                                  </div>
                                )}
                                {prompt.created_at && (
                                  <div className="flex items-center gap-1">
                                    <Clock className="h-3 w-3" />
                                    {new Date(prompt.created_at).toLocaleDateString()}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>

                          <div className="flex gap-2 flex-shrink-0">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                setExpandedPromptId(
                                  expandedPromptId === prompt.id ? null : prompt.id
                                )
                              }
                            >
                              {expandedPromptId === prompt.id ? (
                                <ChevronUp className="h-4 w-4" />
                              ) : (
                                <ChevronDown className="h-4 w-4" />
                              )}
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleSelectPrompt(prompt)}
                              className={selectedPromptId === prompt.id ? 'bg-primary text-primary-foreground' : ''}
                            >
                              {selectedPromptId === prompt.id ? (
                                <Check className="h-4 w-4" />
                              ) : (
                                <Copy className="h-4 w-4" />
                              )}
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleEditPrompt(prompt)}
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setDeleteConfirm(prompt.id)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </div>
                        </div>

                        {/* Expanded Content */}
                        {expandedPromptId === prompt.id && (
                          <div className="mt-4 pt-4 border-t">
                            <p className="text-sm whitespace-pre-wrap font-mono bg-muted p-3 rounded max-h-64 overflow-auto">
                              {prompt.system_prompt}
                            </p>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </ScrollArea>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Prompt?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. The prompt will be permanently deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogAction
            onClick={() => {
              if (deleteConfirm) {
                handleDelete(deleteConfirm);
              }
            }}
            className="bg-destructive"
          >
            Delete
          </AlertDialogAction>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

export default SystemPromptManager;
