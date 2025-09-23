import React, { createContext, useContext, useEffect, useState } from 'react';
import { useMsal } from '@azure/msal-react';
import { InteractionStatus } from '@azure/msal-browser';
import { loginRequest } from '../authConfig';

const AuthContext = createContext({});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const { instance, accounts, inProgress } = useMsal();
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (accounts && accounts.length > 0) {
      setUser(accounts[0]);
      setIsAuthenticated(true);
    } else {
      setUser(null);
      setIsAuthenticated(false);
    }

    if (inProgress === InteractionStatus.None) {
      setIsLoading(false);
    }
  }, [accounts, inProgress]);

  const login = async () => {
    try {
      const loginResponse = await instance.loginPopup(loginRequest);
      if (loginResponse) {
        setUser(loginResponse.account);
        setIsAuthenticated(true);

        // Get the access token for API calls
        const tokenRequest = {
          scopes: loginRequest.scopes,
          account: loginResponse.account
        };

        try {
          const tokenResponse = await instance.acquireTokenSilent(tokenRequest);
          // Store token for API calls
          localStorage.setItem('accessToken', tokenResponse.accessToken);
        } catch (error) {
          console.error('Silent token acquisition failed, using popup', error);
          const tokenResponse = await instance.acquireTokenPopup(tokenRequest);
          localStorage.setItem('accessToken', tokenResponse.accessToken);
        }
      }
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const logout = () => {
    localStorage.removeItem('accessToken');
    instance.logoutPopup({
      postLogoutRedirectUri: '/',
      mainWindowRedirectUri: '/'
    });
  };

  const getAccessToken = async () => {
    if (!accounts || accounts.length === 0) {
      return null;
    }

    const tokenRequest = {
      scopes: loginRequest.scopes,
      account: accounts[0]
    };

    try {
      const tokenResponse = await instance.acquireTokenSilent(tokenRequest);
      return tokenResponse.accessToken;
    } catch (error) {
      console.error('Silent token acquisition failed', error);
      try {
        const tokenResponse = await instance.acquireTokenPopup(tokenRequest);
        return tokenResponse.accessToken;
      } catch (popupError) {
        console.error('Token acquisition failed', popupError);
        return null;
      }
    }
  };

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    getAccessToken
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};