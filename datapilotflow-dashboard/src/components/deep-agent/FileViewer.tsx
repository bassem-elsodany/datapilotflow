/**
 * FileViewer Component for Deep Agent
 * 
 * Dialog to view and edit agent's files.
 * Adapted from: https://github.com/langchain-ai/deep-agents-ui
 */

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import type { FileItem } from '@/types/deep-agent';
import { Copy, Download, Edit, Save, X } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

interface FileViewerProps {
  file: FileItem;
  onSave: (path: string, content: string) => Promise<void>;
  onClose: () => void;
  editDisabled?: boolean;
}

export function FileViewer({
  file,
  onSave,
  onClose,
  editDisabled = false,
}: FileViewerProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [content, setContent] = useState(file.content);
  const [isSaving, setIsSaving] = useState(false);
  const [viewMode, setViewMode] = useState<'preview' | 'code'>('preview');

  // Detect if file is HTML
  const fileName = file.path.split('/').pop() || '';
  const isHtmlFile = fileName.endsWith('.html') || fileName.endsWith('.htm');

  // Update content when file changes
  useEffect(() => {
    setContent(file.content);
    setIsEditing(false);
    setViewMode('preview'); // Reset to preview on file change
  }, [file]);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(content);
  }, [content]);

  const handleDownload = useCallback(() => {
    // Detect file type from extension
    const fileName = file.path.split('/').pop() || 'file.txt';
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

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [content, file.path]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave(file.path, content);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to save file:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span className="font-mono text-sm">{file.path}</span>
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          {isEditing ? (
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="w-full h-[400px] font-mono text-sm"
              placeholder="File content..."
            />
          ) : (
            <div className="flex flex-col gap-2">
              {/* View mode toggle for HTML files */}
              {isHtmlFile && (
                <div className="flex gap-2">
                  <Button
                    variant={viewMode === 'preview' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('preview')}
                  >
                    Preview
                  </Button>
                  <Button
                    variant={viewMode === 'code' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('code')}
                  >
                    Code
                  </Button>
                </div>
              )}

              <div className="w-full h-[400px] overflow-auto border rounded-md">
                {isHtmlFile && viewMode === 'preview' ? (
                  <iframe
                    srcDoc={content}
                    className="w-full h-full border-0"
                    sandbox="allow-same-origin"
                    title="HTML Preview"
                  />
                ) : (
                  <pre className="font-mono text-sm whitespace-pre-wrap p-4">
                    {content}
                  </pre>
                )}
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="flex items-center justify-between">
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
            >
              <Copy className="w-4 h-4 mr-2" />
              Copy
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
            >
              <Download className="w-4 h-4 mr-2" />
              Download
            </Button>
          </div>

          <div className="flex gap-2">
            {isEditing ? (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setContent(file.content);
                    setIsEditing(false);
                  }}
                >
                  <X className="w-4 h-4 mr-2" />
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleSave}
                  disabled={isSaving}
                >
                  {isSaving ? (
                    <>Loading...</>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Save
                    </>
                  )}
                </Button>
              </>
            ) : (
              <>
                {!editDisabled && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditing(true)}
                  >
                    <Edit className="w-4 h-4 mr-2" />
                    Edit
                  </Button>
                )}
                <Button variant="outline" size="sm" onClick={onClose}>
                  Close
                </Button>
              </>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

