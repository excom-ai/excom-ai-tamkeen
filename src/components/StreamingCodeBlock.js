import React, { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const StreamingCodeBlock = ({ language, codeContent, isStreaming = false }) => {
  const [showFormatted, setShowFormatted] = useState(!isStreaming);
  const [streamingContent, setStreamingContent] = useState('');

  useEffect(() => {
    if (isStreaming) {
      setStreamingContent(codeContent);
      setShowFormatted(false);
    } else {
      // When streaming is complete, show formatted version after a brief delay
      const timer = setTimeout(() => {
        setShowFormatted(true);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [codeContent, isStreaming]);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(codeContent);
    const btn = document.activeElement;
    const originalText = btn.textContent;
    btn.textContent = '✓ Copied';
    setTimeout(() => {
      btn.textContent = originalText;
    }, 2000);
  };

  return (
    <div className="code-block-wrapper">
      <div className="code-block-header">
        <span className="code-language">{language || 'plaintext'}</span>
        <button className="copy-button" onClick={copyToClipboard}>
          Copy
        </button>
      </div>

      {!showFormatted ? (
        // Show raw streaming content
        <pre style={{
          margin: 0,
          padding: '16px',
          backgroundColor: '#282c34',
          color: '#abb2bf',
          borderRadius: '0 0 8px 8px',
          fontSize: '14px',
          overflow: 'auto',
          fontFamily: 'Monaco, "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace',
          whiteSpace: 'pre-wrap',
          wordWrap: 'break-word'
        }}>
          <code>{streamingContent}</code>
          {isStreaming && <span className="streaming-cursor">▎</span>}
        </pre>
      ) : (
        // Show formatted syntax highlighted version
        language ? (
          <SyntaxHighlighter
            style={oneDark}
            language={language}
            PreTag="div"
            customStyle={{
              margin: 0,
              borderRadius: '0 0 8px 8px',
              fontSize: '14px'
            }}
          >
            {codeContent}
          </SyntaxHighlighter>
        ) : (
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
        )
      )}
    </div>
  );
};

export default StreamingCodeBlock;