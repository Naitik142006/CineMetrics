import React from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { CurrencyProvider } from './context/CurrencyContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AuthModal } from './components/AuthModal';
import { Navbar } from './components/Navbar';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { UpcomingRadarPage } from './pages/UpcomingRadarPage';
import { MovieDossierPage } from './pages/MovieDossierPage';
import { WhatIfSimulatorPage } from './pages/WhatIfSimulatorPage';
import { MovieComparisonPage } from './pages/MovieComparisonPage';
import { MarketTrendsPage } from './pages/MarketTrendsPage';
import { TalentDossierPage } from './pages/TalentDossierPage';

const MainLayout: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  // The landing page handles its own full-bleed layout and footer
  const isLanding = location.pathname === '/landing' || (!isAuthenticated && location.pathname === '/');

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-[#F0F0F8] flex flex-col font-sans selection:bg-[#6C63FF]/30 selection:text-white">
      <AuthModal />
      {!isLanding && <Navbar />}

      <main className={isLanding ? 'flex-1 w-full' : 'flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-8'}>
        <Routes>
          <Route path="/" element={isAuthenticated ? <DashboardPage /> : <LandingPage />} />
          <Route path="/landing" element={<LandingPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/upcoming" element={<UpcomingRadarPage />} />
          <Route path="/movies/:id" element={<MovieDossierPage />} />
          <Route path="/simulate" element={<WhatIfSimulatorPage />} />
          <Route path="/compare" element={<MovieComparisonPage />} />
          <Route path="/market" element={<MarketTrendsPage />} />
          <Route path="/talent/:role/:name" element={<TalentDossierPage />} />
        </Routes>
      </main>

      {!isLanding && (
        <footer className="border-t border-[#2A2A3A]/60 py-8 px-4 text-center text-xs text-[#5A5A72] bg-[#0A0A0F]/80">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <p>
              © {new Date().getFullYear()} CineMetrics AI. Engineered for Cinema Intelligence, Empirical Research &amp; Risk Attribution.
            </p>
            <div className="flex items-center gap-4 text-[#9090AA]">
              <span>Ensemble v1.1.0-Stacked</span>
              <span>•</span>
              <span>TreeSHAP Exact Additivity</span>
              <span>•</span>
              <span>Split Conformal Uncertainty</span>
            </div>
          </div>
        </footer>
      )}
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <CurrencyProvider>
        <BrowserRouter>
          <MainLayout />
        </BrowserRouter>
      </CurrencyProvider>
    </AuthProvider>
  );
};

export default App;
