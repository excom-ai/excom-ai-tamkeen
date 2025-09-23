import React from 'react';
import ReactDOM from 'react-dom/client';
import { PublicClientApplication, EventType } from '@azure/msal-browser';
import { MsalProvider } from '@azure/msal-react';
import './index.css';
import ExcomApp from './ExcomApp';
import reportWebVitals from './reportWebVitals';
import { msalConfig } from './authConfig';
import { AuthProvider } from './components/AuthProvider';

// Initialize MSAL instance
const msalInstance = new PublicClientApplication(msalConfig);

// Handle redirect promises before rendering
msalInstance.handleRedirectPromise().then((response) => {
  if (response) {
    console.log('Redirect response received:', response);
    if (response.account) {
      console.log('Setting active account from redirect:', response.account);
      msalInstance.setActiveAccount(response.account);
    }
  } else {
    console.log('No redirect response - checking existing accounts');
    // Check if there are existing accounts
    const accounts = msalInstance.getAllAccounts();
    if (accounts.length > 0) {
      console.log('Found existing account:', accounts[0]);
      msalInstance.setActiveAccount(accounts[0]);
    }
  }
}).catch((error) => {
  console.error('Error handling redirect:', error);
});

// Account selection logic
if (!msalInstance.getActiveAccount() && msalInstance.getAllAccounts().length > 0) {
  msalInstance.setActiveAccount(msalInstance.getAllAccounts()[0]);
}

// Listen for sign-in events
msalInstance.addEventCallback((event) => {
  console.log('MSAL Event:', event.eventType, event);
  if (event.eventType === EventType.LOGIN_SUCCESS && event.payload.account) {
    const account = event.payload.account;
    console.log('Login success, setting active account:', account);
    msalInstance.setActiveAccount(account);
  }
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <MsalProvider instance={msalInstance}>
      <AuthProvider>
        <ExcomApp />
      </AuthProvider>
    </MsalProvider>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();