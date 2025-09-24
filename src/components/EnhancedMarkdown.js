import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import remarkBreaks from 'remark-breaks';
import remarkEmoji from 'remark-emoji';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
// SyntaxHighlighter imports moved to StreamingCodeBlock component
import StreamingCodeBlock from './StreamingCodeBlock';
import HtmlPreview from './HtmlPreview';
import 'katex/dist/katex.min.css';
import './EnhancedMarkdown.css';

const EnhancedMarkdown = ({ content, className = '', isStreaming = false }) => {
  // Detect if we have incomplete code blocks (streaming)
  const hasIncompleteCodeBlock = isStreaming && content.includes('```') &&
    (content.split('```').length % 2 === 0); // Odd number means open code block

  const components = {
    code({ node, inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '');
      const language = match ? match[1] : '';
      const codeContent = String(children).replace(/\n$/, '');

      // Handle non-inline code blocks
      if (!inline) {
        // Check if it's HTML code block by language tag or content
        const isHtmlByLanguage = language && (language.toLowerCase() === 'html' || language.toLowerCase() === 'htm');
        const isHtmlByContent = !language && codeContent.trim().match(/^<!DOCTYPE html>|^<html|^<\!--.*-->/i);

        if (isHtmlByLanguage || isHtmlByContent) {
          return <HtmlPreview htmlContent={codeContent} />;
        }

        // Use streaming code block component
        return (
          <StreamingCodeBlock
            language={language}
            codeContent={codeContent}
            isStreaming={hasIncompleteCodeBlock}
          />
        );
      }

      return (
        <code className="inline-code" {...props}>
          {children}
        </code>
      );
    },

    table({ children }) {
      return (
        <div className="table-wrapper">
          <table className="markdown-table">{children}</table>
        </div>
      );
    },

    blockquote({ children }) {
      return (
        <blockquote className="markdown-blockquote">
          {children}
        </blockquote>
      );
    },

    a({ href, children }) {
      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="markdown-link"
        >
          {children}
        </a>
      );
    },

    ul({ children }) {
      return <ul className="markdown-list">{children}</ul>;
    },

    ol({ children }) {
      return <ol className="markdown-list ordered">{children}</ol>;
    },

    li({ children, ...props }) {
      if (props['data-checked'] !== undefined) {
        return (
          <li className="task-list-item">
            <input
              type="checkbox"
              checked={props['data-checked']}
              readOnly
              className="task-checkbox"
            />
            <span>{children}</span>
          </li>
        );
      }
      return <li>{children}</li>;
    },

    h1({ children }) {
      const id = String(children).toLowerCase().replace(/\s+/g, '-');
      return <h1 id={id} className="markdown-heading">{children}</h1>;
    },

    h2({ children }) {
      const id = String(children).toLowerCase().replace(/\s+/g, '-');
      return <h2 id={id} className="markdown-heading">{children}</h2>;
    },

    h3({ children }) {
      const id = String(children).toLowerCase().replace(/\s+/g, '-');
      return <h3 id={id} className="markdown-heading">{children}</h3>;
    },

    img({ src, alt }) {
      return (
        <div className="image-wrapper">
          <img src={src} alt={alt} className="markdown-image" />
          {alt && <p className="image-caption">{alt}</p>}
        </div>
      );
    },

    hr() {
      return <hr className="markdown-divider" />;
    },

    pre({ children }) {
      return <div className="pre-wrapper">{children}</div>;
    }
  };

  return (
    <div className={`enhanced-markdown ${className}`}>
      <ReactMarkdown
        remarkPlugins={[
          remarkGfm,
          remarkMath,
          remarkBreaks,
          remarkEmoji
        ]}
        rehypePlugins={[
          rehypeKatex,
          rehypeRaw
        ]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default React.memo(EnhancedMarkdown);