import React from 'react';
import { useAuth } from './AuthProvider';
import './Login.css';

const Login = () => {
  const { login, isLoading } = useAuth();

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-logo">
          <img src="/logo.png" alt="excom.ai" className="login-logo-img" />
        </div>
        <h1 className="login-title">Welcome to excom.ai</h1>
        <p className="login-subtitle">Sign in with your Microsoft account to continue</p>

        <button
          className="login-button"
          onClick={login}
          disabled={isLoading}
        >
          {isLoading ? (
            <span className="login-button-loading">Loading...</span>
          ) : (
            <>
              <svg className="ms-logo" viewBox="0 0 21 21" xmlns="http://www.w3.org/2000/svg">
                <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
                <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
                <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
                <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
              </svg>
              Sign in with Microsoft
            </>
          )}
        </button>

        <p className="login-footer">
          Securely authenticated via Microsoft Entra ID
        </p>
      </div>
    </div>
  );
};

export default Login;