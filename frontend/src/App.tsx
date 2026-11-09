import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { CurrencyProvider } from './context/CurrencyContext';
import { Navbar } from './components/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { UpcomingRadarPage } from './pages/UpcomingRadarPage';
import { MovieDossierPage } from './pages/MovieDossierPage';
import { WhatIfSimulatorPage } from './pages/WhatIfSimulatorPage';
import { MovieComparisonPage } from './pages/MovieComparisonPage';
import { MarketTrendsPage } from './pages/MarketTrendsPage';
import { TalentDossierPage } from './pages/TalentDossierPage';

export const App: React.FC = () => {
  return (
    <CurrencyProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-[#0A0A0F] text-[#F0F0F8] flex flex-col font-sans selection:bg-[#6C63FF]/30 selection:text-white">
          <Navbar />

          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-8">
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/upcoming" element={<UpcomingRadarPage />} />
              <Route path="/movies/:id" element={<MovieDossierPage />} />
              <Route path="/simulate" element={<WhatIfSimulatorPage />} />
              <Route path="/compare" element={<MovieComparisonPage />} />
              <Route path="/market" element={<MarketTrendsPage />} />
              <Route path="/talent/:role/:name" element={<TalentDossierPage />} />
            </Routes>
          </main>

          <footer className="border-t border-[#2A2A3A]/60 py-8 px-4 text-center text-xs text-[#5A5A72] bg-[#0A0A0F]/80">
            <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
              <p>
                © 2026 CineMetrics AI. Engineered for Cinema Intelligence, Empirical Research & Risk Attribution.
              </p>
              <div className="flex items-center gap-4 text-[#9090AA]">
                <span>CatBoost v1.0.0</span>
                <span>•</span>
                <span>TreeSHAP Exact Additivity</span>
                <span>•</span>
                <span>Split Conformal Uncertainty</span>
              </div>
            </div>
          </footer>
        </div>
      </BrowserRouter>
    </CurrencyProvider>
  );
};

export default App;
