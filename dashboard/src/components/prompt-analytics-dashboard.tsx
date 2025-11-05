/**
 * Prompt Analytics Dashboard Component
 *
 * Phase 3: Advanced Analytics & Insights
 *
 * Features:
 * - Usage statistics and trends
 * - Prompt comparison analysis
 * - Performance metrics
 * - Version history tracking
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  BarChart3,
  TrendingUp,
  Clock,
  GitBranch,
  Target,
  AlertCircle,
  CheckCircle2,
  Eye,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface SystemPrompt {
  id: string;
  name: string;
  description?: string;
  tags: string[];
  usage_count: number;
  version: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

interface AnalyticsData {
  total_prompts: number;
  active_prompts: number;
  total_usage: number;
  average_usage: number;
  prompts: Array<{
    id: string;
    name: string;
    usage_count: number;
    version: number;
    is_active: boolean;
  }>;
}

interface ComparisonData {
  prompt_1: {
    id: string;
    name: string;
    usage_count: number;
    version: number;
  };
  prompt_2: {
    id: string;
    name: string;
    usage_count: number;
    version: number;
  };
  differences: {
    name_differs: boolean;
    prompt_differs: boolean;
    tags_differ: boolean;
    usage_diff: number;
    version_diff: number;
  };
}

interface PromptAnalyticsDashboardProps {
  conversationId: string;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  prompts: SystemPrompt[];
}

export const PromptAnalyticsDashboard: React.FC<PromptAnalyticsDashboardProps> = ({
  conversationId,
  isOpen,
  onOpenChange,
  prompts,
}) => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedPrompt1, setSelectedPrompt1] = useState<string>('');
  const [selectedPrompt2, setSelectedPrompt2] = useState<string>('');
  const [comparison, setComparison] = useState<ComparisonData | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'comparison' | 'history'>(
    'overview'
  );
  const { toast } = useToast();

  // Load analytics
  useEffect(() => {
    if (isOpen && conversationId) {
      loadAnalytics();
    }
  }, [isOpen, conversationId]);

  const loadAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/conversations/${conversationId}/system-prompts/analytics/overview`,
        {
          headers: { 'Content-Type': 'application/json' },
        }
      );
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data.data);
      } else {
        throw new Error('Failed to load analytics');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load analytics',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [conversationId, toast]);

  const handleCompare = async () => {
    if (!selectedPrompt1 || !selectedPrompt2) {
      toast({
        title: 'Error',
        description: 'Select both prompts to compare',
        variant: 'destructive',
      });
      return;
    }

    try {
      const response = await fetch(
        `/api/conversations/${conversationId}/system-prompts/compare`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt_id_1: selectedPrompt1,
            prompt_id_2: selectedPrompt2,
          }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        setComparison(data.data);
        setActiveTab('comparison');
      } else {
        throw new Error('Failed to compare prompts');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to compare',
        variant: 'destructive',
      });
    }
  };

  if (!isOpen) return null;

  const prompt1Data = prompts.find((p) => p.id === selectedPrompt1);
  const prompt2Data = prompts.find((p) => p.id === selectedPrompt2);

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Prompt Analytics & Insights</DialogTitle>
          <DialogDescription>
            Usage statistics, performance metrics, and prompt comparison
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col gap-4">
          {/* Tabs */}
          <div className="flex gap-2 border-b">
            <Button
              variant={activeTab === 'overview' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setActiveTab('overview')}
              className="gap-2"
            >
              <BarChart3 className="h-4 w-4" />
              Overview
            </Button>
            <Button
              variant={activeTab === 'comparison' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setActiveTab('comparison')}
              className="gap-2"
            >
              <TrendingUp className="h-4 w-4" />
              Comparison
            </Button>
          </div>

          <ScrollArea className="flex-1">
            <div className="pr-4 space-y-4">
              {/* Overview Tab */}
              {activeTab === 'overview' && analytics && (
                <div className="space-y-4">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="border rounded-lg p-4">
                      <p className="text-sm text-muted-foreground mb-1">
                        Total Prompts
                      </p>
                      <p className="text-2xl font-bold">
                        {analytics.total_prompts}
                      </p>
                    </div>
                    <div className="border rounded-lg p-4">
                      <p className="text-sm text-muted-foreground mb-1">
                        Active
                      </p>
                      <p className="text-2xl font-bold">
                        {analytics.active_prompts}
                      </p>
                    </div>
                    <div className="border rounded-lg p-4">
                      <p className="text-sm text-muted-foreground mb-1">
                        Total Uses
                      </p>
                      <p className="text-2xl font-bold">
                        {analytics.total_usage}
                      </p>
                    </div>
                    <div className="border rounded-lg p-4">
                      <p className="text-sm text-muted-foreground mb-1">
                        Avg Usage
                      </p>
                      <p className="text-2xl font-bold">
                        {analytics.average_usage.toFixed(1)}
                      </p>
                    </div>
                  </div>

                  {/* Prompts List with Stats */}
                  <div>
                    <h3 className="font-semibold mb-3">Prompt Usage</h3>
                    <div className="space-y-2">
                      {analytics.prompts.map((prompt) => {
                        const promptData = prompts.find(
                          (p) => p.id === prompt.id
                        );
                        return (
                          <div
                            key={prompt.id}
                            className="border rounded-lg p-3 hover:bg-accent/50 transition-colors"
                          >
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <p className="font-medium">
                                    {prompt.name}
                                  </p>
                                  {prompt.is_active ? (
                                    <Badge variant="default" className="text-xs">
                                      Active
                                    </Badge>
                                  ) : (
                                    <Badge
                                      variant="outline"
                                      className="text-xs"
                                    >
                                      Inactive
                                    </Badge>
                                  )}
                                </div>
                                {promptData?.description && (
                                  <p className="text-sm text-muted-foreground">
                                    {promptData.description}
                                  </p>
                                )}
                              </div>

                              <div className="flex items-center gap-4">
                                <div className="text-right">
                                  <div className="flex items-center gap-1 text-sm">
                                    <BarChart3 className="h-4 w-4 text-primary" />
                                    {prompt.usage_count} uses
                                  </div>
                                  <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                                    <GitBranch className="h-3 w-3" />
                                    v{prompt.version}
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* Usage Bar */}
                            {analytics.total_usage > 0 && (
                              <div className="mt-2">
                                <div className="w-full bg-muted rounded-full h-2">
                                  <div
                                    className="bg-primary rounded-full h-2 transition-all"
                                    style={{
                                      width: `${(prompt.usage_count / analytics.total_usage) * 100}%`,
                                    }}
                                  />
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Insights */}
                  <div className="border rounded-lg p-4 bg-accent/50">
                    <h3 className="font-semibold mb-3 flex items-center gap-2">
                      <Eye className="h-4 w-4" />
                      Insights
                    </h3>
                    <ul className="space-y-2 text-sm">
                      {analytics.total_usage === 0 && (
                        <li className="flex items-start gap-2">
                          <AlertCircle className="h-4 w-4 text-warning mt-0.5" />
                          <span>No prompts have been used yet</span>
                        </li>
                      )}
                      {analytics.prompts.some((p) => p.usage_count === 0) && (
                        <li className="flex items-start gap-2">
                          <AlertCircle className="h-4 w-4 text-warning mt-0.5" />
                          <span>
                            {analytics.prompts.filter((p) => p.usage_count === 0)
                              .length}{' '}
                            prompts have not been used
                          </span>
                        </li>
                      )}
                      {analytics.prompts.length > 1 &&
                        analytics.total_usage > 0 && (
                          <li className="flex items-start gap-2">
                            <CheckCircle2 className="h-4 w-4 text-success mt-0.5" />
                            <span>
                              Most used:{' '}
                              <strong>
                                {
                                  analytics.prompts.reduce((a, b) =>
                                    a.usage_count > b.usage_count ? a : b
                                  ).name
                                }
                              </strong>{' '}
                              ({' '}
                              {
                                analytics.prompts.reduce((a, b) =>
                                  a.usage_count > b.usage_count ? a : b
                                ).usage_count
                              }{' '}
                              uses)
                            </span>
                          </li>
                        )}
                      {analytics.active_prompts < analytics.total_prompts && (
                        <li className="flex items-start gap-2">
                          <AlertCircle className="h-4 w-4 text-info mt-0.5" />
                          <span>
                            {analytics.total_prompts -
                              analytics.active_prompts}{' '}
                            inactive prompts
                          </span>
                        </li>
                      )}
                    </ul>
                  </div>
                </div>
              )}

              {/* Comparison Tab */}
              {activeTab === 'comparison' && (
                <div className="space-y-4">
                  {/* Comparison Setup */}
                  <div className="border rounded-lg p-4 bg-accent/50">
                    <h3 className="font-semibold mb-3">Compare Prompts</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium mb-2 block">
                          Prompt 1
                        </label>
                        <Select
                          value={selectedPrompt1}
                          onValueChange={setSelectedPrompt1}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select first prompt" />
                          </SelectTrigger>
                          <SelectContent>
                            {prompts.map((p) => (
                              <SelectItem key={p.id} value={p.id}>
                                {p.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <label className="text-sm font-medium mb-2 block">
                          Prompt 2
                        </label>
                        <Select
                          value={selectedPrompt2}
                          onValueChange={setSelectedPrompt2}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select second prompt" />
                          </SelectTrigger>
                          <SelectContent>
                            {prompts.map((p) => (
                              <SelectItem key={p.id} value={p.id}>
                                {p.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <Button
                      onClick={handleCompare}
                      className="mt-4 w-full"
                    >
                      <TrendingUp className="h-4 w-4 mr-2" />
                      Compare
                    </Button>
                  </div>

                  {/* Comparison Results */}
                  {comparison && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Prompt 1 */}
                      <div className="border rounded-lg p-4">
                        <h4 className="font-semibold mb-3">
                          {comparison.prompt_1.name}
                        </h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground">Usage</span>
                            <span className="font-medium">
                              {comparison.prompt_1.usage_count} uses
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground">
                              Version
                            </span>
                            <span className="font-medium">
                              v{comparison.prompt_1.version}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Prompt 2 */}
                      <div className="border rounded-lg p-4">
                        <h4 className="font-semibold mb-3">
                          {comparison.prompt_2.name}
                        </h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground">Usage</span>
                            <span className="font-medium">
                              {comparison.prompt_2.usage_count} uses
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground">
                              Version
                            </span>
                            <span className="font-medium">
                              v{comparison.prompt_2.version}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Differences */}
                      <div className="md:col-span-2 border rounded-lg p-4 bg-accent/50">
                        <h4 className="font-semibold mb-3">Differences</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                          <div className="space-y-2">
                            {comparison.differences.name_differs && (
                              <div className="flex items-center gap-2 text-warning">
                                <AlertCircle className="h-4 w-4" />
                                <span>Name differs</span>
                              </div>
                            )}
                            {comparison.differences.prompt_differs && (
                              <div className="flex items-center gap-2 text-warning">
                                <AlertCircle className="h-4 w-4" />
                                <span>Content differs</span>
                              </div>
                            )}
                            {comparison.differences.tags_differ && (
                              <div className="flex items-center gap-2 text-warning">
                                <AlertCircle className="h-4 w-4" />
                                <span>Tags differ</span>
                              </div>
                            )}
                          </div>

                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="text-muted-foreground">
                                Usage Difference
                              </span>
                              <span
                                className={
                                  comparison.differences.usage_diff > 0
                                    ? 'text-success'
                                    : 'text-destructive'
                                }
                              >
                                {comparison.differences.usage_diff > 0 ? '+' : ''}
                                {comparison.differences.usage_diff}
                              </span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-muted-foreground">
                                Version Difference
                              </span>
                              <span>
                                {comparison.differences.version_diff > 0
                                  ? `+${comparison.differences.version_diff}`
                                  : comparison.differences.version_diff}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {!comparison && selectedPrompt1 && selectedPrompt2 && (
                    <div className="text-center py-8 text-muted-foreground">
                      Click "Compare" to analyze the differences
                    </div>
                  )}
                </div>
              )}
            </div>
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default PromptAnalyticsDashboard;
