import React, { useState } from 'react';
import './HtmlPreview.css';

const HtmlPreview = ({ htmlContent }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showCode, setShowCode] = useState(false);

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
          min-height: 100vh;
        }
        h1, h2, h3, h4, h5, h6 {
          margin-top: 20px;
          margin-bottom: 10px;
        }
        p {
          margin-bottom: 10px;
        }
        table {
          border-collapse: collapse;
          width: 100%;
          margin: 20px 0;
        }
        th, td {
          border: 1px solid #ddd;
          padding: 8px;
          text-align: left;
        }
        th {
          background-color: #f2f2f2;
        }
        a {
          color: #0366d6;
          text-decoration: none;
        }
        a:hover {
          text-decoration: underline;
        }
        pre {
          background: #f6f8fa;
          padding: 16px;
          border-radius: 6px;
          overflow-x: auto;
        }
        code {
          background: #f6f8fa;
          padding: 2px 4px;
          border-radius: 3px;
        }
      </style>
    </head>
    <body>
      ${htmlContent}
    </body>
    </html>
  `;

  const handleCopyHtml = () => {
    navigator.clipboard.writeText(htmlContent);
    const btn = document.activeElement;
    btn.textContent = '✓ Copied';
    setTimeout(() => {
      btn.textContent = 'Copy HTML';
    }, 2000);
  };

  const handleOpenInNewTab = () => {
    const blob = new Blob([fullHtml], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
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
            className="html-preview-iframe"
            title="HTML Preview"
            srcDoc={fullHtml}
            sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox"
            style={{
              height: isExpanded ? '800px' : '400px',
              minHeight: '200px',
              width: '100%',
              border: 'none',
              display: 'block'
            }}
          />
        </div>
      )}
    </div>
  );
};

export default React.memo(HtmlPreview);