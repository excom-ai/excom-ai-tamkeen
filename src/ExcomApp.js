import React, { useState, useEffect } from 'react';
import { useAuth } from './components/AuthProvider';
import Chat from './components/Chat';
import Settings from './components/Settings';
import Login from './components/Login';
import './ExcomApp.css';

function ExcomApp() {
  const { isAuthenticated, isLoading, user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

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
      if (showMobileMenu && !event.target.closest('.mobile-menu-btn') && !event.target.closest('.mobile-nav')) {
        setShowMobileMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserMenu, showMobileMenu]);

  // Handle tab change
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setShowMobileMenu(false);
  };

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
        <button className="mobile-menu-btn" onClick={() => setShowMobileMenu(!showMobileMenu)}>
          <span></span>
          <span></span>
          <span></span>
        </button>
        <div className="app-logo">
          <img src="/logo.png" alt="excom.ai" className="logo-image" />
          <span className="logo-text">excom.ai</span>
        </div>
        <div className="app-tabs">
          <button
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => handleTabChange('chat')}
          >
            Chat
          </button>
          <button
            className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => handleTabChange('settings')}
          >
            Settings
          </button>
        </div>
        <div className="user-info">
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

      {/* Mobile Navigation */}
      <div className={`mobile-nav ${showMobileMenu ? 'open' : ''}`}>
        <div className="mobile-nav-header">
          <div className="app-logo">
            <img src="/logo.png" alt="excom.ai" className="logo-image" />
            <span className="logo-text">excom.ai</span>
          </div>
        </div>
        <div className="mobile-nav-tabs">
          <button
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => handleTabChange('chat')}
          >
            Chat
          </button>
          <button
            className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => handleTabChange('settings')}
          >
            Settings
          </button>
        </div>
      </div>
      {showMobileMenu && <div className="mobile-nav-overlay show" onClick={() => setShowMobileMenu(false)} />}

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