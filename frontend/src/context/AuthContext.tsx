import React, { createContext, useContext, useState, useEffect } from 'react';

export interface UserProfile {
  name: string;
  email: string;
  role: string;
  avatarInitials: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: UserProfile | null;
  login: (email?: string, name?: string) => void;
  logout: () => void;
  showAuthModal: boolean;
  openAuthModal: () => void;
  closeAuthModal: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = 'cinemetrics_auth_session';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [showAuthModal, setShowAuthModal] = useState(false);

  const login = (email?: string, name?: string) => {
    const userProfile: UserProfile = {
      name: name || 'CineMetrics User',
      email: email || 'user@cinemetrics.ai',
      role: 'User',
      avatarInitials: 'CU',
    };
    setUser(userProfile);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(userProfile));
    } catch (e) {
      console.warn('Storage unavailable:', e);
    }
    setShowAuthModal(false);
  };

  const logout = () => {
    setUser(null);
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
        isAuthenticated: !!user,
        user,
        login,
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

