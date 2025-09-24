import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from './components/AuthProvider';
import Chat from './components/Chat';
import Login from './components/Login';
import './ExcomApp.css';

function ExcomApp() {
  const { isAuthenticated, isLoading, user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const chatRef = useRef(null);

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

  // Save settings to localStorage whenever they change - v2.0
  useEffect(() => {
    localStorage.setItem('excomSettings', JSON.stringify(settings));
  }, [settings]);

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showUserMenu && !event.target.closest('.user-info')) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserMenu]);


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
        <div className="user-info">
          <button
            className="clear-chat-btn"
            onClick={() => chatRef.current?.clearChat()}
            title="Clear chat"
          >
            Clear
          </button>
          <button
            className="user-toggle-btn"
            onClick={() => setShowUserMenu(!showUserMenu)}
          >
            <span className="user-icon">👤</span>
          </button>
          {showUserMenu && (
            <div className="user-dropdown">
              <div className="user-name">
                {user?.name || user?.username || user?.displayName || user?.mail || user?.userPrincipalName || 'User'}
              </div>
              <button className="logout-btn" onClick={logout}>
                Sign Out
              </button>
            </div>
          )}
        </div>
      </header>


      {/* Content */}
      <main className="app-content">
        <Chat ref={chatRef} settings={settings} />
      </main>
    </div>
  );
}

export default ExcomApp;