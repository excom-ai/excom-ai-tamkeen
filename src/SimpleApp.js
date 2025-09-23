import React from 'react';

function SimpleApp() {
  return (
    <div style={{
      minHeight: '100vh',
      background: '#0a0f1b',
      color: '#e0e0e0',
      padding: '2rem',
      fontFamily: 'monospace'
    }}>
      <h1 style={{ color: '#4fc3f7' }}>Simple Test App</h1>
      <p>This is a simple test without ui-core to verify the app works.</p>
      <div style={{
        marginTop: '2rem',
        padding: '1rem',
        background: 'rgba(79, 195, 247, 0.1)',
        border: '1px solid rgba(79, 195, 247, 0.3)',
        borderRadius: '8px'
      }}>
        <h2>Hello World!</h2>
        <p>If you can see this, the React app is working correctly.</p>
      </div>
    </div>
  );
}

export default SimpleApp;