import React from 'react';

function HelloWorld() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '400px',
      padding: '2rem'
    }}>
      <h1 style={{
        fontSize: '4rem',
        background: 'linear-gradient(90deg, #4fc3f7, #29b6f6)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        marginBottom: '1rem'
      }}>
        Hello World!
      </h1>
      <p style={{
        fontSize: '1.5rem',
        color: '#9e9e9e'
      }}>
        Welcome to Tamkeen ERP
      </p>
      <div style={{
        marginTop: '2rem',
        padding: '1rem 2rem',
        background: 'rgba(79, 195, 247, 0.1)',
        border: '1px solid rgba(79, 195, 247, 0.3)',
        borderRadius: '8px'
      }}>
        <p>This is a simple Hello World page using the UI Core library</p>
      </div>
    </div>
  );
}

export default HelloWorld;