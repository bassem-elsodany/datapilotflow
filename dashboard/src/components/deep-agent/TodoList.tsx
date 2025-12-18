/**
 * TodoList Component for Deep Agent
 *
 * Displays agent's planning tasks with status indicators.
 * Adapted from: https://github.com/langchain-ai/deep-agents-ui
 */

import { CheckCircle, Circle, Clock, ListTodo } from 'lucide-react';
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
    <div className="h-full overflow-y-auto p-4 space-y-5">
      <div className="flex items-center gap-2 pb-2 border-b border-gray-200">
        <ListTodo size={18} className="text-gray-600" />
        <h3 className="text-sm font-bold text-gray-900 uppercase tracking-widest">
          Tasks ({todos.length})
        </h3>
      </div>

      {/* In Progress */}
      {groupedTodos.in_progress.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Clock size={18} className="text-amber-500" />
            <h4 className="text-sm font-bold text-gray-900 uppercase tracking-widest">
              In Progress ({groupedTodos.in_progress.length})
            </h4>
          </div>
          <div className="space-y-3">
            {groupedTodos.in_progress.map((todo) => (
              <div
                key={todo.id}
                className="flex items-start gap-3 p-4 rounded-lg bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 hover:border-amber-300 transition-colors"
              >
                {getStatusIcon(todo.status)}
                <span className="text-base flex-1 text-gray-900 break-words">{todo.content}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pending */}
      {groupedTodos.pending.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Circle size={18} className="text-gray-400" />
            <h4 className="text-sm font-bold text-gray-900 uppercase tracking-widest">
              Pending ({groupedTodos.pending.length})
            </h4>
          </div>
          <div className="space-y-3">
            {groupedTodos.pending.map((todo) => (
              <div
                key={todo.id}
                className="flex items-start gap-3 p-4 rounded-lg bg-gradient-to-r from-gray-50 to-slate-50 border border-gray-200 hover:border-gray-300 transition-colors"
              >
                {getStatusIcon(todo.status)}
                <span className="text-base flex-1 text-gray-800 break-words">{todo.content}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Completed */}
      {groupedTodos.completed.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircle size={18} className="text-emerald-500" />
            <h4 className="text-sm font-bold text-gray-900 uppercase tracking-widest">
              Completed ({groupedTodos.completed.length})
            </h4>
          </div>
          <div className="space-y-3">
            {groupedTodos.completed.map((todo) => (
              <div
                key={todo.id}
                className={cn(
                  'flex items-start gap-3 p-4 rounded-lg bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 hover:border-emerald-300 transition-colors'
                )}
              >
                {getStatusIcon(todo.status)}
                <span className="text-base flex-1 line-through text-gray-600 break-words">
                  {todo.content}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

