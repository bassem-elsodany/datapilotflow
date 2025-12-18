/**
 * ToolCallsList Component for Deep Agent
 * 
 * Displays agent's tool execution history with expandable details.
 * Adapted from: https://github.com/langchain-ai/deep-agents-ui
 */

import { ChevronDown, ChevronUp, Terminal, AlertCircle, Loader2, CheckCircle } from 'lucide-react';
import { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import type { ToolCall } from '@/types/deep-agent';
import { cn } from '@/lib/utils';

interface ToolCallsListProps {
  toolCalls: ToolCall[];
}

interface ToolCallItemProps {
  toolCall: ToolCall;
}

function ToolCallItem({ toolCall }: ToolCallItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const statusIcon = useMemo(() => {
    switch (toolCall.status) {
      case 'completed':
        return <CheckCircle size={16} className="text-green-500" />;
      case 'error':
        return <AlertCircle size={16} className="text-red-500" />;
      case 'pending':
        return <Loader2 size={16} className="text-blue-500 animate-spin" />;
      case 'interrupted':
        return <Terminal size={16} className="text-orange-500" />;
      default:
        return <Terminal size={16} className="text-gray-500" />;
    }
  }, [toolCall.status]);

  const statusColor = useMemo(() => {
    switch (toolCall.status) {
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      case 'pending':
        return 'bg-blue-50 border-blue-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  }, [toolCall.status]);

  return (
    <div className={cn('rounded-lg border p-3', statusColor)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {statusIcon}
          <span className="font-mono text-sm font-medium">{toolCall.name}</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? (
            <ChevronUp size={16} />
          ) : (
            <ChevronDown size={16} />
          )}
        </Button>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="mt-3 space-y-2">
          {/* Arguments */}
          {Object.keys(toolCall.args).length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-600 uppercase mb-1">
                Arguments
              </p>
              <pre className="text-xs bg-white border rounded p-2 overflow-auto max-h-32">
                {JSON.stringify(toolCall.args, null, 2)}
              </pre>
            </div>
          )}

          {/* Result */}
          {toolCall.result && (
            <div>
              <p className="text-xs font-semibold text-gray-600 uppercase mb-1">
                Result
              </p>
              <pre className="text-xs bg-white border rounded p-2 overflow-auto max-h-48 whitespace-pre-wrap">
                {toolCall.result}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ToolCallsList({ toolCalls }: ToolCallsListProps) {
  if (toolCalls.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center">
        <p className="text-sm text-gray-500">
          No tool calls yet. The agent will execute tools as needed.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-3">
      <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-3">
        Tool Executions ({toolCalls.length})
      </h3>
      {toolCalls.map((toolCall) => (
        <ToolCallItem key={toolCall.id} toolCall={toolCall} />
      ))}
    </div>
  );
}

