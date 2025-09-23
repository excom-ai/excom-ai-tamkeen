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

  // Force a recheck after component mounts to catch any missed authentication
  useEffect(() => {
    const timer = setTimeout(() => {
      const activeAccount = instance.getActiveAccount();
      const allAccounts = instance.getAllAccounts();
      console.log('Force recheck after mount:', { activeAccount, allAccounts });

      if (activeAccount && !isAuthenticated) {
        console.log('Found active account on recheck, setting authenticated');
        setUser(activeAccount);
        setIsAuthenticated(true);
        setIsLoading(false);
      } else if (allAccounts.length > 0 && !isAuthenticated) {
        console.log('Found accounts on recheck, setting authenticated');
        instance.setActiveAccount(allAccounts[0]);
        setUser(allAccounts[0]);
        setIsAuthenticated(true);
        setIsLoading(false);
      }
    }, 1000); // Wait 1 second after mount

    return () => clearTimeout(timer);
  }, [instance, isAuthenticated]);

  useEffect(() => {
    console.log('Auth state check:', {
      accountsLength: accounts?.length,
      inProgress,
      accounts,
      activeAccount: instance.getActiveAccount()
    });

    // Check both accounts array and active account
    const activeAccount = instance.getActiveAccount();
    const hasAccounts = accounts && accounts.length > 0;

    if (hasAccounts || activeAccount) {
      const accountToUse = activeAccount || accounts[0];
      console.log('User authenticated:', accountToUse);
      setUser(accountToUse);
      setIsAuthenticated(true);
    } else {
      console.log('No authenticated user found');
      setUser(null);
      setIsAuthenticated(false);
    }

    if (inProgress === InteractionStatus.None) {
      console.log('Setting loading to false');
      setIsLoading(false);
    }
  }, [accounts, inProgress, instance]);

  const login = async () => {
    try {
      // Use redirect instead of popup for more reliable authentication
      await instance.loginRedirect(loginRequest);
    } catch (error) {
      console.error('Login failed:', error);
      // Fallback to popup if redirect fails
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
            localStorage.setItem('accessToken', tokenResponse.accessToken);
          } catch (tokenError) {
            console.error('Token acquisition failed', tokenError);
          }
        }
      } catch (popupError) {
        console.error('Popup login also failed:', popupError);
      }
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