import React, { useState, useEffect } from 'react';
import Chat from './components/Chat';
import Settings from './components/Settings';
import './ExcomApp.css';

function ExcomApp() {
  const [activeTab, setActiveTab] = useState('chat');

  // Load settings from localStorage or use defaults
  const [settings, setSettings] = useState(() => {
    const savedSettings = localStorage.getItem('excomSettings');
    if (savedSettings) {
      return JSON.parse(savedSettings);
    }
    return {
      apiUrl: 'http://localhost:9000',
      streaming: false  // Disabled to enable tool usage
    };
  });

  // Save settings to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('excomSettings', JSON.stringify(settings));
  }, [settings]);

  return (
    <div className="excom-app">
      {/* Header */}
      <header className="app-header">
        <div className="app-logo">
          <span className="logo-text">excom.ai</span>
        </div>
        <div className="app-tabs">
          <button
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            Chat
          </button>
          <button
            className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            Settings
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="app-content">
        {activeTab === 'chat' ? (
          <Chat settings={settings} />
        ) : (
          <Settings settings={settings} setSettings={setSettings} />
        )}
      </main>
    </div>
  );
}

export default ExcomApp;