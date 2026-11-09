import React, { createContext, useContext, useState, ReactNode } from 'react';
import { CurrencyMode } from '../types';

interface CurrencyContextType {
  currency: CurrencyMode;
  toggleCurrency: () => void;
  setCurrency: (mode: CurrencyMode) => void;
}

const CurrencyContext = createContext<CurrencyContextType | undefined>(undefined);

export const CurrencyProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currency, setCurrencyState] = useState<CurrencyMode>(() => {
    return (localStorage.getItem('cinemetrics_currency') as CurrencyMode) || 'USD';
  });

  const toggleCurrency = () => {
    const next = currency === 'USD' ? 'INR' : 'USD';
    setCurrencyState(next);
    localStorage.setItem('cinemetrics_currency', next);
  };

  const setCurrency = (mode: CurrencyMode) => {
    setCurrencyState(mode);
    localStorage.setItem('cinemetrics_currency', mode);
  };

  return (
    <CurrencyContext.Provider value={{ currency, toggleCurrency, setCurrency }}>
      {children}
    </CurrencyContext.Provider>
  );
};

export const useCurrency = (): CurrencyContextType => {
  const context = useContext(CurrencyContext);
  if (!context) {
    throw new Error('useCurrency must be used within a CurrencyProvider');
  }
  return context;
};
