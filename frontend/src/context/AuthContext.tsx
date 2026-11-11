import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '../services/api';

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: string;
  avatarInitials: string;
}

interface StoredSession {
  token: string;
  user: UserProfile;
}

interface AuthContextType {
  isAuthenticated: boolean;
  isLoadingAuth: boolean;
  user: UserProfile | null;
  loginWithCredentials: (email: string, password: string) => Promise<void>;
  registerAccount: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  showAuthModal: boolean;
  openAuthModal: () => void;
  closeAuthModal: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = 'cinemetrics_auth_session';

function readStoredSession(): StoredSession | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.token === 'string' && parsed.user?.email) {
      return parsed as StoredSession;
    }
    // Clear legacy demo-only localStorage sessions without a signed backend token
    localStorage.removeItem(STORAGE_KEY);
    return null;
  } catch {
    return null;
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const initialSession = readStoredSession();
  const [user, setUser] = useState<UserProfile | null>(initialSession?.user ?? null);
  const [token, setToken] = useState<string | null>(initialSession?.token ?? null);
  const [isLoadingAuth, setIsLoadingAuth] = useState<boolean>(!!initialSession?.token);
  const [showAuthModal, setShowAuthModal] = useState(false);

  useEffect(() => {
    if (!token) {
      setIsLoadingAuth(false);
      return;
    }
    let active = true;
    apiService
      .getCurrentUser(token)
      .then((verifiedUser) => {
        if (!active) return;
        setUser(verifiedUser);
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify({ token, user: verifiedUser }));
        } catch {
          // ignore storage write failure
        }
      })
      .catch((err) => {
        if (!active) return;
        // Clear session when token is invalid/expired (401); keep session if backend is temporarily unreachable
        if (err?.response?.status === 401) {
          setUser(null);
          setToken(null);
          try {
            localStorage.removeItem(STORAGE_KEY);
          } catch {
            // ignore
          }
        }
      })
      .finally(() => {
        if (active) setIsLoadingAuth(false);
      });

    return () => {
      active = false;
    };
  }, [token]);

  const persistSession = (newToken: string, newUser: UserProfile) => {
    setToken(newToken);
    setUser(newUser);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ token: newToken, user: newUser }));
    } catch (e) {
      console.warn('Storage unavailable:', e);
    }
    setShowAuthModal(false);
  };

  const loginWithCredentials = async (email: string, password: string) => {
    const data = await apiService.login(email, password);
    persistSession(data.token, data.user);
  };

  const registerAccount = async (name: string, email: string, password: string) => {
    const data = await apiService.register(name, email, password);
    persistSession(data.token, data.user);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      console.warn('Storage unavailable:', e);
    }
  };

  const openAuthModal = () => setShowAuthModal(true);
  const closeAuthModal = () => setShowAuthModal(false);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: !!(user && token),
        isLoadingAuth,
        user,
        loginWithCredentials,
        registerAccount,
        logout,
        showAuthModal,
        openAuthModal,
        closeAuthModal,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
