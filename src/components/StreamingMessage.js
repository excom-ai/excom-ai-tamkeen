import React, { useRef, useEffect, memo } from 'react';
import EnhancedMarkdown from './EnhancedMarkdown';

// Memoized component for completed items - won't re-render unless items change
const CompletedItems = memo(({ items }) => {
  if (!items || items.length === 0) return null;

  return (
    <>
      {items.map((item) => {
        if (item.type === 'thinking') {
          return (
            <div key={`think-${item.timestamp}`} className="inline-thinking">
              <span className="think-icon">🤔</span>
              <span className="think-content">{item.content}</span>
            </div>
          );
        } else if (item.type === 'tool_call') {
          // Display tool calls as inline text, not as boxes
          return (
            <div key={`tool-${item.timestamp}`} className="tool-inline-text">
              <em>(Calling tool: {item.name})</em>
              {item.isProcessing && (
                <span className="processing-dots" style={{marginLeft: '5px'}}>
                  <span>.</span><span>.</span><span>.</span>
                </span>
              )}
            </div>
          );
        }
        return null;
      })}
    </>
  );
});

CompletedItems.displayName = 'CompletedItems';

// Component for streaming text that updates via ref to avoid re-renders
const StreamingText = memo(({ text, isStreaming, autoRenderHtml }) => {
  const contentRef = useRef(null);
  const lastTextRef = useRef('');

  // Update text content directly via DOM when streaming
  useEffect(() => {
    if (isStreaming && contentRef.current && text !== lastTextRef.current) {
      // For simple text updates during streaming, update DOM directly
      if (!text.includes('```') && !text.includes('`') && !text.includes('#')) {
        contentRef.current.textContent = text;
        lastTextRef.current = text;
      }
    }
  }, [text, isStreaming]);

  // Use EnhancedMarkdown for complex content or when not streaming
  if (!isStreaming || text.includes('```') || text.includes('`') || text.includes('#')) {
    return (
      <EnhancedMarkdown
        content={text}
        isStreaming={isStreaming}
        autoRenderHtml={autoRenderHtml}
      />
    );
  }

  // Simple text div that updates via ref
  return <div ref={contentRef} className="streaming-text-content">{text}</div>;
});

StreamingText.displayName = 'StreamingText';

// Main streaming message component
const StreamingMessage = memo(({ message, settings }) => {
  // New optimized rendering with separated streaming text
  if (message.completedItems !== undefined || message.streamingText !== undefined || message.text) {
    return (
      <>
        {/* Always render text first if it exists */}
        {message.text && (
          <StreamingText
            text={message.text}
            isStreaming={false}
            autoRenderHtml={settings.autoRenderHtml}
          />
        )}
        {/* Then render streaming text if still streaming */}
        {message.streamingText && !message.text && (
          <StreamingText
            text={message.streamingText}
            isStreaming={message.isStreaming}
            autoRenderHtml={settings.autoRenderHtml}
          />
        )}
        {/* Finally render completed items (tool calls) after text */}
        <CompletedItems items={message.completedItems} />
      </>
    );
  }

  // Fallback for old format
  return (
    <EnhancedMarkdown
      content={message.text}
      isStreaming={false}
      autoRenderHtml={settings.autoRenderHtml}
    />
  );
});

StreamingMessage.displayName = 'StreamingMessage';

export default StreamingMessage;