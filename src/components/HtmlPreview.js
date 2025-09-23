import React, { useState, useEffect, useRef } from 'react';
import './HtmlPreview.css';

const HtmlPreview = ({ htmlContent, height = '400px' }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showCode, setShowCode] = useState(false);
  const iframeRef = useRef(null);

  useEffect(() => {
    if (iframeRef.current) {
      const iframe = iframeRef.current;
      const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;

      // Create a complete HTML document with proper structure
      const fullHtml = `
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            * {
              margin: 0;
              padding: 0;
              box-sizing: border-box;
            }
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
              line-height: 1.6;
              color: #333;
              padding: 20px;
              background: white;
            }
            /* Allow scrolling for overflow content */
            html, body {
              overflow: auto;
            }
          </style>
        </head>
        <body>
          ${htmlContent}
        </body>
        </html>
      `;

      iframeDoc.open();
      iframeDoc.write(fullHtml);
      iframeDoc.close();

      // Prevent navigation within iframe
      iframeDoc.addEventListener('click', (e) => {
        if (e.target.tagName === 'A') {
          e.preventDefault();
          e.stopPropagation();
          // Optionally open in new tab if it's an external link
          if (e.target.href && e.target.href.startsWith('http')) {
            window.open(e.target.href, '_blank');
          }
        }
      });

      // Adjust iframe height based on content
      const adjustHeight = () => {
        try {
          const contentHeight = iframeDoc.body.scrollHeight;
          if (!isExpanded && contentHeight > 400) {
            iframe.style.height = '400px';
          } else {
            iframe.style.height = contentHeight + 40 + 'px';
          }
        } catch (e) {
          console.error('Could not adjust iframe height:', e);
        }
      };

      // Wait for content to load then adjust height
      iframe.onload = adjustHeight;
      setTimeout(adjustHeight, 100);
    }
  }, [htmlContent, isExpanded]);

  const handleCopyHtml = () => {
    navigator.clipboard.writeText(htmlContent);
    const btn = document.activeElement;
    btn.textContent = '✓ Copied';
    setTimeout(() => {
      btn.textContent = 'Copy HTML';
    }, 2000);
  };

  const handleOpenInNewTab = () => {
    const newWindow = window.open('', '_blank');
    const fullHtml = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HTML Preview</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
          }
        </style>
      </head>
      <body>
        ${htmlContent}
      </body>
      </html>
    `;
    newWindow.document.write(fullHtml);
    newWindow.document.close();
  };

  return (
    <div className="html-preview-container">
      <div className="html-preview-header">
        <div className="preview-label">
          <span className="preview-icon">🌐</span>
          <span>HTML Preview</span>
        </div>
        <div className="preview-controls">
          <button
            className="preview-btn"
            onClick={() => setShowCode(!showCode)}
            title="Toggle code view"
          >
            {showCode ? '👁️ Preview' : '</> Code'}
          </button>
          <button
            className="preview-btn"
            onClick={handleCopyHtml}
            title="Copy HTML"
          >
            Copy HTML
          </button>
          <button
            className="preview-btn"
            onClick={handleOpenInNewTab}
            title="Open in new tab"
          >
            ↗️ New Tab
          </button>
          <button
            className="preview-btn"
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? '⬆️ Collapse' : '⬇️ Expand'}
          </button>
        </div>
      </div>

      {showCode ? (
        <div className="html-code-view">
          <pre><code>{htmlContent}</code></pre>
        </div>
      ) : (
        <div className={`html-preview-iframe-container ${isExpanded ? 'expanded' : ''}`}>
          <iframe
            ref={iframeRef}
            className="html-preview-iframe"
            title="HTML Preview"
            sandbox="allow-scripts"
            style={{ height: isExpanded ? 'auto' : height }}
          />
        </div>
      )}
    </div>
  );
};

export default HtmlPreview;