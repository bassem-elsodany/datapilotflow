/**
 * ToolCallsList Component for Deep Agent
 *
 * Displays agent's tool execution history with expandable details.
 * Adapted from: https://github.com/langchain-ai/deep-agents-ui
 */

import { ChevronDown, ChevronUp, Terminal, AlertCircle, Loader2, CheckCircle, Copy } from 'lucide-react';
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

interface CodeBlockProps {
  content: string;
  label: string;
  color: 'blue' | 'emerald' | 'rose';
}

function CodeBlock({ content, label, color }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const labelBgColors = {
    blue: 'bg-blue-50 text-blue-900 border-blue-200',
    emerald: 'bg-emerald-50 text-emerald-900 border-emerald-200',
    rose: 'bg-rose-50 text-rose-900 border-rose-200',
  };

  const codeBgColors = {
    blue: 'bg-blue-950 border-blue-800',
    emerald: 'bg-emerald-950 border-emerald-800',
    rose: 'bg-rose-950 border-rose-800',
  };

  const dotColors = {
    blue: 'bg-blue-500',
    emerald: 'bg-emerald-500',
    rose: 'bg-rose-500',
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div>
      <div className={`flex items-center justify-between gap-3 border-b-2 px-5 py-4 rounded-t-lg ${labelBgColors[color]}`}>
        <div className="flex items-center gap-3">
          <div className={`h-3 w-3 rounded-full ${dotColors[color]}`} />
          <h4 className="font-bold text-base">{label}</h4>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-8 w-8 p-0"
          title={copied ? 'Copied!' : 'Copy to clipboard'}
        >
          <Copy size={16} className={copied ? 'text-green-600' : 'text-gray-500 hover:text-gray-700'} />
        </Button>
      </div>
      <div className={`${codeBgColors[color]} rounded-b-lg border-2 border-t-0 overflow-hidden`}>
        <div className="px-6 py-6 overflow-x-auto max-h-96">
          <pre
            className="text-gray-100 font-mono whitespace-pre-wrap break-words"
            style={{
              fontSize: '13px',
              lineHeight: '1.7',
              letterSpacing: '0.3px',
            }}
          >
            {content}
          </pre>
        </div>
      </div>
    </div>
  );
}

function ToolCallItem({ toolCall }: ToolCallItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const statusIcon = useMemo(() => {
    switch (toolCall.status) {
      case 'completed':
        return <CheckCircle size={20} className="text-emerald-500" />;
      case 'error':
        return <AlertCircle size={20} className="text-rose-500" />;
      case 'pending':
        return <Loader2 size={20} className="text-blue-500 animate-spin" />;
      case 'interrupted':
        return <Terminal size={20} className="text-amber-500" />;
      default:
        return <Terminal size={20} className="text-gray-400" />;
    }
  }, [toolCall.status]);

  const statusColor = useMemo(() => {
    switch (toolCall.status) {
      case 'completed':
        return 'bg-white border-emerald-200 hover:border-emerald-300 hover:shadow-md';
      case 'error':
        return 'bg-white border-rose-200 hover:border-rose-300 hover:shadow-md';
      case 'pending':
        return 'bg-white border-blue-200 hover:border-blue-300 hover:shadow-md';
      default:
        return 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-md';
    }
  }, [toolCall.status]);

  const headerBgColor = useMemo(() => {
    switch (toolCall.status) {
      case 'completed':
        return 'bg-emerald-50/50';
      case 'error':
        return 'bg-rose-50/50';
      case 'pending':
        return 'bg-blue-50/50';
      default:
        return 'bg-gray-50/50';
    }
  }, [toolCall.status]);

  const statusBadgeColor = useMemo(() => {
    switch (toolCall.status) {
      case 'completed':
        return 'bg-emerald-100 text-emerald-800';
      case 'error':
        return 'bg-rose-100 text-rose-800';
      case 'pending':
        return 'bg-blue-100 text-blue-800';
      case 'interrupted':
        return 'bg-amber-100 text-amber-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }, [toolCall.status]);

  const jsonInputStr = JSON.stringify(toolCall.args, null, 2);
  const jsonOutputStr =
    typeof toolCall.result === 'string'
      ? toolCall.result
      : JSON.stringify(toolCall.result, null, 2);

  return (
    <div className={cn('rounded-lg border-2 transition-all shadow-sm', statusColor)}>
      {/* Header */}
      <div className={`flex items-center justify-between gap-4 px-5 py-4 ${headerBgColor}`}>
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="flex-shrink-0">{statusIcon}</div>
          <div className="min-w-0 flex-1">
            <h3 className="font-bold text-gray-900 text-base truncate">
              {toolCall.name}
            </h3>
            <span
              className={cn(
                'text-xs font-semibold px-2.5 py-1 rounded-md inline-block mt-1.5',
                statusBadgeColor
              )}
            >
              {toolCall.status.toUpperCase()}
            </span>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex-shrink-0 h-8 w-8 p-0 hover:bg-gray-100"
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
        <div className="px-5 py-6 border-t-2 border-gray-100 space-y-6 bg-gray-50/30">
          {/* Arguments */}
          {Object.keys(toolCall.args).length > 0 && (
            <CodeBlock content={jsonInputStr} label="Input Parameters" color="blue" />
          )}

          {/* Result */}
          {toolCall.result && (
            <CodeBlock content={jsonOutputStr} label="Output Result" color="emerald" />
          )}

          {/* Error Message */}
          {toolCall.status === 'error' && toolCall.errorMessage && (
            <div className="bg-rose-50 border-l-4 border-rose-500 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle size={18} className="text-rose-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold text-rose-900 mb-1 text-sm">Error Details</h4>
                  <p className="text-rose-800 text-sm leading-relaxed">{toolCall.errorMessage}</p>
                </div>
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
      <div className="flex h-full items-center justify-center p-8 text-center bg-gradient-to-br from-gray-50 to-gray-100">
        <div>
          <Terminal size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-600 text-base font-medium">
            No tool calls yet. The agent will execute tools as needed.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      {/* Header */}
      <div className="sticky top-0 bg-white/80 backdrop-blur-sm rounded-xl p-4 mb-6 border border-gray-200/50 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Terminal size={22} className="text-blue-600" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Tool Executions</h2>
            <p className="text-sm text-gray-600">
              {toolCalls.length} {toolCalls.length === 1 ? 'execution' : 'executions'}
            </p>
          </div>
        </div>
      </div>

      {/* Tool Calls List */}
      <div className="space-y-4">
        {toolCalls.map((toolCall) => (
          <ToolCallItem key={toolCall.id} toolCall={toolCall} />
        ))}
      </div>
    </div>
  );
}

