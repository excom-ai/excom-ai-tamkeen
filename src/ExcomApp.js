import React, { useState, useEffect } from 'react';
import { useAuth } from './components/AuthProvider';
import Chat from './components/Chat';
import Settings from './components/Settings';
import Login from './components/Login';
import './ExcomApp.css';

function ExcomApp() {
  const { isAuthenticated, isLoading, user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');

  // Load settings from localStorage or use defaults
  const [settings, setSettings] = useState(() => {
    const savedSettings = localStorage.getItem('excomSettings');
    if (savedSettings) {
      return JSON.parse(savedSettings);
    }
    return {
      apiUrl: 'http://localhost:9000',
      streaming: true  // Enable streaming for real-time responses
    };
  });

  // Save settings to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('excomSettings', JSON.stringify(settings));
  }, [settings]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // Show login if not authenticated
  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <div className="excom-app">
      {/* Header */}
      <header className="app-header">
        <div className="app-logo">
          <img src="/logo.png" alt="excom.ai" className="logo-image" />
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
        <div className="user-info">
          <span className="user-name">{user?.name || user?.username}</span>
          <button className="logout-btn" onClick={logout}>
            Sign Out
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