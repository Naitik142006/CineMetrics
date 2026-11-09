import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCurrency } from '../context/CurrencyContext';
import { formatCurrency } from '../utils/format';
import { Cinema3DCanvas } from '../components/Cinema3DCanvas';
import {
  Film,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  TrendingUp,
  Sliders,
  DollarSign,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Layers,
  Activity,
  Compass,
  Play,
  Zap,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const { openAuthModal, isAuthenticated } = useAuth();
  const { currency, toggleCurrency } = useCurrency();
  const navigate = useNavigate();

  // Interactive Live Hero Tentpole Superposition Demo
  const [selectedHeroMovie, setSelectedHeroMovie] = useState<number>(0);
  const [heroStage, setHeroStage] = useState<'stage1' | 'stage4'>('stage4');

  const marqueeDemos = [
    {
      title: 'Avengers: Doomsday',
      year: '2026',
      director: 'Anthony & Joe Russo',
      star: 'Robert Downey Jr. (Doctor Doom)',
      budgetUsd: 275_000_000,
      stage1GrossUsd: 1_380_000_000,
      stage1LowUsd: 940_000_000,
      stage1HighUsd: 1_820_000_000,
      stage4GrossUsd: 1_450_000_000,
      stage4LowUsd: 1_360_000_000,
      stage4HighUsd: 1_540_000_000,
      readiness: 94,
      tag: 'Marvel MCU Event Tentpole',
    },
    {
      title: 'Kalki 2898 AD: Part 2',
      year: '2026',
      director: 'Nag Ashwin',
      star: 'Prabhas, Amitabh Bachchan, Kamal Haasan',
      budgetUsd: 75_000_000, // ~600 Cr
      stage1GrossUsd: 155_000_000,
      stage1LowUsd: 105_000_000,
      stage1HighUsd: 215_000_000,
      stage4GrossUsd: 168_000_000,
      stage4LowUsd: 156_000_000,
      stage4HighUsd: 180_000_000,
      readiness: 88,
      tag: 'Pan-Indian Sci-Fi Mythology',
    },
    {
      title: 'The Batman: Part II',
      year: '2026',
      director: 'Matt Reeves',
      star: 'Robert Pattinson, Colin Farrell',
      budgetUsd: 190_000_000,
      stage1GrossUsd: 820_000_000,
      stage1LowUsd: 560_000_000,
      stage1HighUsd: 1_080_000_000,
      stage4GrossUsd: 855_000_000,
      stage4LowUsd: 795_000_000,
      stage4HighUsd: 915_000_000,
      readiness: 86,
      tag: 'DC Elseworlds Crime Epic',
    },
  ];

  const currentDemo = marqueeDemos[selectedHeroMovie];
  const isStage4 = heroStage === 'stage4';
  const displayGross = isStage4 ? currentDemo.stage4GrossUsd : currentDemo.stage1GrossUsd;
  const displayLow = isStage4 ? currentDemo.stage4LowUsd : currentDemo.stage1LowUsd;
  const displayHigh = isStage4 ? currentDemo.stage4HighUsd : currentDemo.stage1HighUsd;

  const handleEnterTerminal = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    } else {
      openAuthModal();
    }
  };

  return (
    <div className="relative min-h-screen bg-[#07070B] text-[#F0F0F8] font-sans selection:bg-[#E8B74A]/30 selection:text-white overflow-x-hidden">
      {/* ========================================================================= */}
      {/* 1. TOP BAR — "CineMetrics Horizon OS" Header */}
      {/* ========================================================================= */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#07070B]/80 backdrop-blur-xl border-b border-[#1E1E2C]/80 px-4 sm:px-8 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          {/* Brand Logo & Protocol Version */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#E8B74A] to-[#6C63FF] p-[1.5px] shadow-lg shadow-[#E8B74A]/10">
              <div className="w-full h-full bg-[#07070B] rounded-[6.5px] flex items-center justify-center">
                <Film className="w-4 h-4 text-[#E8B74A]" />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-mono font-extrabold text-sm sm:text-base tracking-wider text-white">
                CINEMETRICS
              </span>
              <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-[#E8B74A]/10 text-[#E8B74A] border border-[#E8B74A]/30 font-semibold">
                PROTOCOL 2026
              </span>
            </div>
          </div>

          {/* Center Navigation Anchors */}
          <nav className="hidden lg:flex items-center gap-6 font-mono text-xs text-[#9090AA]">
            <a href="#superposition" className="hover:text-white transition-colors">
              • QUANTUM SUPERPOSITION
            </a>
            <a href="#paradox" className="hover:text-white transition-colors">
              • THE BLIND SPOT
            </a>
            <a href="#dimensions" className="hover:text-white transition-colors">
              • 4 DIMENSIONS
            </a>
            <a href="#marquee" className="hover:text-white transition-colors">
              • MARQUEE PORTFOLIO
            </a>
          </nav>

          {/* Right Action Bar */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Currency Pill */}
            <button
              onClick={toggleCurrency}
              title="Toggle Global Currency (USD / INR)"
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#111118] border border-[#2A2A3A] hover:border-[#E8B74A]/60 text-xs font-mono font-bold transition-all text-white cursor-pointer"
            >
              <DollarSign className="w-3 h-3 text-[#E8B74A]" />
              <span className={currency === 'USD' ? 'text-[#E8B74A]' : 'text-[#9090AA]'}>USD</span>
              <span className="text-[#5A5A72]">/</span>
              <span className={currency === 'INR' ? 'text-[#E8B74A]' : 'text-[#9090AA]'}>INR</span>
            </button>

            {isAuthenticated ? (
              <button
                onClick={() => navigate('/dashboard')}
                className="px-4 py-1.5 rounded-lg bg-[#E8B74A] text-black font-semibold text-xs hover:bg-[#F3C766] transition-all cursor-pointer flex items-center gap-1.5 shadow-lg shadow-[#E8B74A]/20"
              >
                <span>OPEN DASHBOARD</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <>
                <button
                  onClick={openAuthModal}
                  className="px-3 py-1.5 rounded-lg text-xs font-mono text-[#9090AA] hover:text-white transition-colors cursor-pointer"
                >
                  SIGN IN
                </button>
                <button
                  onClick={openAuthModal}
                  className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-[#E8B74A] to-[#D49E28] hover:from-[#F3C766] hover:to-[#E8B74A] text-black font-bold text-xs transition-all cursor-pointer flex items-center gap-1.5 shadow-lg shadow-[#E8B74A]/25"
                >
                  <span>EXECUTIVE ACCESS</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ========================================================================= */}
      {/* 2. HERO SECTION — The Collapse of Theatrical Uncertainty */}
      {/* ========================================================================= */}
      <section id="superposition" className="relative min-h-screen flex flex-col justify-center px-4 sm:px-8 pt-28 pb-16">
        {/* 3D Anamorphic Crystal Canvas */}
        <Cinema3DCanvas intensity={1.15} />

        {/* Cinematic Vignette */}
        <div className="absolute inset-0 bg-radial-gradient pointer-events-none from-transparent via-[#07070B]/70 to-[#07070B]" />

        <div className="relative max-w-7xl mx-auto w-full z-10 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column: Mission Statement */}
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#111118]/80 border border-[#2A2A3A] text-xs font-mono text-[#E8B74A]">
              <span className="w-2 h-2 rounded-full bg-[#E8B74A] animate-ping" />
              <span>THE ARCHITECTURE OF THEATRICAL CERTAINTY</span>
            </div>

            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-[1.06]">
              WE FORECAST <br />
              <span className="bg-gradient-to-r from-white via-zinc-100 to-[#E8B74A] bg-clip-text text-transparent">
                BOX OFFICE BEFORE
              </span> <br />
              THE CAMERAS WRAP.
            </h1>

            <p className="max-w-xl text-sm sm:text-base text-[#9090AA] leading-relaxed font-normal">
              The entertainment industry write-downs exceed <strong>$4.8 Billion annually</strong> on uncalibrated producer gut-feeling. CineMetrics unifies 3-way gradient boosting ensembles, TreeSHAP dollar attribution, and live multiplex seating physics to turn movie greenlights into mathematical ground truth.
            </p>

            {/* Action Bar */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <button
                onClick={handleEnterTerminal}
                className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-[#E8B74A] to-[#D49E28] hover:from-[#F3C766] hover:to-[#E8B74A] text-black font-extrabold text-sm transition-all cursor-pointer flex items-center gap-2.5 shadow-xl shadow-[#E8B74A]/25 group"
              >
                <span>{isAuthenticated ? 'LAUNCH DASHBOARD' : 'INITIALIZE STUDIO TERMINAL'}</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>

              <button
                onClick={() => {
                  if (isAuthenticated) navigate('/simulate');
                  else openAuthModal();
                }}
                className="px-5 py-3.5 rounded-xl bg-[#111118]/80 hover:bg-[#1A1A26] border border-[#2A2A3A] hover:border-[#6C63FF]/70 text-white font-mono text-xs transition-all cursor-pointer flex items-center gap-2"
              >
                <Sliders className="w-4 h-4 text-[#6C63FF]" />
                <span>[TEST WHAT-IF ENGINE]</span>
              </button>
            </div>

            {/* Live Model Stats Ticker */}
            <div className="pt-4 border-t border-[#1E1E2C] grid grid-cols-3 gap-4 text-xs font-mono">
              <div>
                <p className="text-[#5A5A72] text-[10px] uppercase">Stage 4 Precision</p>
                <p className="text-[#E8B74A] font-bold text-sm">R² ≥ 0.925 (±8.6%)</p>
              </div>
              <div>
                <p className="text-[#5A5A72] text-[10px] uppercase">Conformal Guarantees</p>
                <p className="text-emerald-400 font-bold text-sm">93.39% Empirical</p>
              </div>
              <div>
                <p className="text-[#5A5A72] text-[10px] uppercase">Model Latency</p>
                <p className="text-purple-400 font-bold text-sm">&lt; 18ms TreeSHAP</p>
              </div>
            </div>
          </div>

          {/* Right Column: Live Interactive "Superposition Collider" Widget */}
          <div className="lg:col-span-5">
            <div className="relative rounded-2xl bg-[#0E0E16]/90 border border-[#2A2A3A] p-6 shadow-2xl backdrop-blur-xl space-y-5">
              {/* Widget Header */}
              <div className="flex items-center justify-between border-b border-[#1E1E2C] pb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="font-mono text-xs text-white uppercase tracking-wider font-bold">
                    Superposition Collider
                  </span>
                </div>
                <span className="font-mono text-[10px] text-[#9090AA] px-2 py-0.5 rounded bg-[#1A1A26] border border-[#2A2A3A]">
                  LIVE DEMO
                </span>
              </div>

              {/* Movie Selector Tabs */}
              <div className="flex gap-2 p-1 bg-[#151520] rounded-xl border border-[#2A2A3A]">
                {marqueeDemos.map((m, idx) => (
                  <button
                    key={m.title}
                    onClick={() => setSelectedHeroMovie(idx)}
                    className={`flex-1 py-1.5 text-[11px] font-mono rounded-lg transition-all cursor-pointer ${
                      selectedHeroMovie === idx
                        ? 'bg-[#E8B74A] text-black font-bold shadow-md'
                        : 'text-[#9090AA] hover:text-white'
                    }`}
                  >
                    {m.title.split(':')[0]}
                  </button>
                ))}
              </div>

              {/* Title & Metadata */}
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-bold text-white">{currentDemo.title}</h3>
                  <span className="text-xs font-mono text-[#E8B74A] font-bold">
                    {currentDemo.year}
                  </span>
                </div>
                <p className="text-xs text-[#9090AA] mt-0.5">
                  Dir: {currentDemo.director} • Star: {currentDemo.star}
                </p>
                <span className="inline-block mt-2 text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#6C63FF]/15 text-[#9090AA] border border-[#6C63FF]/30">
                  {currentDemo.tag}
                </span>
              </div>

              {/* Stage Toggle (Announcement vs. Pre-Sales) */}
              <div className="p-3 rounded-xl bg-[#151520] border border-[#2A2A3A] space-y-3">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-[#9090AA]">Simulate Lifecycle Phase:</span>
                  <div className="flex gap-1.5">
                    <button
                      onClick={() => setHeroStage('stage1')}
                      className={`px-2.5 py-1 rounded-md text-[11px] transition-all cursor-pointer ${
                        !isStage4
                          ? 'bg-[#2A2A3A] text-white font-bold'
                          : 'text-[#9090AA] hover:text-white'
                      }`}
                    >
                      Stage 1 (Prior)
                    </button>
                    <button
                      onClick={() => setHeroStage('stage4')}
                      className={`px-2.5 py-1 rounded-md text-[11px] transition-all cursor-pointer ${
                        isStage4
                          ? 'bg-[#6C63FF] text-white font-bold shadow-md'
                          : 'text-[#9090AA] hover:text-white'
                      }`}
                    >
                      Stage 4 (Pre-Sales)
                    </button>
                  </div>
                </div>

                {/* Forecast Display */}
                <div className="pt-2 border-t border-[#2A2A3A]/60 flex items-baseline justify-between">
                  <div>
                    <span className="text-[10px] font-mono uppercase text-[#9090AA]">
                      {isStage4 ? 'Stage 4 Bayesian Forecast:' : 'Stage 1 Announcement Prior:'}
                    </span>
                    <p className={`text-2xl font-black font-mono ${isStage4 ? 'text-[#E8B74A]' : 'text-zinc-200'}`}>
                      {formatCurrency(displayGross, currency)}
                    </p>
                  </div>
                  <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded-full ${
                    isStage4 ? 'bg-purple-950 text-purple-300 border border-purple-500/50' : 'bg-[#2A2A3A] text-zinc-400'
                  }`}>
                    {isStage4 ? 'R² ≥ 0.925' : 'R² = 0.680'}
                  </span>
                </div>

                {/* Uncertainty Band Comparison */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-[11px] font-mono text-[#9090AA]">
                    <span>80% Confidence Interval:</span>
                    <span className="text-zinc-300">
                      {formatCurrency(displayLow, currency)} – {formatCurrency(displayHigh, currency)}
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-[#111118] overflow-hidden p-0.5 border border-[#2A2A3A]">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isStage4 ? 'bg-gradient-to-r from-[#6C63FF] to-[#E8B74A] w-4/5' : 'bg-zinc-500 w-2/5'
                      }`}
                    />
                  </div>
                  <p className="text-[10px] font-mono text-[#5A5A72] text-right">
                    {isStage4 ? '⚡ Uncertainty collapsed by 75.6%' : 'Wide pre-production confidence cone (±32%)'}
                  </p>
                </div>
              </div>

              {/* Action */}
              <button
                onClick={handleEnterTerminal}
                className="w-full py-2.5 rounded-xl bg-white hover:bg-zinc-200 text-black font-bold text-xs font-mono transition-all cursor-pointer flex items-center justify-center gap-2 shadow-lg shadow-white/10"
              >
                <span>OPEN FULL DOSSIER IN TERMINAL</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 3. THE PARADOX — Traditional Studio Guesswork vs. CineMetrics Ground Truth */}
      {/* ========================================================================= */}
      <section id="paradox" className="relative py-24 px-4 sm:px-8 border-t border-[#1E1E2C] bg-[#0A0A10]">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <span className="text-xs font-mono text-[#E8B74A] uppercase tracking-wider font-semibold">
              [THE DUALITY PARADOX]
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              THE $4.8 BILLION STUDIO BLIND SPOT
            </h2>
            <p className="text-sm text-[#9090AA] leading-relaxed">
              Why traditional Hollywood and Bollywood greenlighting fails, and how mathematical calibration replaces gut optimism.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Card 1: Traditional Method */}
            <div className="p-7 rounded-2xl bg-[#0E0E16] border border-red-500/20 space-y-5 relative overflow-hidden">
              <div className="flex items-center gap-2.5 text-red-400 font-mono text-xs font-bold uppercase tracking-wider">
                <AlertTriangle className="w-4 h-4" />
                <span>Traditional Producer Guesswork</span>
              </div>
              <h3 className="text-xl font-bold text-white">The Committee Blind Spot</h3>
              <p className="text-xs text-[#9090AA] leading-relaxed">
                Greenlights decided by executive seniority, anecdotal past hits, and emotional attachments to IP. Completely blindsided by format fatigue, shifting audience demographics, and uncalibrated budgets.
              </p>

              <div className="space-y-2.5 pt-2 font-mono text-xs text-red-300">
                <div className="p-3 rounded-xl bg-red-950/20 border border-red-500/30 flex items-center justify-between">
                  <span>Joker: Folie à Deux ($200M Budget)</span>
                  <span className="font-bold">-$150M Loss</span>
                </div>
                <div className="p-3 rounded-xl bg-red-950/20 border border-red-500/30 flex items-center justify-between">
                  <span>The Marvels ($220M Budget)</span>
                  <span className="font-bold">-$180M Loss</span>
                </div>
                <div className="p-3 rounded-xl bg-red-950/20 border border-red-500/30 flex items-center justify-between">
                  <span>Borderlands ($120M Budget)</span>
                  <span className="font-bold">-$100M Loss</span>
                </div>
              </div>
            </div>

            {/* Card 2: The CineMetrics Protocol */}
            <div className="p-7 rounded-2xl bg-[#11111E] border border-[#E8B74A]/40 space-y-5 relative overflow-hidden shadow-2xl shadow-[#E8B74A]/10">
              <div className="flex items-center gap-2.5 text-[#E8B74A] font-mono text-xs font-bold uppercase tracking-wider">
                <CheckCircle2 className="w-4 h-4" />
                <span>The CineMetrics Protocol</span>
              </div>
              <h3 className="text-xl font-bold text-white">Statistical Ground Truth</h3>
              <p className="text-xs text-zinc-300 leading-relaxed">
                Empirical feature attribution. We evaluate 2,600+ directors and 2,500+ actors without lookahead leakage. TreeSHAP proves which actor or release month drives value, while Split Conformal intervals bound downside catastrophe before capital expenditure.
              </p>

              <div className="space-y-2.5 pt-2 font-mono text-xs text-emerald-300">
                <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 flex items-center justify-between">
                  <span>3-Way Stacking Ensemble</span>
                  <span className="font-bold">R² = 0.473 (Pre-Release)</span>
                </div>
                <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 flex items-center justify-between">
                  <span>TreeSHAP Local Attribution</span>
                  <span className="font-bold">Machine Precision &lt; 1e-4</span>
                </div>
                <div className="p-3 rounded-xl bg-purple-950/20 border border-purple-500/40 flex items-center justify-between text-purple-300">
                  <span>Stage 4 Pre-Sales Velocity</span>
                  <span className="font-bold">R² ≥ 0.925 (±8.6% Error)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 4. FOUR DIMENSIONS OF PREDICTABILITY — The Original 4-Pillar Grid */}
      {/* ========================================================================= */}
      <section id="dimensions" className="relative py-24 px-4 sm:px-8 border-t border-[#1E1E2C] bg-[#07070B]">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="space-y-2">
            <span className="text-xs font-mono text-[#6C63FF] uppercase tracking-wider font-semibold">
              [FOUR DIMENSIONS OF PREDICTABILITY]
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              HOW CINEMETRICS CRACKS THE BOX OFFICE
            </h2>
            <p className="text-sm text-[#9090AA] max-w-2xl">
              Four domain-engineered machine learning engines operating in harmony to eliminate financial blind spots.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Dimension 1 */}
            <div className="p-6 rounded-2xl bg-[#0E0E16] border border-[#2A2A3A] hover:border-[#E8B74A]/60 transition-all space-y-4 group">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#E8B74A] font-bold">DIMENSION I</span>
                <span className="text-[#5A5A72]">TALENT EQUITY ENGINE</span>
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-[#E8B74A] transition-colors">
                Ordered Target Statistics on Talent
              </h3>
              <p className="text-xs text-[#9090AA] leading-relaxed">
                Director career hit rates and lead actor historical ROI multiples are calculated strictly using chronological snapshots (zero future leakage). Oblivious trees in CatBoost prevent overfitting on small sample sizes.
              </p>
              <div className="pt-2 text-[11px] font-mono text-[#5A5A72] flex items-center gap-3">
                <span>• 2,608 Directors Evaluated</span>
                <span>• 2,526 Lead Actors Tracked</span>
              </div>
            </div>

            {/* Dimension 2 */}
            <div className="p-6 rounded-2xl bg-[#0E0E16] border border-[#2A2A3A] hover:border-[#6C63FF]/60 transition-all space-y-4 group">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#6C63FF] font-bold">DIMENSION II</span>
                <span className="text-[#5A5A72]">AUDIENCE VELOCITY NLP</span>
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-[#6C63FF] transition-colors">
                Multilingual YouTube Trailer Velocity
              </h3>
              <p className="text-xs text-[#9090AA] leading-relaxed">
                Free YouTube views don't predict ticket sales without passion. We fuse daily view accumulation velocity (Δviews / Δt), like-to-view ratios, and domain-adapted cinema sentiment for English and Indian regional slang.
              </p>
              <div className="pt-2 text-[11px] font-mono text-[#5A5A72] flex items-center gap-3">
                <span>• Sub-Millisecond CPU Inference</span>
                <span>• Hinglish &amp; Emoji Valence</span>
              </div>
            </div>

            {/* Dimension 3 */}
            <div className="p-6 rounded-2xl bg-[#0E0E16] border border-[#2A2A3A] hover:border-purple-500/60 transition-all space-y-4 group">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-purple-400 font-bold">DIMENSION III</span>
                <span className="text-[#5A5A72]">PRE-SALES SEATING PHYSICS</span>
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-purple-300 transition-colors">
                Stage 4 Conjugate Bayesian Updating
              </h3>
              <p className="text-xs text-[#9090AA] leading-relaxed">
                When tickets go on sale 7 days before opening night, pre-sales velocity replaces casual curiosity. The Bayesian posterior snaps the forecast to real money with 75.6% variance shrinkage and $R^2 \ge 0.925$.
              </p>
              <div className="pt-2 text-[11px] font-mono text-[#5A5A72] flex items-center gap-3">
                <span>• Multiplex Screen Capacity Bounding</span>
                <span>• MAPE ±8.6%</span>
              </div>
            </div>

            {/* Dimension 4 */}
            <div className="p-6 rounded-2xl bg-[#0E0E16] border border-[#2A2A3A] hover:border-emerald-500/60 transition-all space-y-4 group">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-emerald-400 font-bold">DIMENSION IV</span>
                <span className="text-[#5A5A72]">COUNTERFACTUAL SANDBOX</span>
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-emerald-300 transition-colors">
                Studio What-If Simulator Digital Twin
              </h3>
              <p className="text-xs text-[#9090AA] leading-relaxed">
                Test alternative production choices before greenlighting: What if we cast Ryan Reynolds instead of Chris Pratt? What if we move release from September to Christmas? Generates exact dollar delta with causal TreeSHAP breakdown.
              </p>
              <div className="pt-2 text-[11px] font-mono text-[#5A5A72] flex items-center gap-3">
                <span>• Instantaneous Scenario Evaluation</span>
                <span>• Break-Even Probability</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 5. MARQUEE PORTFOLIO PREVIEW — Live Tentpoles from CineMetrics Catalog */}
      {/* ========================================================================= */}
      <section id="marquee" className="relative py-24 px-4 sm:px-8 border-t border-[#1E1E2C] bg-[#0A0A10]">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4">
            <div className="space-y-2">
              <span className="text-xs font-mono text-[#E8B74A] uppercase tracking-wider font-semibold">
                [THE MARQUEE 100 RADAR]
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                ACTIVE 2026–2027 TENTPOLE TRACKING
              </h2>
              <p className="text-xs sm:text-sm text-[#9090AA]">
                CineMetrics continuously tracks over 100 announced theatrical releases worldwide.
              </p>
            </div>

            <button
              onClick={() => {
                if (isAuthenticated) navigate('/upcoming');
                else openAuthModal();
              }}
              className="px-4 py-2 rounded-xl bg-[#151520] hover:bg-[#202030] border border-[#2A2A3A] hover:border-[#E8B74A]/60 text-white font-mono text-xs transition-all cursor-pointer flex items-center gap-2"
            >
              <span>[EXPLORE FULL RADAR]</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              {
                title: 'Spider-Man: Beyond the Spider-Verse',
                date: 'Summer 2026',
                forecast: 950_000_000,
                readiness: 90,
                badge: 'Stage 3 Refined',
                badgeColor: 'text-amber-300 bg-amber-950/60 border-amber-500/40',
              },
              {
                title: 'Avengers: Secret Wars',
                date: 'May 2027',
                forecast: 1_850_000_000,
                readiness: 84,
                badge: 'Stage 2 Teaser',
                badgeColor: 'text-blue-300 bg-blue-950/60 border-blue-500/40',
              },
              {
                title: 'Toy Story 5',
                date: 'June 2026',
                forecast: 920_000_000,
                readiness: 82,
                badge: 'Stage 2 Teaser',
                badgeColor: 'text-blue-300 bg-blue-950/60 border-blue-500/40',
              },
              {
                title: 'Pushpa 2: The Rule (Theatrical Actuals)',
                date: 'Released',
                forecast: 145_000_000,
                readiness: 100,
                badge: 'Stage 5 Synchronized',
                badgeColor: 'text-emerald-300 bg-emerald-950/60 border-emerald-500/40',
              },
            ].map((m) => (
              <div
                key={m.title}
                className="p-5 rounded-2xl bg-[#0E0E16] border border-[#2A2A3A] hover:border-[#6C63FF]/50 transition-all flex flex-col justify-between space-y-4 group"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <span className="text-[#5A5A72]">{m.date}</span>
                    <span className={`px-2 py-0.5 rounded-full border text-[10px] ${m.badgeColor}`}>
                      {m.badge}
                    </span>
                  </div>
                  <h4 className="text-base font-bold text-white group-hover:text-[#E8B74A] transition-colors leading-snug">
                    {m.title}
                  </h4>
                </div>

                <div className="pt-3 border-t border-[#1E1E2C] flex items-baseline justify-between font-mono">
                  <div>
                    <span className="text-[10px] text-[#5A5A72] uppercase">Projected Gross</span>
                    <p className="text-lg font-extrabold text-[#E8B74A]">{formatCurrency(m.forecast, currency)}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-[#5A5A72] uppercase">Readiness</span>
                    <p className="text-sm font-bold text-zinc-300">{m.readiness}/100</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 6. CALL TO ACTION & TERMINAL AUTHORIZATION GATEWAY */}
      {/* ========================================================================= */}
      <section className="relative py-28 px-4 sm:px-8 border-t border-[#1E1E2C] bg-[#07070B] text-center">
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="inline-block px-3 py-1 rounded-full bg-[#111118] border border-[#2A2A3A] text-xs font-mono text-[#E8B74A]">
            PROTOCOL CLEARANCE // PRODUCTION LEVEL
          </div>

          <h2 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
            INITIALIZE YOUR STUDIO TERMINAL
          </h2>

          <p className="text-sm text-[#9090AA] max-w-xl mx-auto leading-relaxed">
            Gain immediate access to full counterfactual simulation, TreeSHAP waterfall attributions, and Stage 4 pre-sales sensitivity models.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <button
              onClick={handleEnterTerminal}
              className="px-8 py-3.5 rounded-xl bg-gradient-to-r from-[#E8B74A] to-[#D49E28] hover:from-[#F3C766] hover:to-[#E8B74A] text-black font-extrabold text-sm transition-all cursor-pointer shadow-xl shadow-[#E8B74A]/25 flex items-center gap-2 group"
            >
              <span>{isAuthenticated ? 'CONTINUE TO DASHBOARD' : 'SIGN IN / ENTER TERMINAL'}</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 7. SYSTEM FOOTER */}
      {/* ========================================================================= */}
      <footer className="border-t border-[#1E1E2C] py-8 px-4 sm:px-8 bg-[#050508] text-xs font-mono text-[#5A5A72]">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>
            CINEMETRICS // 2.0 • Theatrical Quantitative Intelligence &amp; Risk Nexus
          </p>
          <div className="flex items-center gap-4 text-[#9090AA]">
            <span>MODELS: 3-WAY STACK (CATBOOST + LIGHTGBM)</span>
            <span>•</span>
            <span>VOVK CONFORMAL (80% / 95%)</span>
            <span>•</span>
            <span className="text-emerald-400">STAGE 4 ACTIVE</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
