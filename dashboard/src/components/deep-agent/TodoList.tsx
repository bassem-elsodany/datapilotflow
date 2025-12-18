/**
 * TodoList Component for Deep Agent
 * 
 * Displays agent's planning tasks with status indicators.
 * Adapted from: https://github.com/langchain-ai/deep-agents-ui
 */

import { CheckCircle, Circle, Clock } from 'lucide-react';
import { useMemo } from 'react';
import type { TodoItem } from '@/types/deep-agent';
import { cn } from '@/lib/utils';

interface TodoListProps {
  todos: TodoItem[];
}

const getStatusIcon = (status: TodoItem['status']) => {
  switch (status) {
    case 'completed':
      return <CheckCircle size={16} className="text-green-500" />;
    case 'in_progress':
      return <Clock size={16} className="text-yellow-500 animate-pulse" />;
    default:
      return <Circle size={16} className="text-gray-400" />;
  }
};

export function TodoList({ todos }: TodoListProps) {
  const groupedTodos = useMemo(() => {
    return {
      in_progress: todos.filter((t) => t.status === 'in_progress'),
      pending: todos.filter((t) => t.status === 'pending'),
      completed: todos.filter((t) => t.status === 'completed'),
    };
  }, [todos]);

  if (todos.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center">
        <p className="text-sm text-gray-500">
          No tasks yet. The agent will create a plan when needed.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      {/* In Progress */}
      {groupedTodos.in_progress.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
            In Progress
          </h3>
          {groupedTodos.in_progress.map((todo) => (
            <div
              key={todo.id}
              className="flex items-start gap-2 p-3 rounded-lg bg-yellow-50 border border-yellow-200"
            >
              {getStatusIcon(todo.status)}
              <span className="text-sm flex-1">{todo.content}</span>
            </div>
          ))}
        </div>
      )}

      {/* Pending */}
      {groupedTodos.pending.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
            Pending
          </h3>
          {groupedTodos.pending.map((todo) => (
            <div
              key={todo.id}
              className="flex items-start gap-2 p-3 rounded-lg bg-gray-50 border border-gray-200"
            >
              {getStatusIcon(todo.status)}
              <span className="text-sm flex-1 text-gray-600">{todo.content}</span>
            </div>
          ))}
        </div>
      )}

      {/* Completed */}
      {groupedTodos.completed.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
            Completed ({groupedTodos.completed.length})
          </h3>
          {groupedTodos.completed.map((todo) => (
            <div
              key={todo.id}
              className={cn(
                'flex items-start gap-2 p-3 rounded-lg bg-green-50 border border-green-200 opacity-60'
              )}
            >
              {getStatusIcon(todo.status)}
              <span className="text-sm flex-1 line-through text-gray-500">
                {todo.content}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

