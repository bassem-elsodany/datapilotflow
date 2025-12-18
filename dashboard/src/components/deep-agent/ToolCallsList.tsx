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
        return <CheckCircle size={18} className="text-emerald-500" />;
      case 'error':
        return <AlertCircle size={18} className="text-rose-500" />;
      case 'pending':
        return <Loader2 size={18} className="text-blue-500 animate-spin" />;
      case 'interrupted':
        return <Terminal size={18} className="text-amber-500" />;
      default:
        return <Terminal size={18} className="text-gray-400" />;
    }
  }, [toolCall.status]);

  const statusColor = useMemo(() => {
    switch (toolCall.status) {
      case 'completed':
        return 'bg-emerald-50 border-emerald-200 hover:border-emerald-300';
      case 'error':
        return 'bg-rose-50 border-rose-200 hover:border-rose-300';
      case 'pending':
        return 'bg-blue-50 border-blue-200 hover:border-blue-300';
      default:
        return 'bg-gray-50 border-gray-200 hover:border-gray-300';
    }
  }, [toolCall.status]);

  const statusBadgeColor = useMemo(() => {
    switch (toolCall.status) {
      case 'completed':
        return 'bg-emerald-100 text-emerald-700';
      case 'error':
        return 'bg-rose-100 text-rose-700';
      case 'pending':
        return 'bg-blue-100 text-blue-700';
      case 'interrupted':
        return 'bg-amber-100 text-amber-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  }, [toolCall.status]);

  return (
    <div className={cn('rounded-lg border p-4 transition-all', statusColor)}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-3 min-w-0 flex-1">
          <div className="flex-shrink-0 mt-1">
            {statusIcon}
          </div>
          <div className="min-w-0 flex-1">
            <span className="font-mono text-lg font-bold text-gray-900 block break-words whitespace-normal">
              {toolCall.name}
            </span>
            <span className={cn('text-xs font-medium px-2.5 py-1.5 rounded inline-block mt-2', statusBadgeColor)}>
              {toolCall.status}
            </span>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex-shrink-0 mt-0"
        >
          {isExpanded ? (
            <ChevronUp size={20} />
          ) : (
            <ChevronDown size={20} />
          )}
        </Button>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="mt-6 space-y-8 pt-6 border-t-2 border-gray-300">
          {/* Arguments */}
          {Object.keys(toolCall.args).length > 0 && (
            <div>
              <div className="mb-4 flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-blue-500" />
                <p className="text-xl font-bold text-gray-900 uppercase tracking-wider">
                  📥 Input Parameters
                </p>
              </div>
              <div className="bg-gray-950 rounded-lg border-3 border-gray-700 overflow-x-auto">
                <pre className="text-lg text-gray-100 font-mono leading-relaxed p-6" style={{ whiteSpace: 'pre', wordWrap: 'normal' }}>
                  <code>{JSON.stringify(toolCall.args, null, 2)}</code>
                </pre>
              </div>
            </div>
          )}

          {/* Result */}
          {toolCall.result && (
            <div>
              <div className="mb-4 flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-emerald-500" />
                <p className="text-xl font-bold text-gray-900 uppercase tracking-wider">
                  📤 Output Result
                </p>
              </div>
              <div className="bg-gray-950 rounded-lg border-3 border-gray-700 overflow-x-auto">
                <pre className="text-lg text-gray-100 font-mono leading-relaxed p-6" style={{ whiteSpace: 'pre', wordWrap: 'normal' }}>
                  <code>{typeof toolCall.result === 'string' ? toolCall.result : JSON.stringify(toolCall.result, null, 2)}</code>
                </pre>
              </div>
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
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <div className="flex items-center gap-2 pb-2 border-b border-gray-200">
        <Terminal size={18} className="text-gray-600" />
        <h3 className="text-sm font-bold text-gray-900 uppercase tracking-widest">
          Tool Executions ({toolCalls.length})
        </h3>
      </div>
      <div className="space-y-3">
        {toolCalls.map((toolCall) => (
          <ToolCallItem key={toolCall.id} toolCall={toolCall} />
        ))}
      </div>
    </div>
  );
}

