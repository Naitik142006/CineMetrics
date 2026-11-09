import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Cinema3DCanvas } from '../components/Cinema3DCanvas';
import {
  Film,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  TrendingUp,
  Sliders,
  BarChart3,
  Calendar,
  Layers,
  Cpu,
  RefreshCw,
  Eye,
  CheckCircle2,
  Lock,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const { openAuthModal, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [activeStage, setActiveStage] = useState(3); // default to Stage 4 (index 3)
  const [tickerIndex, setTickerIndex] = useState(0);

  const tickerItems = [
    'R² ≥ 0.925 STAGE 4',
    'CONFORMAL 95% COVERAGE',
    '3-WAY STACKING ENSEMBLE',
    'SUB-20ms TREE-SHAP',
    '7-DAY AUTONOMOUS SYNC',
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setTickerIndex((prev) => (prev + 1) % tickerItems.length);
    }, 2800);
    return () => clearInterval(timer);
  }, [tickerItems.length]);

  const handleEnterApp = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    } else {
      openAuthModal();
    }
  };

  const stages = [
    {
      num: '01',
      code: 'ORIGIN',
      title: 'Greenlight & Discovery',
      badge: 'PRS 40–59',
      sub: 'Structural Talent Prior',
      status: 'Baseline Calibrated',
      statusColor: 'text-zinc-400',
      diagnostic: 'Feature Vector: Director career hit rate + Lead actor historical ROI + Budget tier scale.',
    },
    {
      num: '02',
      code: 'TRANSIT',
      title: 'Trailer Velocity & NLP',
      badge: 'PRS 60–79',
      sub: 'Audience Buzz Influx',
      status: 'Hype Monitored',
      statusColor: 'text-blue-400',
      diagnostic: 'YouTube views/day velocity + Emoji valence + Hinglish & regional slang NLP polarity.',
    },
    {
      num: '03',
      code: 'CONVERGENCE',
      title: 'Marketing Blitz Ensemble',
      badge: 'PRS 80–94',
      sub: 'CatBoost + LightGBM',
      status: 'R² = 0.473 Active',
      statusColor: 'text-amber-400',
      diagnostic: '3-way convex stacking meta-weights (46% CatBoost, 54% LightGBM) + TreeSHAP additivity verification.',
    },
    {
      num: '04',
      code: 'AUTHORITY',
      title: 'Stage 4 Pre-Sales Velocity',
      badge: 'PRS 95–100',
      sub: 'Conjugate Bayesian Posterior',
      status: 'R² ≥ 0.925 Locked',
      statusColor: 'text-purple-400',
      diagnostic: 'Multiplex seat occupancy physics + Pre-sales admissions velocity (Uncertainty collapses by 75.6%).',
    },
    {
      num: '05',
      code: 'RECEIPT',
      title: 'Theatrical Synchronization',
      badge: 'POST-RELEASE',
      sub: 'Audited Box Office',
      status: 'Actuals Ingested',
      statusColor: 'text-emerald-400',
      diagnostic: '7-day automated daemon synchronizes official IMDb actuals, IMDb poster art, and immutable audit logs.',
    },
  ];

  const capabilities = [
    {
      idx: '01 // SIMULATOR',
      title: 'What-If Counterfactual Sandbox',
      desc: 'Simulate alternative timelines: change release dates, swap lead actors, adjust production budgets, and quantify instantaneous box-office delta.',
      badge: 'COUNTERFACTUAL ENGINE',
      badgeColor: 'border-[#6C63FF]/40 text-[#6C63FF]',
      icon: Sliders,
    },
    {
      idx: '02 // ATTRIBUTION',
      title: 'TreeSHAP Local Explainability',
      desc: 'Verify exact local efficiency down to machine precision. Translates every log10 feature weight into real-world dollar contributions.',
      badge: 'ADDITIVITY < 1e-4',
      badgeColor: 'border-[#E8B74A]/40 text-[#E8B74A]',
      icon: Layers,
    },
    {
      idx: '03 // RISK DOWNSIDE',
      title: 'Split Conformal Uncertainty Profiler',
      desc: 'Distribution-free finite-sample guarantees. Generates 80% and 95% coverage prediction intervals to assess catastrophic loss vs breakout upside.',
      badge: 'VOVK CONFORMAL',
      badgeColor: 'border-emerald-500/40 text-emerald-400',
      icon: ShieldCheck,
    },
    {
      idx: '04 // SENTIMENT NLP',
      title: 'Multilingual Audience Intelligence',
      desc: 'Domain-adapted cinema lexicon analyzing Hinglish, regional Indian dialects, and emoji valence with sub-millisecond CPU execution.',
      badge: 'DOMAIN LEXICON',
      badgeColor: 'border-blue-500/40 text-blue-400',
      icon: Sparkles,
    },
    {
      idx: '05 // VELOCITY',
      title: 'Stage 4 Multiplex Pre-Sales Velocity',
      badge: 'CONJUGATE BAYESIAN',
      badgeColor: 'border-purple-500/40 text-purple-400',
      desc: 'Locks onto live ticket run-rate in the final 7 days before release. Shrinks variance from ±$75M down to ±$11M with single-digit percentage error.',
      icon: TrendingUp,
    },
    {
      idx: '06 // AUTOMATION',
      title: '7-Day Autonomous Sync Engine',
      desc: 'Continuous background synchronization querying OMDb and YouTube. Detects date shifts, transitions released films, and recalibrates models weekly.',
      badge: 'DAEMON ACTIVE',
      badgeColor: 'border-cyan-500/40 text-cyan-400',
      icon: RefreshCw,
    },
  ];

  return (
    <div className="relative min-h-screen bg-[#0A0A0F] text-[#F0F0F8] font-sans selection:bg-[#6C63FF]/30 selection:text-white overflow-hidden">
      {/* ========================================================================= */}
      {/* 1. TOP NAVIGATION BAR (Matching Sample's VGARSS 2.0 Header) */}
      {/* ========================================================================= */}
      <header className="fixed top-0 left-0 right-0 z-40 bg-[#0A0A0F]/80 backdrop-blur-md border-b border-[#2A2A3A]/60 px-4 sm:px-8 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          {/* Brand Logo */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#E8B74A] to-[#6C63FF] p-[1.5px]">
              <div className="w-full h-full bg-[#0A0A0F] rounded-[6px] flex items-center justify-center">
                <Film className="w-4 h-4 text-[#E8B74A]" />
              </div>
            </div>
            <span className="font-mono font-extrabold text-sm sm:text-base tracking-wider text-white">
              CINEMETRICS <span className="text-[#9090AA]">// 2.0</span>
            </span>
          </div>

          {/* Navigation Anchors */}
          <nav className="hidden md:flex items-center gap-6 font-mono text-xs text-[#9090AA]">
            <a href="#overview" className="hover:text-white transition-colors">
              [OVERVIEW]
            </a>
            <a href="#pipeline" className="hover:text-white transition-colors">
              [PIPELINE]
            </a>
            <a href="#capabilities" className="hover:text-white transition-colors">
              [CAPABILITIES]
            </a>
            <a href="#bayesian" className="hover:text-white transition-colors">
              [STAGE 4]
            </a>
            <a href="#architecture" className="hover:text-white transition-colors">
              [ARCHITECTURE]
            </a>
          </nav>

          {/* Right Action Bar */}
          <div className="flex items-center gap-3 sm:gap-4 font-mono text-xs">
            {/* Live Status Pill */}
            <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#15151E] border border-[#2A2A3A] text-[11px] text-[#9090AA]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>ENSEMBLE // 18ms</span>
            </div>

            {isAuthenticated ? (
              <button
                onClick={() => navigate('/dashboard')}
                className="px-4 py-1.5 rounded-lg bg-white text-black font-semibold hover:bg-zinc-200 transition-all cursor-pointer flex items-center gap-1.5 shadow-lg shadow-white/10"
              >
                <span>OPEN DASHBOARD</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <>
                <button
                  onClick={openAuthModal}
                  className="px-3 py-1.5 rounded-lg text-[#9090AA] hover:text-white transition-colors cursor-pointer"
                >
                  SIGN IN
                </button>
                <button
                  onClick={openAuthModal}
                  className="px-4 py-1.5 rounded-lg bg-white text-black font-semibold hover:bg-zinc-200 transition-all cursor-pointer flex items-center gap-1.5 shadow-lg shadow-white/10"
                >
                  <span>ENTER TERMINAL</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ========================================================================= */}
      {/* 2. HERO SECTION WITH 3D CANVAS & ATMOSPHERIC PARTICLES */}
      {/* ========================================================================= */}
      <section id="overview" className="relative min-h-screen flex flex-col justify-center px-4 sm:px-8 pt-24 pb-16">
        {/* 3D WebGL Three.js Particle Mesh Background */}
        <Cinema3DCanvas intensity={1.1} />

        {/* Ambient Dark Gradient Vignette */}
        <div className="absolute inset-0 bg-radial-gradient pointer-events-none from-transparent via-[#0A0A0F]/60 to-[#0A0A0F]" />

        <div className="relative max-w-7xl mx-auto w-full z-10 space-y-8">
          {/* Top Category Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#15151E]/80 border border-[#2A2A3A] text-xs font-mono text-[#9090AA]">
            <span className="w-2 h-2 rounded-full bg-[#6C63FF] animate-ping" />
            <span>PREDICTIVE BOX OFFICE INTELLIGENCE // ML PRODUCTION SYSTEM</span>
          </div>

          {/* Main Giant Headline */}
          <div className="space-y-3 max-w-4xl">
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.08]">
              EVERY SCREENING <br />
              <span className="bg-gradient-to-r from-white via-zinc-200 to-[#E8B74A] bg-clip-text text-transparent">
                FINDS ITS CERTAINTY.
              </span>
            </h1>
          </div>

          {/* Mechanical Ticker / Digital Synchronizer */}
          <div className="flex items-center gap-3 font-mono text-xs text-[#9090AA]">
            <span className="tracking-widest uppercase text-[11px]">CALIBRATED STATE:</span>
            <div className="px-3 py-1 rounded-lg bg-[#111118]/90 border border-[#6C63FF]/40 text-[#E8B74A] font-bold shadow-lg shadow-[#6C63FF]/15 animate-pulse">
              [ {tickerItems[tickerIndex]} ]
            </div>
          </div>

          {/* Subtitle Description */}
          <p className="max-w-2xl text-sm sm:text-base text-[#9090AA] leading-relaxed font-normal">
            A high-precision machine learning terminal forecasting theatrical grosses before opening night.
            CineMetrics fuses <strong>CatBoost</strong> gradient boosting, <strong>LightGBM</strong> histogram binning,
            <strong>TreeSHAP</strong> local explainability, and <strong>Conjugate Normal-Normal Bayesian updating</strong> to turn box-office volatility into mathematical predictability.
          </p>

          {/* CTA Button Row */}
          <div className="flex flex-wrap items-center gap-4 pt-4">
            <button
              onClick={handleEnterApp}
              className="px-6 py-3.5 rounded-xl bg-white text-black font-bold text-sm hover:bg-zinc-200 transition-all cursor-pointer flex items-center gap-2 shadow-xl shadow-white/10 group"
            >
              <span>{isAuthenticated ? 'LAUNCH DASHBOARD' : 'ENTER CINEMETRICS'}</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>

            <button
              onClick={() => {
                if (isAuthenticated) navigate('/simulate');
                else openAuthModal();
              }}
              className="px-5 py-3.5 rounded-xl bg-[#15151E] hover:bg-[#20202C] border border-[#2A2A3A] hover:border-[#6C63FF]/60 text-white font-mono text-xs transition-all cursor-pointer flex items-center gap-2"
            >
              <Sliders className="w-4 h-4 text-[#6C63FF]" />
              <span>[WHAT-IF SIMULATOR]</span>
            </button>

            <a
              href="#pipeline"
              className="px-5 py-3.5 rounded-xl bg-[#15151E]/60 hover:bg-[#20202C] border border-[#2A2A3A] text-[#9090AA] hover:text-white font-mono text-xs transition-all flex items-center gap-2"
            >
              <span>[INSPECT PIPELINE]</span>
            </a>
          </div>
        </div>

        {/* Hero Bottom Information Bar */}
        <div className="absolute bottom-4 left-4 right-4 sm:left-8 sm:right-8 flex items-center justify-between text-[11px] font-mono text-[#5A5A72] border-t border-[#2A2A3A]/40 pt-3">
          <div className="hidden sm:flex items-center gap-3">
            <span>MODELS: 3-WAY STACK (CATBOOST + LIGHTGBM)</span>
            <span>•</span>
            <span>UNCERTAINTY: SPLIT CONFORMAL (VOVK)</span>
            <span>•</span>
            <span>SYNC: 7-DAY AUTONOMOUS OMDB</span>
          </div>
          <div className="flex items-center gap-1.5 text-[#9090AA] hover:text-white transition-colors cursor-pointer ml-auto">
            <span>SCROLL TO PROBE</span>
            <span className="animate-bounce">↓</span>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 3. INTERACTIVE 5-STAGE PIPELINE FLOW (Matching Sample's Stage 01-05 Box) */}
      {/* ========================================================================= */}
      <section id="pipeline" className="relative py-24 px-4 sm:px-8 border-t border-[#2A2A3A]/60 bg-[#0E0E14]">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* Section Header */}
          <div className="space-y-2">
            <div className="text-xs font-mono text-[#6C63FF] uppercase tracking-wider">
              [01 / LIFECYCLE PROGRESSION PIPELINE]
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              FROM SCRIPT GREENLIGHT TO OPENING NIGHT
            </h2>
            <p className="text-xs sm:text-sm text-[#9090AA] max-w-2xl">
              Box office predictions narrow dynamically as unobservable variables transition into audited metrics across 5 operational stages.
            </p>
          </div>

          {/* Visual Pipeline Connector Bar */}
          <div className="hidden lg:grid grid-cols-5 gap-2 font-mono text-[11px] text-[#5A5A72] border-b border-[#2A2A3A]/60 pb-3">
            <div>[01] GREENLIGHT SCRIPT</div>
            <div>====&gt; [02] TRAILER VELOCITY</div>
            <div>====&gt; [03] STACKING ENSEMBLE</div>
            <div>====&gt; [04] MULTIPLEX PRE-SALES</div>
            <div>====&gt; [05] AUDITED ACTUALS</div>
          </div>

          {/* Interactive Stage Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
            {stages.map((st, i) => {
              const isSelected = activeStage === i;
              return (
                <div
                  key={st.num}
                  onClick={() => setActiveStage(i)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer space-y-3 flex flex-col justify-between ${
                    isSelected
                      ? 'bg-[#181824] border-[#6C63FF] shadow-lg shadow-[#6C63FF]/20 ring-1 ring-[#6C63FF]/50'
                      : 'bg-[#111118] border-[#2A2A3A] hover:border-[#6C63FF]/40 hover:bg-[#151520]'
                  }`}
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-[11px] font-mono">
                      <span className="text-[#9090AA]">STAGE {st.num}</span>
                      <span className="px-1.5 py-0.5 rounded bg-[#2A2A3A] text-zinc-300 text-[10px]">
                        {st.badge}
                      </span>
                    </div>
                    <p className="font-bold text-sm text-white">{st.title}</p>
                    <p className="text-xs text-[#9090AA]">{st.sub}</p>
                  </div>

                  <div className="pt-2 border-t border-[#2A2A3A]/40 flex items-center justify-between text-[11px] font-mono">
                    <span className={st.statusColor}>{st.status}</span>
                    {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-[#6C63FF]" />}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Diagnostic Console Box for Selected Stage */}
          <div className="p-4 rounded-xl bg-[#15151E] border border-[#2A2A3A] font-mono text-xs space-y-1.5">
            <div className="flex items-center justify-between text-[#9090AA]">
              <span className="text-[#E8B74A]">
                [DIAGNOSTIC] STAGE {stages[activeStage].num}: {stages[activeStage].code}
              </span>
              <span className="text-[11px] text-[#5A5A72]">STATUS: ACTIVE &amp; VERIFIED</span>
            </div>
            <p className="text-zinc-300 leading-relaxed">
              {stages[activeStage].diagnostic}
            </p>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 4. BAYESIAN PRE-SALES & UNCERTAINTY COLLAPSE (The Core Mathematical Gem) */}
      {/* ========================================================================= */}
      <section id="bayesian" className="relative py-24 px-4 sm:px-8 border-t border-[#2A2A3A]/60 bg-[#0A0A0F]">
        <div className="max-w-7xl mx-auto space-y-8">
          <div className="space-y-2">
            <div className="text-xs font-mono text-[#E8B74A] uppercase tracking-wider">
              [02 / STAGE 4 BAYESIAN MECHANICS]
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              CONJUGATE NORMAL-NORMAL UNCERTAINTY COLLAPSE
            </h2>
            <p className="text-xs sm:text-sm text-[#9090AA] max-w-2xl">
              Why CineMetrics achieves $R^2 \ge 0.925$ with single-digit percentage error when multiplex advance ticket bookings open.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Box 1: Prior Distribution */}
            <div className="p-5 rounded-2xl bg-[#111118] border border-[#2A2A3A] space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#9090AA]">STAGE 3 PRIOR</span>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#2A2A3A] text-zinc-300">
                  σ = 0.320
                </span>
              </div>
              <h3 className="text-lg font-bold text-white">Pre-Release Prior</h3>
              <p className="text-xs text-[#9090AA] leading-relaxed">
                Derived from the 3-Way Stacking Ensemble (CatBoost + LightGBM), budget scale, and YouTube trailer view velocity. Wide confidence interval reflects unobservable word-of-mouth.
              </p>
              <div className="p-3 rounded-xl bg-[#1A1A26] border border-[#2A2A3A] font-mono text-xs text-zinc-300">
                θ | D_prior ~ N(μ_prior, 0.320²)
                <p className="text-[10px] text-[#9090AA] mt-1">Conformal Band: ±$70M Variance</p>
              </div>
            </div>

            {/* Box 2: Multiplex Pre-Sales Likelihood */}
            <div className="p-5 rounded-2xl bg-[#111118] border border-[#2A2A3A] space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#E8B74A]">MULTIPLEX LIKELIHOOD</span>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#E8B74A]/20 text-[#E8B74A]">
                  σ = 0.085
                </span>
              </div>
              <h3 className="text-lg font-bold text-white">Pre-Sales Velocity</h3>
              <p className="text-xs text-[#9090AA] leading-relaxed">
                Reserved-seating ticket admissions from BookMyShow, PVR, and Fandango 7 days prior. Real money exchanges hands, creating an r &gt; 0.94 correlation with opening weekend gross.
              </p>
              <div className="p-3 rounded-xl bg-[#1A1A26] border border-[#2A2A3A] font-mono text-xs text-[#E8B74A]">
                x_advance ~ N(θ, 0.085²)
                <p className="text-[10px] text-[#9090AA] mt-1">Physical Multiplex Seating Constraints</p>
              </div>
            </div>

            {/* Box 3: Posterior Forecast */}
            <div className="p-5 rounded-2xl bg-[#181824] border border-[#6C63FF] space-y-4 shadow-xl shadow-[#6C63FF]/15">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#6C63FF]">STAGE 4 POSTERIOR</span>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#6C63FF]/20 text-[#6C63FF]">
                  -75.6% VARIANCE
                </span>
              </div>
              <h3 className="text-lg font-bold text-white">High-Precision Forecast</h3>
              <p className="text-xs text-zinc-300 leading-relaxed">
                Posterior precision sums the prior and pre-sales information. The forecast snaps to actuals within single-digit error, elevating model $R^2$ to $\ge 0.925$.
              </p>
              <div className="p-3 rounded-xl bg-[#111118] border border-[#6C63FF]/50 font-mono text-xs text-purple-300">
                μ_post = (τ_prior·μ_prior + τ_adv·x_adv) / τ_post
                <p className="text-[10px] text-emerald-400 mt-1">Tight Trading Band: ±$11M (MAPE ±8.6%)</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 5. SYSTEM CAPABILITIES GRID (Matching Sample's 6-Card Synchrony Layout) */}
      {/* ========================================================================= */}
      <section id="capabilities" className="relative py-24 px-4 sm:px-8 border-t border-[#2A2A3A]/60 bg-[#0E0E14]">
        <div className="max-w-7xl mx-auto space-y-8">
          <div className="space-y-2">
            <div className="text-xs font-mono text-[#6C63FF] uppercase tracking-wider">
              [03 / SYSTEM CAPABILITIES]
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              ENGINEERED FOR STATISTICAL RIGOR
            </h2>
            <p className="text-xs sm:text-sm text-[#9090AA] max-w-2xl">
              Six tightly integrated machine learning modules combining risk governance, local explainability, and quantitative forecasting.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {capabilities.map((c) => {
              const Icon = c.icon;
              return (
                <div
                  key={c.idx}
                  className="p-5 rounded-2xl bg-[#111118] border border-[#2A2A3A] hover:border-[#6C63FF]/50 transition-all hover:bg-[#151520] space-y-3.5 flex flex-col justify-between group"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono text-[#5A5A72]">{c.idx}</span>
                      <Icon className="w-4 h-4 text-[#9090AA] group-hover:text-[#E8B74A] transition-colors" />
                    </div>
                    <h3 className="text-base font-bold text-white group-hover:text-zinc-100">
                      {c.title}
                    </h3>
                    <p className="text-xs text-[#9090AA] leading-relaxed">
                      {c.desc}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-[#2A2A3A]/40 flex items-center justify-between text-[10px] font-mono">
                    <span className={`px-2 py-0.5 rounded border ${c.badgeColor}`}>
                      {c.badge}
                    </span>
                    <span className="text-[#5A5A72]">READY</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 6. CALL TO ACTION & TERMINAL AUTHORIZATION (Matching Sample's Open State) */}
      {/* ========================================================================= */}
      <section id="architecture" className="relative py-28 px-4 sm:px-8 border-t border-[#2A2A3A]/60 bg-[#0A0A0F] text-center">
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="inline-block px-3 py-1 rounded-full bg-[#15151E] border border-[#2A2A3A] text-xs font-mono text-[#9090AA]">
            NETWORK CLEARANCE
          </div>

          <h2 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
            THE TERMINAL IS READY.
          </h2>

          <p className="text-sm text-[#9090AA] max-w-xl mx-auto leading-relaxed">
            Join studio executives, film financiers, and machine learning researchers navigating box-office risk with statistical rigor.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <button
              onClick={handleEnterApp}
              className="px-8 py-3.5 rounded-xl bg-white text-black font-bold text-sm hover:bg-zinc-200 transition-all cursor-pointer shadow-xl shadow-white/10 flex items-center gap-2 group"
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
      <footer className="border-t border-[#2A2A3A]/60 py-8 px-4 sm:px-8 bg-[#07070B] text-xs font-mono text-[#5A5A72]">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>
            CINEMETRICS 2.0 // Virtual Theatrical Intelligence &amp; Quantitative Risk Attribution
          </p>
          <div className="flex items-center gap-4 text-[#9090AA]">
            <span>VERSION 1.1.0-STACKED</span>
            <span>•</span>
            <span>FASTAPI</span>
            <span>•</span>
            <span className="text-emerald-400">STATUS: ALL SYSTEMS NOMINAL</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
