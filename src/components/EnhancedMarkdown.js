import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import remarkBreaks from 'remark-breaks';
import remarkEmoji from 'remark-emoji';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import HtmlPreview from './HtmlPreview';
import 'katex/dist/katex.min.css';
import './EnhancedMarkdown.css';

const EnhancedMarkdown = ({ content, className = '' }) => {
  const components = {
    code({ node, inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '');
      const language = match ? match[1] : '';
      const codeContent = String(children).replace(/\n$/, '');

      // Debug logging
      console.log('Code block detected:', { language, className, inline, contentPreview: codeContent.substring(0, 50) });

      // Handle non-inline code blocks
      if (!inline) {
        // Check if it's HTML code block by language tag or content
        const isHtmlByLanguage = language && (language.toLowerCase() === 'html' || language.toLowerCase() === 'htm');
        const isHtmlByContent = !language && codeContent.trim().match(/^<!DOCTYPE html>|^<html|^<\!--.*-->/i);

        if (isHtmlByLanguage || isHtmlByContent) {
          console.log('HTML block detected, rendering with HtmlPreview');
          return <HtmlPreview htmlContent={codeContent} />;
        }

        // If there's a language specified, use syntax highlighter
        if (language) {
          return (
            <div className="code-block-wrapper">
              <div className="code-block-header">
                <span className="code-language">{language}</span>
                <button
                  className="copy-button"
                  onClick={() => {
                    navigator.clipboard.writeText(codeContent);
                    const btn = document.activeElement;
                    btn.textContent = '✓ Copied';
                    setTimeout(() => {
                      btn.textContent = 'Copy';
                    }, 2000);
                  }}
                >
                  Copy
                </button>
              </div>
              <SyntaxHighlighter
                style={oneDark}
                language={language}
                PreTag="div"
                customStyle={{
                  margin: 0,
                  borderRadius: '0 0 8px 8px',
                  fontSize: '14px'
                }}
                {...props}
              >
                {codeContent}
              </SyntaxHighlighter>
            </div>
          );
        }

        // For code blocks without language, just show as plain code
        return (
          <div className="code-block-wrapper">
            <div className="code-block-header">
              <span className="code-language">plaintext</span>
              <button
                className="copy-button"
                onClick={() => {
                  navigator.clipboard.writeText(codeContent);
                  const btn = document.activeElement;
                  btn.textContent = '✓ Copied';
                  setTimeout(() => {
                    btn.textContent = 'Copy';
                  }, 2000);
                }}
              >
                Copy
              </button>
            </div>
            <pre style={{
              margin: 0,
              padding: '16px',
              backgroundColor: '#282c34',
              color: '#abb2bf',
              borderRadius: '0 0 8px 8px',
              fontSize: '14px',
              overflow: 'auto'
            }}>
              <code>{codeContent}</code>
            </pre>
          </div>
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