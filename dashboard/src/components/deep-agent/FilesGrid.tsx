/**
 * FilesGrid Component for Deep Agent
 *
 * Displays agent's file system in a grid layout.
 * Adapted from: https://github.com/langchain-ai/deep-agents-ui
 */

import type { FileContent, FileItem } from '@/types/deep-agent';
import { FileText, Download, FolderOpen } from 'lucide-react';
import { useState } from 'react';
import { FileViewer } from './FileViewer';

interface FilesGridProps {
  files: Record<string, FileContent>;
  onSaveFile?: (path: string, content: string) => Promise<void>;
  editDisabled?: boolean;
}

export function FilesGrid({ files, onSaveFile, editDisabled = false }: FilesGridProps) {
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);

  const handleSaveFile = async (path: string, content: string) => {
    if (onSaveFile) {
      await onSaveFile(path, content);
    }
    setSelectedFile({ path, content });
  };

  const fileEntries = Object.entries(files);

  if (fileEntries.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center">
        <p className="text-sm text-gray-500">
          No files created yet. The agent will create files as needed.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="h-full overflow-y-auto p-4">
        <div className="mb-4 flex items-center gap-2 pb-2 border-b border-gray-200">
          <FolderOpen size={18} className="text-gray-600" />
          <h3 className="text-sm font-bold text-gray-900 uppercase tracking-widest">
            Files ({fileEntries.length})
          </h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {fileEntries.map(([path, content]) => {
            // Handle different content formats from Deep Agents
            let fileContent: string;

            // Check if content is an object with nested content property (Deep Agents with metadata)
            if (typeof content === 'object' && content !== null && 'content' in content) {
              const contentArray = (content as { content: unknown }).content;
              if (Array.isArray(contentArray)) {
                fileContent = contentArray.join('\n');
              } else {
                fileContent = String(contentArray || '');
              }
            }
            // Check if content is a direct array
            else if (Array.isArray(content)) {
              fileContent = content.join('\n');
            }
            // Fallback: treat as string
            else {
              fileContent = String(content || '');
            }

            const handleDownload = () => {
              console.log('💾 [DOWNLOAD STARTED]', path);
              console.log('📊 [CONTENT LENGTH]', fileContent.length, 'characters');
              console.log('📊 [CONTENT FIRST 200 CHARS]', fileContent.substring(0, 200));
              console.log('📊 [CONTENT LAST 200 CHARS]', fileContent.substring(fileContent.length - 200));

              // Detect file type from extension
              const fileName = path.split('/').pop() || 'file.txt';
              const extension = fileName.split('.').pop()?.toLowerCase();

              let mimeType = 'text/plain';
              if (extension === 'html' || extension === 'htm') {
                mimeType = 'text/html';
              } else if (extension === 'json') {
                mimeType = 'application/json';
              } else if (extension === 'xml') {
                mimeType = 'application/xml';
              } else if (extension === 'md') {
                mimeType = 'text/markdown';
              }

              const blob = new Blob([fileContent], { type: mimeType });
              console.log('📊 [BLOB SIZE]', blob.size, 'bytes');

              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = fileName;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              URL.revokeObjectURL(url);

              console.log('✅ [DOWNLOAD COMPLETE]', fileName);
            };

            return (
              <button
                key={path}
                type="button"
                onClick={handleDownload}
                className="group flex flex-col items-start gap-3 p-4 rounded-lg border border-gray-200 bg-white hover:bg-blue-50 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer"
              >
                <div className="flex items-start justify-between w-full gap-2">
                  <FileText size={32} className="text-blue-600 flex-shrink-0 group-hover:text-blue-700" />
                  <Download size={18} className="text-gray-400 group-hover:text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
                <div className="text-left w-full min-w-0">
                  <span className="text-base font-bold text-gray-900 block break-words">
                    {path.split('/').pop() || path}
                  </span>
                  <span className="text-sm text-gray-600 break-all block mt-2">
                    {path}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {selectedFile && (
        <FileViewer
          file={selectedFile}
          onSave={handleSaveFile}
          onClose={() => setSelectedFile(null)}
          editDisabled={editDisabled}
        />
      )}
    </>
  );
}

