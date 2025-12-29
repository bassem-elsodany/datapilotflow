import React from 'react';
import { Box, Text, Code, Button, Group } from '@mantine/core';
import { IconCopy } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  // Handle empty content
  if (!content || content.trim() === '') {
    return null;
  }

  // Parse markdown and convert to styled components
  const parseMarkdown = (text: string) => {
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];

      // Code blocks
      if (line.startsWith('```')) {
        const language = line.slice(3).trim();
        const codeLines: string[] = [];
        i++; // Skip the opening ```
        
        while (i < lines.length && !lines[i].startsWith('```')) {
          codeLines.push(lines[i]);
          i++;
        }
        
        if (i < lines.length) {
          i++; // Skip the closing ```
        }

        const codeContent = codeLines.join('\n');
        elements.push(
          <CodeBlock 
            key={`code-${elements.length}`} 
            language={language} 
            content={codeContent} 
          />
        );
        continue;
      }

      // Headings
      if (line.startsWith('#')) {
        const level = line.match(/^#+/)?.[0].length || 1;
        const headingText = line.replace(/^#+\s*/, '');
        const headingLevel = Math.min(level, 6);
        
        const headingStyle = {
          margin: `${Math.max(24 - level * 4, 12)}px 0 ${Math.max(12 - level * 2, 8)}px 0`,
          fontSize: `${Math.max(24 - level * 2, 16)}px`,
          fontWeight: level === 1 ? '700' : level === 2 ? '600' : '600',
          color: 'var(--mantine-color-gray-9)',
          lineHeight: '1.3'
        };
        
        if (headingLevel === 1) {
          elements.push(
            <h1 key={`heading-${elements.length}`} style={headingStyle}>
              {parseInlineMarkdown(headingText)}
            </h1>
          );
        } else if (headingLevel === 2) {
          elements.push(
            <h2 key={`heading-${elements.length}`} style={headingStyle}>
              {parseInlineMarkdown(headingText)}
            </h2>
          );
        } else if (headingLevel === 3) {
          elements.push(
            <h3 key={`heading-${elements.length}`} style={headingStyle}>
              {parseInlineMarkdown(headingText)}
            </h3>
          );
        } else if (headingLevel === 4) {
          elements.push(
            <h4 key={`heading-${elements.length}`} style={headingStyle}>
              {parseInlineMarkdown(headingText)}
            </h4>
          );
        } else if (headingLevel === 5) {
          elements.push(
            <h5 key={`heading-${elements.length}`} style={headingStyle}>
              {parseInlineMarkdown(headingText)}
            </h5>
          );
        } else {
          elements.push(
            <h6 key={`heading-${elements.length}`} style={headingStyle}>
              {parseInlineMarkdown(headingText)}
            </h6>
          );
        }
        i++;
        continue;
      }

      // Lists
      if (line.match(/^[\s]*[-*+]\s/)) {
        const listItems: string[] = [];
        const listType = 'ul';
        
        while (i < lines.length && lines[i].match(/^[\s]*[-*+]\s/)) {
          const itemText = lines[i].replace(/^[\s]*[-*+]\s*/, '');
          listItems.push(itemText);
          i++;
        }

        elements.push(
          <ul
            key={`list-${elements.length}`}
            style={{
              margin: '12px 0',
              paddingLeft: '24px',
              listStyleType: 'disc',
              listStylePosition: 'outside'
            }}
          >
            {listItems.map((item, index) => (
              <li
                key={index}
                style={{
                  margin: '6px 0',
                  lineHeight: '1.6'
                }}
              >
                {parseInlineMarkdown(item)}
              </li>
            ))}
          </ul>
        );
        continue;
      }

      // Numbered lists
      if (line.match(/^[\s]*\d+\.\s/)) {
        const listItems: string[] = [];
        
        while (i < lines.length && lines[i].match(/^[\s]*\d+\.\s/)) {
          const itemText = lines[i].replace(/^[\s]*\d+\.\s*/, '');
          listItems.push(itemText);
          i++;
        }

        elements.push(
          <ol
            key={`olist-${elements.length}`}
            style={{
              margin: '12px 0',
              paddingLeft: '24px',
              listStyleType: 'decimal'
            }}
          >
            {listItems.map((item, index) => (
              <li
                key={index}
                style={{
                  margin: '6px 0',
                  lineHeight: '1.6'
                }}
              >
                {parseInlineMarkdown(item)}
              </li>
            ))}
          </ol>
        );
        continue;
      }

      // Blockquotes
      if (line.startsWith('>')) {
        const quoteLines: string[] = [];
        
        while (i < lines.length && lines[i].startsWith('>')) {
          quoteLines.push(lines[i].replace(/^>\s*/, ''));
          i++;
        }

        elements.push(
          <blockquote
            key={`quote-${elements.length}`}
            style={{
              borderLeft: '4px solid var(--mantine-color-blue-6)',
              padding: '12px 16px',
              margin: '16px 0',
              background: 'var(--mantine-color-blue-0)',
              borderRadius: '0 6px 6px 0',
              color: 'var(--mantine-color-gray-6)',
              fontStyle: 'italic'
            }}
          >
            {quoteLines.map((quoteLine, index) => (
              <div key={index}>
                {parseInlineMarkdown(quoteLine)}
              </div>
            ))}
          </blockquote>
        );
        continue;
      }

      // Horizontal rules
      if (line.match(/^[\s]*[-*_]{3,}[\s]*$/)) {
        elements.push(
          <hr
            key={`hr-${elements.length}`}
            style={{
              border: 'none',
              borderTop: '1px solid var(--mantine-color-gray-3)',
              margin: '20px 0'
            }}
          />
        );
        i++;
        continue;
      }

      // Regular paragraphs
      if (line.trim()) {
        elements.push(
          <p
            key={`p-${elements.length}`}
            style={{
              margin: '12px 0',
              lineHeight: '1.6'
            }}
          >
            {parseInlineMarkdown(line)}
          </p>
        );
      } else {
        // Empty line - add spacing
        elements.push(<div key={`spacing-${elements.length}`} style={{ height: '8px' }} />);
      }

      i++;
    }

    return elements;
  };

  // Parse inline markdown (bold, italic, code, links)
  const parseInlineMarkdown = (text: string): React.ReactNode => {
    const parts: React.ReactNode[] = [];
    let currentText = '';
    let i = 0;

    while (i < text.length) {
      // Inline code
      if (text.slice(i, i + 1) === '`') {
        if (currentText) {
          parts.push(<span key={`text-${parts.length}`}>{currentText}</span>);
          currentText = '';
        }

        i++; // Skip opening backtick
        const codeStart = i;
        while (i < text.length && text[i] !== '`') {
          i++;
        }
        
        if (i < text.length) {
          const codeContent = text.slice(codeStart, i);
          parts.push(
            <Code
              key={`inline-code-${parts.length}`}
              style={{
                backgroundColor: 'var(--mantine-color-gray-1)',
                color: 'var(--mantine-color-gray-8)',
                padding: '2px 6px',
                borderRadius: '4px',
                fontFamily: 'var(--mantine-font-family-monospace)',
                fontSize: '0.9em',
                border: '1px solid var(--mantine-color-gray-3)'
              }}
            >
              {codeContent}
            </Code>
          );
          i++; // Skip closing backtick
        }
        continue;
      }

      // Bold
      if (text.slice(i, i + 2) === '**') {
        if (currentText) {
          parts.push(<span key={`text-${parts.length}`}>{currentText}</span>);
          currentText = '';
        }

        i += 2; // Skip opening **
        const boldStart = i;
        while (i < text.length - 1 && text.slice(i, i + 2) !== '**') {
          i++;
        }
        
        if (i < text.length - 1) {
          const boldContent = text.slice(boldStart, i);
          parts.push(
            <strong
              key={`bold-${parts.length}`}
              style={{
                fontWeight: '600',
                color: 'var(--mantine-color-gray-9)'
              }}
            >
              {parseInlineMarkdown(boldContent)}
            </strong>
          );
          i += 2; // Skip closing **
        }
        continue;
      }

      // Italic
      if (text.slice(i, i + 1) === '*') {
        if (currentText) {
          parts.push(<span key={`text-${parts.length}`}>{currentText}</span>);
          currentText = '';
        }

        i++; // Skip opening *
        const italicStart = i;
        while (i < text.length && text[i] !== '*') {
          i++;
        }
        
        if (i < text.length) {
          const italicContent = text.slice(italicStart, i);
          parts.push(
            <em
              key={`italic-${parts.length}`}
              style={{
                fontStyle: 'italic'
              }}
            >
              {parseInlineMarkdown(italicContent)}
            </em>
          );
          i++; // Skip closing *
        }
        continue;
      }

      // Links
      if (text.slice(i, i + 1) === '[') {
        if (currentText) {
          parts.push(<span key={`text-${parts.length}`}>{currentText}</span>);
          currentText = '';
        }

        i++; // Skip opening [
        const linkTextStart = i;
        while (i < text.length && text[i] !== ']') {
          i++;
        }
        
        if (i < text.length && text.slice(i, i + 1) === ']' && text.slice(i + 1, i + 2) === '(') {
          const linkText = text.slice(linkTextStart, i);
          i += 2; // Skip ] and (
          
          const urlStart = i;
          while (i < text.length && text[i] !== ')') {
            i++;
          }
          
          if (i < text.length) {
            const url = text.slice(urlStart, i);
            parts.push(
              <a
                key={`link-${parts.length}`}
                href={url}
                style={{
                  color: 'var(--mantine-color-blue-6)',
                  textDecoration: 'none',
                  borderBottom: '1px solid transparent',
                  transition: 'border-color 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  (e.target as HTMLElement).style.borderBottomColor = 'var(--mantine-color-blue-6)';
                }}
                onMouseLeave={(e) => {
                  (e.target as HTMLElement).style.borderBottomColor = 'transparent';
                }}
              >
                {linkText}
              </a>
            );
            i++; // Skip closing )
          }
        }
        continue;
      }

      currentText += text[i];
      i++;
    }

    if (currentText) {
      parts.push(<span key={`text-${parts.length}`}>{currentText}</span>);
    }

    return parts.length > 0 ? parts : text;
  };

  return (
    <Box className={className || ''}>
      {parseMarkdown(content)}
    </Box>
  );
}

// Code block component with syntax highlighting and copy functionality
function CodeBlock({ language, content }: { language: string; content: string }) {
  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    notifications.show({
      title: 'Copied!',
      message: 'Code copied to clipboard',
      color: 'green',
    });
  };

  return (
    <Box
      style={{
        backgroundColor: 'var(--mantine-color-white)',
        border: '1px solid var(--mantine-color-blue-2)',
        borderRadius: '12px',
        margin: '20px 0',
        overflow: 'hidden',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)'
      }}
    >
      <Group
        justify="space-between"
        p="sm"
        style={{
          backgroundColor: 'var(--mantine-color-blue-0)',
          borderBottom: '1px solid var(--mantine-color-blue-2)'
        }}
      >
        <Code style={{ 
          backgroundColor: 'var(--mantine-color-blue-1)', 
          color: 'var(--mantine-color-blue-7)', 
          fontSize: '12px',
          fontWeight: '600',
          padding: '4px 8px',
          borderRadius: '6px'
        }}>
          {language || 'code'}
        </Code>
        <Button
          size="xs"
          variant="light"
          color="blue"
          leftSection={<IconCopy size={14} />}
          onClick={handleCopy}
          style={{ 
            color: 'var(--mantine-color-blue-7)',
            fontWeight: '500'
          }}
        >
          Copy
        </Button>
      </Group>
      <Box p="lg">
        <Code
          block
          style={{
            backgroundColor: 'transparent',
            color: 'var(--mantine-color-gray-8)',
            fontFamily: 'var(--mantine-font-family-monospace)',
            fontSize: '14px',
            lineHeight: 1.6,
            padding: '0',
            whiteSpace: 'pre-wrap'
          }}
        >
          {content}
        </Code>
      </Box>
    </Box>
  );
}
