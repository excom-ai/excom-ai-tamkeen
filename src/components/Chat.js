import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from './AuthProvider';
import EnhancedMarkdown from './EnhancedMarkdown';
import './Chat.css';

function Chat({ settings }) {
  const { getAccessToken } = useAuth();
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! I'm your AI assistant. How can I help you today?", sender: 'bot', timestamp: new Date() }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentAbortController, setCurrentAbortController] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingTool, setProcessingTool] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const stopGeneration = () => {
    if (currentAbortController) {
      currentAbortController.abort('user_stopped');
      setCurrentAbortController(null);
      setIsTyping(false);
    }
  };

  const handleStreamedResponse = async (currentMessage) => {
    console.log('=== HANDLESTREAMEDRESPONSE CALLED ===');
    console.log('Using streaming endpoint!');

    const abortController = new AbortController();
    setCurrentAbortController(abortController);

    const botMessageId = Date.now() + 1;
    let accumulatedText = '';

    try {
      // Get auth token if available
      const token = await getAccessToken();
      const headers = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      console.log('Fetching from:', `${settings.apiUrl}/api/chat/stream`);
      const response = await fetch(`${settings.apiUrl}/api/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: currentMessage,
          conversation_history: messages.slice(-10) // Last 10 messages for context
        }),
        signal: abortController.signal
      });

      if (!response.ok) {
        throw new Error('Stream response not ok');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      // Add initial empty bot message
      setMessages(prev => [...prev, {
        id: botMessageId,
        text: '',
        sender: 'bot',
        timestamp: new Date()
      }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              break;
            }

            try {
              const parsed = JSON.parse(data);

              if (parsed.type === 'content') {
                accumulatedText += parsed.content;
                setMessages(prev => prev.map(msg =>
                  msg.id === botMessageId
                    ? { ...msg, text: accumulatedText }
                    : msg
                ));
              } else if (parsed.type === 'tool_call') {
                // Add condensed tool call info inline
                const toolName = parsed.tool || 'tool';
                const toolInfo = `\n\n🔧 *Using ${toolName}...*\n`;
                accumulatedText += toolInfo;
                setIsProcessing(true);
                setProcessingTool(toolName);
                setMessages(prev => prev.map(msg =>
                  msg.id === botMessageId
                    ? { ...msg, text: accumulatedText, isProcessing: true, processingTool: toolName }
                    : msg
                ));
              } else if (parsed.type === 'tool_result') {
                // Tool completed - stop processing indicator
                setIsProcessing(false);
                setProcessingTool('');
                // Only show errors, skip successful results
                if (parsed.is_error) {
                  const errorInfo = `\n❌ Tool error: ${parsed.content}\n`;
                  accumulatedText += errorInfo;
                }
                setMessages(prev => prev.map(msg =>
                  msg.id === botMessageId
                    ? { ...msg, text: accumulatedText, isProcessing: false, processingTool: '' }
                    : msg
                ));
              } else if (parsed.type === 'thinking' || parsed.type === 'reasoning' ||
                         parsed.type === 'tool_complete' || parsed.type === 'status') {
                // Skip these - don't display them at all
              } else if (parsed.type === 'error') {
                throw new Error(parsed.content);
              } else if (parsed.type === 'done') {
                // Stream complete - break out of all loops
                setIsProcessing(false);
                setProcessingTool('');
                console.log('Stream completed - received done signal');
                return; // Exit the entire streaming function
              }
            } catch (e) {
              if (e instanceof SyntaxError) {
                console.warn('Failed to parse SSE data:', data);
              } else {
                throw e;
              }
            }
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        const reason = error.cause || error.message;
        if (reason === 'user_stopped') {
          setMessages(prev => prev.map(msg =>
            msg.id === botMessageId
              ? { ...msg, text: accumulatedText + '\n\n*[Generation stopped by user]*' }
              : msg
          ));
        }
      } else {
        console.error('Stream error:', error);
        setMessages(prev => prev.map(msg =>
          msg.id === botMessageId
            ? { ...msg, text: 'Sorry, I encountered an error. Please try again.', isError: true }
            : msg
        ));
      }
    } finally {
      setCurrentAbortController(null);
    }
  };

  const handleNormalResponse = async (currentMessage) => {
    console.log('=== HANDLENORMALRESPONSE CALLED ===');
    console.log('WHY ARE WE HERE? THIS SHOULD NOT BE CALLED!');

    try {
      // Get auth token if available
      const token = await getAccessToken();
      const headers = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      console.log('Fetching from NON-STREAMING:', `${settings.apiUrl}/api/chat`);
      const response = await fetch(`${settings.apiUrl}/api/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: currentMessage,
          conversation_history: messages.slice(-10)
        })
      });

      const data = await response.json();

      if (response.ok) {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          text: data.response,
          sender: 'bot',
          timestamp: new Date()
        }]);
      } else {
        throw new Error(data.detail || 'Failed to get response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error. Please try again.',
        sender: 'bot',
        isError: true,
        timestamp: new Date()
      }]);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isTyping) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    // Debug logging
    console.log('Settings:', settings);
    console.log('Streaming enabled?', settings.streaming);

    // FORCE STREAMING TO TRUE FOR NOW
    const forceStreaming = true;
    console.log('FORCING STREAMING:', forceStreaming);
    console.log('Using endpoint:', forceStreaming ? '/api/chat/stream' : '/api/chat');

    // Debug message removed - streaming is always enabled

    try {
      if (forceStreaming) {  // Use forced value
        await handleStreamedResponse(inputMessage);
      } else {
        await handleNormalResponse(inputMessage);
      }
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([{
      id: 1,
      text: "Chat cleared. How can I help you?",
      sender: 'bot',
      timestamp: new Date()
    }]);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <span className="chat-title">ExCom AI Assistant</span>
        <button className="clear-btn" onClick={clearChat}>
          🗑️ Clear
        </button>
      </div>

      <div className="messages-area">
        {messages.map(message => (
          message.sender === 'system' ? (
            <div key={message.id} className="system-message" data-type={message.messageType || 'status'}>
              <div className="system-message-content">
                {message.messageType === 'tool_result' || message.messageType === 'tool_error' ? (
                  <EnhancedMarkdown content={message.text} />
                ) : (
                  message.text
                )}
              </div>
            </div>
          ) : (
            <div
              key={message.id}
              className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'} ${message.isError ? 'error' : ''}`}
            >
              <div className="message-avatar">
                {message.sender === 'user' ? '👤' : '🤖'}
              </div>
              <div className="message-content">
                <div className="message-bubble">
                  {message.sender === 'bot' ? (
                    <>
                      <EnhancedMarkdown content={message.text} />
                      {message.isProcessing && (
                        <div className="processing-indicator">
                          <span className="processing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                          </span>
                          <span className="processing-text">Processing {message.processingTool || 'tool'}...</span>
                        </div>
                      )}
                    </>
                  ) : (
                    message.text
                  )}
                </div>
                <div className="message-time">
                  {formatTime(message.timestamp)}
                </div>
              </div>
            </div>
          )
        ))}
        {isTyping && !currentAbortController && (
          <div className="typing-indicator">
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <textarea
          ref={inputRef}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          className="message-input"
          rows="3"
        />
        <div className="input-controls">
          {isTyping && currentAbortController ? (
            <button className="stop-btn" onClick={stopGeneration}>
              ⏹️ Stop
            </button>
          ) : (
            <button
              className="send-btn"
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isTyping}
            >
              {isTyping ? '⏳' : '📤'} Send
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default Chat;