import React from 'react';
import './Settings.css';

function Settings({ settings, setSettings }) {
  const handleApiUrlChange = (e) => {
    setSettings(prev => ({ ...prev, apiUrl: e.target.value }));
  };

  const handleStreamingToggle = () => {
    setSettings(prev => ({ ...prev, streaming: !prev.streaming }));
  };


  const testConnection = async () => {
    try {
      const response = await fetch(`${settings.apiUrl}/api/health`);
      if (response.ok) {
        alert('Connection successful!');
      } else {
        alert('Connection failed. Please check the API URL.');
      }
    } catch (error) {
      alert(`Connection error: ${error.message}`);
    }
  };

  const resetToDefaults = () => {
    const defaults = {
      apiUrl: 'http://localhost:9000',
      streaming: false  // Disabled to enable tool usage
    };
    setSettings(defaults);
  };

  return (
    <div className="settings-container">
      <div className="settings-section">
        <h3 className="section-title">API Configuration</h3>
        <div className="settings-group">
          <label className="setting-label">
            API URL
            <input
              type="text"
              className="setting-input"
              value={settings.apiUrl}
              onChange={handleApiUrlChange}
              placeholder="http://localhost:9000"
            />
          </label>
          <button className="test-btn" onClick={testConnection}>
            🔌 Test Connection
          </button>
        </div>
      </div>

      <div className="settings-section">
        <h3 className="section-title">Chat Settings</h3>
        <div className="settings-group">
          <label className="setting-toggle">
            <input
              type="checkbox"
              checked={settings.streaming}
              onChange={handleStreamingToggle}
            />
            <span className="toggle-slider"></span>
            <span className="toggle-label">Enable Streaming Responses</span>
            <small style={{ display: 'block', marginTop: '8px', opacity: 0.7 }}>
              Note: Disable streaming to enable tool usage (JIRA/Freshservice queries)
            </small>
          </label>
        </div>
      </div>


      <div className="settings-section">
        <h3 className="section-title">About</h3>
        <div className="about-info">
          <p className="about-item">
            <span className="about-label">Version:</span>
            <span className="about-value">1.0.0</span>
          </p>
          <p className="about-item">
            <span className="about-label">Model:</span>
            <span className="about-value">Claude Sonnet 4</span>
          </p>
          <p className="about-item">
            <span className="about-label">Status:</span>
            <span className="about-value status-online">● Online</span>
          </p>
        </div>
      </div>

      <div className="settings-footer">
        <button className="reset-btn" onClick={resetToDefaults}>
          🔄 Reset to Defaults
        </button>
      </div>
    </div>
  );
}

export default Settings;