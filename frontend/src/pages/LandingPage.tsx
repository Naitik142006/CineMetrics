import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCurrency } from '../context/CurrencyContext';
import { formatCurrency, getPosterUrl } from '../utils/format';
import { apiService } from '../services/api';
import { UpcomingMovieItem } from '../types';
import {
  Film,
  ArrowRight,
  Sliders,
  DollarSign,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  TrendingUp,
  Flame,
  Globe2,
  ShieldCheck,
  Target,
  BarChart3,
  Clock,
} from 'lucide-react';

interface HeroPreviewItem {
  id?: string;
  title: string;
  releaseDate: string;
  year: string;
  director: string;
  star: string;
  industry: string;
  posterPath?: string | null;
  expectedUsd: number;
  lowUsd: number;
  highUsd: number;
  earlyExpectedUsd: number;
  earlyLowUsd: number;
  earlyHighUsd: number;
  daysToRelease?: number | null;
}

const FALLBACK_HERO_PREVIEWS: HeroPreviewItem[] = [
  {
    title: 'Avengers: Doomsday',
    releaseDate: '2026-12-16',
    year: '2026',
    director: 'Anthony & Joe Russo',
    star: 'Robert Downey Jr.',
    industry: 'Hollywood',
    expectedUsd: 1_450_000_000,
    lowUsd: 1_190_000_000,
    highUsd: 1_710_000_000,
    earlyExpectedUsd: 1_380_000_000,
    earlyLowUsd: 940_000_000,
    earlyHighUsd: 1_820_000_000,
  },
  {
    title: 'King',
    releaseDate: '2026-12-24',
    year: '2026',
    director: 'Siddharth Anand',
    star: 'Shah Rukh Khan',
    industry: 'Bollywood',
    expectedUsd: 155_000_000,
    lowUsd: 122_000_000,
    highUsd: 192_000_000,
    earlyExpectedUsd: 145_000_000,
    earlyLowUsd: 98_000_000,
    earlyHighUsd: 205_000_000,
  },
  {
    title: 'Dune: Part Three',
    releaseDate: '2026-12-15',
    year: '2026',
    director: 'Denis Villeneuve',
    star: 'Timothée Chalamet',
    industry: 'Hollywood',
    expectedUsd: 840_000_000,
    lowUsd: 690_000_000,
    highUsd: 990_000_000,
    earlyExpectedUsd: 790_000_000,
    earlyLowUsd: 540_000_000,
    earlyHighUsd: 1_050_000_000,
  },
];

export const LandingPage: React.FC = () => {
  const { openAuthModal, isAuthenticated } = useAuth();
  const { currency, toggleCurrency } = useCurrency();
  const navigate = useNavigate();

  const [selectedHeroMovie, setSelectedHeroMovie] = useState<number>(0);
  const [forecastView, setForecastView] = useState<'early' | 'release'>('release');
  const [liveUpcoming, setLiveUpcoming] = useState<UpcomingMovieItem[]>([]);

  useEffect(() => {
    let active = true;
    async function loadUpcomingPreview() {
      try {
        const items = await apiService.getUpcomingMovies({
          sort_by: 'forecast',
          limit: 6,
        });
        if (active && Array.isArray(items) && items.length > 0) {
          setLiveUpcoming(items);
        }
      } catch (err) {
        console.warn('Landing upcoming preview unavailable:', err);
      }
    }
    loadUpcomingPreview();
    return () => {
      active = false;
    };
  }, []);

  const heroItems: HeroPreviewItem[] =
    liveUpcoming.length >= 3
      ? liveUpcoming.slice(0, 3).map((m) => ({
          id: m.id,
          title: m.primary_title,
          releaseDate: m.release_date,
          year: String(m.release_year),
          director: m.director,
          star: m.lead_actor,
          industry: m.industry,
          posterPath: m.poster_path,
          expectedUsd: m.expected_gross_usd,
          lowUsd: m.pessimistic_bound_80_usd,
          highUsd: m.optimistic_bound_80_usd,
          earlyExpectedUsd: Math.round(m.expected_gross_usd * 0.94),
          earlyLowUsd: Math.round(m.expected_gross_usd * 0.64),
          earlyHighUsd: Math.round(m.expected_gross_usd * 1.28),
          daysToRelease: m.days_to_release,
        }))
      : FALLBACK_HERO_PREVIEWS;

  const currentDemo = heroItems[selectedHeroMovie] || heroItems[0];
  const currentDemoPosterUrl = getPosterUrl(currentDemo.posterPath);
  const isReleaseView = forecastView === 'release';
  const displayGross = isReleaseView ? currentDemo.expectedUsd : currentDemo.earlyExpectedUsd;
  const displayLow = isReleaseView ? currentDemo.lowUsd : currentDemo.earlyLowUsd;
  const displayHigh = isReleaseView ? currentDemo.highUsd : currentDemo.earlyHighUsd;

  const upcomingPortfolio = liveUpcoming.slice(0, 4);

  const handleEnterTerminal = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    } else {
      openAuthModal();
    }
  };

  const todayFormatted = new Date().toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div className="relative min-h-screen bg-[#07070B] text-[#F0F0F8] font-sans selection:bg-[#E8B74A]/30 selection:text-white overflow-x-hidden">
      {/* ========================================================================= */}
      {/* 1. TOP BAR */}
      {/* ========================================================================= */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#07070B]/85 backdrop-blur-xl border-b border-[#1E1E2C]/80 px-4 sm:px-8 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
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
                BOX OFFICE AI
              </span>
            </div>
          </div>

          <nav className="hidden lg:flex items-center gap-6 font-mono text-xs text-[#9090AA]">
            <a href="#overview" className="hover:text-white transition-colors">
              • OVERVIEW
            </a>
            <a href="#why-better" className="hover:text-white transition-colors">
              • WHY CINEMETRICS
            </a>
            <a href="#use-cases" className="hover:text-white transition-colors">
              • USE CASES
            </a>
            <a href="#upcoming-live" className="hover:text-white transition-colors">
              • UPCOMING RADAR
            </a>
          </nav>

          <div className="flex items-center gap-2 sm:gap-3">
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
                  <span>LAUNCH APP</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ========================================================================= */}
      {/* 2. HERO SECTION — Value & Capabilities */}
      {/* ========================================================================= */}
      <section
        id="overview"
        className="relative min-h-screen flex flex-col justify-center px-4 sm:px-8 pt-28 pb-16 overflow-hidden"
      >
        {/* Stable Static Architectural Cinema Grid & Ambient Studio Lighting */}
        <div aria-hidden="true" className="absolute inset-0 pointer-events-none select-none overflow-hidden">
          <div
            className="absolute inset-0 opacity-[0.22]"
            style={{
              backgroundImage:
                'linear-gradient(to right, rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.06) 1px, transparent 1px)',
              backgroundSize: '56px 56px',
              maskImage: 'radial-gradient(ellipse 80% 70% at 50% 45%, #000 40%, transparent 100%)',
              WebkitMaskImage: 'radial-gradient(ellipse 80% 70% at 50% 45%, #000 40%, transparent 100%)',
            }}
          />

          <div className="absolute -top-24 -left-24 w-[520px] h-[520px] rounded-full bg-[#E8B74A]/[0.08] blur-[120px]" />
          <div className="absolute top-1/4 right-[-8%] w-[560px] h-[560px] rounded-full bg-[#6C63FF]/[0.12] blur-[130px]" />
          <div className="absolute bottom-0 left-1/3 w-[420px] h-[280px] rounded-full bg-sky-500/[0.06] blur-[110px]" />

          <svg
            className="absolute inset-0 w-full h-full opacity-35"
            viewBox="0 0 1440 900"
            preserveAspectRatio="xMidYMid slice"
            fill="none"
          >
            <circle cx="1030" cy="450" r="320" stroke="url(#heroRingGold)" strokeWidth="1" strokeDasharray="4 8" />
            <circle cx="1030" cy="450" r="230" stroke="url(#heroRingIndigo)" strokeWidth="1" />
            <line x1="0" y1="450" x2="1440" y2="450" stroke="rgba(255,255,255,0.04)" strokeWidth="1" />
            <defs>
              <linearGradient id="heroRingGold" x1="710" y1="130" x2="1350" y2="770" gradientUnits="userSpaceOnUse">
                <stop stopColor="#E8B74A" stopOpacity="0.45" />
                <stop offset="1" stopColor="#E8B74A" stopOpacity="0.05" />
              </linearGradient>
              <linearGradient id="heroRingIndigo" x1="800" y1="220" x2="1260" y2="680" gradientUnits="userSpaceOnUse">
                <stop stopColor="#6C63FF" stopOpacity="0.5" />
                <stop offset="1" stopColor="#38BDF8" stopOpacity="0.08" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        <div className="absolute inset-0 pointer-events-none bg-gradient-to-b from-transparent via-transparent to-[#07070B]" />

        <div className="relative max-w-7xl mx-auto w-full z-10 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column: Product Value Proposition */}
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#111118]/80 border border-[#2A2A3A] text-xs font-mono text-[#E8B74A]">
              <span className="w-2 h-2 rounded-full bg-[#E8B74A]" />
              <span>PRE-RELEASE BOX OFFICE &amp; RISK INTELLIGENCE</span>
            </div>

            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-[1.06]">
              SMARTER FILM <br />
              <span className="bg-gradient-to-r from-white via-zinc-100 to-[#E8B74A] bg-clip-text text-transparent">
                DECISIONS BEFORE
              </span>{' '}
              <br />
              OPENING NIGHT.
            </h1>

            <p className="max-w-xl text-sm sm:text-base text-[#9090AA] leading-relaxed font-normal">
              CineMetrics helps studios, distributors, investors, and cinema analysts estimate theatrical revenue, spot financial downside early, and test budget, casting, and release-date decisions across Hollywood and Indian cinema—all in one place.
            </p>

            {/* Action Bar */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <button
                onClick={handleEnterTerminal}
                className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-[#E8B74A] to-[#D49E28] hover:from-[#F3C766] hover:to-[#E8B74A] text-black font-extrabold text-sm transition-all cursor-pointer flex items-center gap-2.5 shadow-xl shadow-[#E8B74A]/25 group"
              >
                <span>{isAuthenticated ? 'OPEN DASHBOARD' : 'EXPLORE LIVE DASHBOARD'}</span>
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
                <span>TRY WHAT-IF SIMULATOR</span>
              </button>
            </div>

            {/* Product Benefits Strip */}
            <div className="pt-4 border-t border-[#1E1E2C] grid grid-cols-3 gap-4 text-xs font-mono">
              <div>
                <p className="text-[#5A5A72] text-[10px] uppercase">Global + Regional</p>
                <p className="text-[#E8B74A] font-bold text-sm">Hollywood &amp; Indian Cinema</p>
              </div>
              <div>
                <p className="text-[#5A5A72] text-[10px] uppercase">Risk Visibility</p>
                <p className="text-emerald-400 font-bold text-sm">Low-to-High Revenue Ranges</p>
              </div>
              <div>
                <p className="text-[#5A5A72] text-[10px] uppercase">Live Calendar</p>
                <p className="text-purple-400 font-bold text-sm">Synced as of {todayFormatted}</p>
              </div>
            </div>
          </div>

          {/* Right Column: Live Upcoming Forecast Preview Card */}
          <div className="lg:col-span-5">
            <div className="relative rounded-2xl bg-[#0E0E16]/90 border border-[#2A2A3A] p-6 shadow-2xl backdrop-blur-xl space-y-5">
              <div className="flex items-center justify-between border-b border-[#1E1E2C] pb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span className="font-mono text-xs text-white uppercase tracking-wider font-bold">
                    Upcoming Forecast Preview
                  </span>
                </div>
                <span className="font-mono text-[10px] text-[#9090AA] px-2 py-0.5 rounded bg-[#1A1A26] border border-[#2A2A3A]">
                  LIVE RADAR
                </span>
              </div>

              {/* Movie Selector Tabs */}
              <div className="flex gap-2 p-1 bg-[#151520] rounded-xl border border-[#2A2A3A]">
                {heroItems.map((m, idx) => (
                  <button
                    key={m.title}
                    onClick={() => setSelectedHeroMovie(idx)}
                    className={`flex-1 py-1.5 px-2 text-[11px] font-mono rounded-lg transition-all cursor-pointer truncate ${
                      selectedHeroMovie === idx
                        ? 'bg-[#E8B74A] text-black font-bold shadow-md'
                        : 'text-[#9090AA] hover:text-white'
                    }`}
                  >
                    {m.title.split(':')[0]}
                  </button>
                ))}
              </div>

              {/* Title, Poster & Metadata */}
              <div className="flex items-start gap-3.5">
                <div className="w-14 h-20 rounded-xl overflow-hidden bg-[#151520] border border-[#2A2A3A] flex items-center justify-center flex-shrink-0 shadow-lg">
                  {currentDemoPosterUrl ? (
                    <img
                      src={currentDemoPosterUrl}
                      alt={currentDemo.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <Film className="w-5 h-5 text-[#5A5A72]" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-lg font-bold text-white truncate">{currentDemo.title}</h3>
                    <span className="text-xs font-mono text-[#E8B74A] font-bold shrink-0">
                      {currentDemo.releaseDate}
                    </span>
                  </div>
                  <p className="text-xs text-[#9090AA] mt-0.5 truncate">
                    Dir: {currentDemo.director} • Lead: {currentDemo.star}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="inline-block text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#6C63FF]/15 text-[#9090AA] border border-[#6C63FF]/30">
                      {currentDemo.industry}
                    </span>
                    {currentDemo.daysToRelease !== undefined && currentDemo.daysToRelease !== null && (
                      <span className="inline-block text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-950/50 text-emerald-300 border border-emerald-500/30">
                        Releases in {currentDemo.daysToRelease} days
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Outlook View Toggle */}
              <div className="p-3 rounded-xl bg-[#151520] border border-[#2A2A3A] space-y-3">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-[#9090AA]">Planning Horizon:</span>
                  <div className="flex gap-1.5">
                    <button
                      onClick={() => setForecastView('early')}
                      className={`px-2.5 py-1 rounded-md text-[11px] transition-all cursor-pointer ${
                        !isReleaseView
                          ? 'bg-[#2A2A3A] text-white font-bold'
                          : 'text-[#9090AA] hover:text-white'
                      }`}
                    >
                      Early Greenlight
                    </button>
                    <button
                      onClick={() => setForecastView('release')}
                      className={`px-2.5 py-1 rounded-md text-[11px] transition-all cursor-pointer ${
                        isReleaseView
                          ? 'bg-[#6C63FF] text-white font-bold shadow-md'
                          : 'text-[#9090AA] hover:text-white'
                      }`}
                    >
                      Campaign Outlook
                    </button>
                  </div>
                </div>

                <div className="pt-2 border-t border-[#2A2A3A]/60 flex items-baseline justify-between">
                  <div>
                    <span className="text-[10px] font-mono uppercase text-[#9090AA]">
                      {isReleaseView ? 'Projected Worldwide Gross:' : 'Early Baseline Projection:'}
                    </span>
                    <p className={`text-2xl font-black font-mono ${isReleaseView ? 'text-[#E8B74A]' : 'text-zinc-200'}`}>
                      {formatCurrency(displayGross, currency)}
                    </p>
                  </div>
                  <span
                    className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded-full ${
                      isReleaseView
                        ? 'bg-purple-950 text-purple-300 border border-purple-500/50'
                        : 'bg-[#2A2A3A] text-zinc-400'
                    }`}
                  >
                    {isReleaseView ? 'High Confidence' : 'Wide Early Range'}
                  </span>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-between text-[11px] font-mono text-[#9090AA]">
                    <span>Expected Floor – Ceiling:</span>
                    <span className="text-zinc-300">
                      {formatCurrency(displayLow, currency)} – {formatCurrency(displayHigh, currency)}
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-[#111118] overflow-hidden p-0.5 border border-[#2A2A3A]">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isReleaseView ? 'bg-gradient-to-r from-[#6C63FF] to-[#E8B74A] w-4/5' : 'bg-zinc-500 w-2/5'
                      }`}
                    />
                  </div>
                  <p className="text-[10px] font-mono text-[#5A5A72] text-right">
                    {isReleaseView
                      ? 'Tighter outlook as trailer momentum and release details lock in'
                      : 'Broader early-stage range prior to trailer launch'}
                  </p>
                </div>
              </div>

              <button
                onClick={() => {
                  if (isAuthenticated && currentDemo.id) {
                    navigate(`/movies/${currentDemo.id}`);
                  } else {
                    handleEnterTerminal();
                  }
                }}
                className="w-full py-2.5 rounded-xl bg-white hover:bg-zinc-200 text-black font-bold text-xs font-mono transition-all cursor-pointer flex items-center justify-center gap-2 shadow-lg shadow-white/10"
              >
                <span>VIEW FULL MOVIE BREAKDOWN</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 3. WHY CINEMETRICS IS BETTER */}
      {/* ========================================================================= */}
      <section id="why-better" className="relative py-24 px-4 sm:px-8 border-t border-[#1E1E2C] bg-[#0A0A10]">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <span className="text-xs font-mono text-[#E8B74A] uppercase tracking-wider font-semibold">
              [WHY CINEMETRICS]
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              BUILT TO OUTPERFORM GUT FEELINGS &amp; STATIC SPREADSHEETS
            </h2>
            <p className="text-sm text-[#9090AA] leading-relaxed">
              Most trackers only report box-office numbers after a film opens. CineMetrics gives you clear pre-release visibility across global and Indian markets before money is locked in.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Traditional Approach */}
            <div className="p-7 rounded-2xl bg-[#0E0E16] border border-red-500/20 space-y-5 relative overflow-hidden">
              <div className="flex items-center gap-2.5 text-red-400 font-mono text-xs font-bold uppercase tracking-wider">
                <AlertTriangle className="w-4 h-4" />
                <span>Traditional Tracking &amp; Spreadsheets</span>
              </div>
              <h3 className="text-xl font-bold text-white">Where Legacy Approaches Fall Short</h3>
              <p className="text-xs text-[#9090AA] leading-relaxed">
                Decisions rely on scattered Excel comps, single-number guesses, and backward-looking opening weekend reports—leaving Indian regional releases underserved and upside/downside risk hidden.
              </p>

              <div className="space-y-2.5 pt-2 font-mono text-xs text-red-300">
                <div className="p-3 rounded-xl bg-red-950/20 border border-red-500/30 flex items-center justify-between gap-2">
                  <span>Single Point Estimates</span>
                  <span className="font-bold text-right">Hides Downside Risk</span>
                </div>
                <div className="p-3 rounded-xl bg-red-950/20 border border-red-500/30 flex items-center justify-between gap-2">
                  <span>US-Only Coverage</span>
                  <span className="font-bold text-right">Misses Bollywood &amp; South India</span>
                </div>
                <div className="p-3 rounded-xl bg-red-950/20 border border-red-500/30 flex items-center justify-between gap-2">
                  <span>Static Comps</span>
                  <span className="font-bold text-right">No Way to Test Changes</span>
                </div>
              </div>
            </div>

            {/* Why CineMetrics Is Better */}
            <div className="p-7 rounded-2xl bg-[#11111E] border border-[#E8B74A]/40 space-y-5 relative overflow-hidden shadow-2xl shadow-[#E8B74A]/10">
              <div className="flex items-center gap-2.5 text-[#E8B74A] font-mono text-xs font-bold uppercase tracking-wider">
                <CheckCircle2 className="w-4 h-4" />
                <span>The CineMetrics Advantage</span>
              </div>
              <h3 className="text-xl font-bold text-white">Actionable Pre-Release Clarity</h3>
              <p className="text-xs text-zinc-300 leading-relaxed">
                Get realistic floor-to-ceiling revenue bands, instant USD/INR conversion, head-to-head film comparisons, and interactive scenario testing tailored to both Hollywood and Indian cinema.
              </p>

              <div className="space-y-2.5 pt-2 font-mono text-xs text-emerald-300">
                <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 flex items-center justify-between gap-2">
                  <span>Worst, Expected &amp; Best-Case Bands</span>
                  <span className="font-bold text-right">Clear Break-Even Odds</span>
                </div>
                <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 flex items-center justify-between gap-2">
                  <span>Global + Pan-Indian Markets</span>
                  <span className="font-bold text-right">USD &amp; ₹ Crore Ready</span>
                </div>
                <div className="p-3 rounded-xl bg-purple-950/20 border border-purple-500/40 flex items-center justify-between gap-2 text-purple-300">
                  <span>Interactive Scenario Sandbox</span>
                  <span className="font-bold text-right">Test Budget, Cast &amp; Dates</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 4. USE CASES — What You Can Use CineMetrics For */}
      {/* ========================================================================= */}
      <section id="use-cases" className="relative py-24 px-4 sm:px-8 border-t border-[#1E1E2C] bg-[#07070B]">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="space-y-2">
            <span className="text-xs font-mono text-[#6C63FF] uppercase tracking-wider font-semibold">
              [USES OF CINEMETRICS]
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              WHAT YOU CAN DO WITH THIS PLATFORM
            </h2>
            <p className="text-sm text-[#9090AA] max-w-2xl">
              Practical workflows designed for producers, acquisition teams, marketing strategists, and film enthusiasts.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Use Case 1 */}
            <div className="p-6 rounded-2xl bg-[#0E0E16] border border-[#2A2A3A] hover:border-[#E8B74A]/60 transition-all space-y-4 group">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#E8B74A] font-bold flex items-center gap-1.5">
                  <Target className="w-3.5 h-3.5" /> USE CASE 01
                </span>
                <span className="text-[#5A5A72]">BUDGET &amp; GREENLIGHTING</span>
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-[#E8B74A] transition-colors">
                Evaluate ROI &amp; Capital Risk Before Investing
              </h3>
              <p className="text-xs text-[#9090AA] leading-relaxed">
                Check whether a film&apos;s production budget makes financial sense against projected theatrical returns, worst-case downside floors, and commercial break-even probabilities.
              </p>
              <div className="pt-2 text-[11px] font-mono text-[#5A5A72] flex items-center gap-3">
                <span>• Break-Even Probability</span>
                <span>• Worst-to-Best Range</span>
              </div>
            </div>

            {/* Use Case 2 */}
            <div className="p-6 rounded-2xl bg-[#0E0E16] border border-[#2A2A3A] hover:border-[#6C63FF]/60 transition-all space-y-4 group">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#6C63FF] font-bold flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5" /> USE CASE 02
                </span>
                <span className="text-[#5A5A72]">RELEASE PLANNING</span>
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-[#6C63FF] transition-colors">
                Pick Stronger Release Windows &amp; Avoid Clashes
              </h3>
              <p className="text-xs text-[#9090AA] leading-relaxed">
                Browse an always-current radar of upcoming theatrical releases filtered by industry, release year, and countdown window so you can spot crowded holiday weekends early.
              </p>
              <div className="pt-2 text-[11px] font-mono text-[#5A5A72] flex items-center gap-3">
                <span>• Live Countdown Radar</span>
                <span>• Multi-Industry Calendar</span>
              </div>
            </div>

            {/* Use Case 3 */}
            <div className="p-6 rounded-2xl bg-[#0E0E16] border border-[#2A2A3A] hover:border-purple-500/60 transition-all space-y-4 group">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-purple-400 font-bold flex items-center gap-1.5">
                  <Globe2 className="w-3.5 h-3.5" /> USE CASE 03
                </span>
                <span className="text-[#5A5A72]">TALENT &amp; MARKET BENCHMARKS</span>
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-purple-300 transition-colors">
                Compare Films, Stars, Directors &amp; Regional Markets
              </h3>
              <p className="text-xs text-[#9090AA] leading-relaxed">
                Inspect director and lead-actor box-office track records, compare up to four films side by side, and explore market trends across Hollywood, Bollywood, Tollywood, Kollywood, and more.
              </p>
              <div className="pt-2 text-[11px] font-mono text-[#5A5A72] flex items-center gap-3">
                <span>• Talent Track Records</span>
                <span>• Side-by-Side Comparison</span>
              </div>
            </div>

            {/* Use Case 4 */}
            <div className="p-6 rounded-2xl bg-[#0E0E16] border border-[#2A2A3A] hover:border-emerald-500/60 transition-all space-y-4 group">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                  <BarChart3 className="w-3.5 h-3.5" /> USE CASE 04
                </span>
                <span className="text-[#5A5A72]">SCENARIO &amp; BUZZ TRACKING</span>
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-emerald-300 transition-colors">
                Test &ldquo;What-If&rdquo; Changes &amp; Track Audience Hype
              </h3>
              <p className="text-xs text-[#9090AA] leading-relaxed">
                Experiment with different budgets, directors, lead actors, or trailer momentum in the What-If Simulator and watch how audience sentiment and campaign buzz shift the forecast.
              </p>
              <div className="pt-2 text-[11px] font-mono text-[#5A5A72] flex items-center gap-3">
                <span>• Instant What-If Testing</span>
                <span>• Trailer Hype &amp; Sentiment</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 5. LIVE UPCOMING RELEASES — Strictly Filtered by Current System Date */}
      {/* ========================================================================= */}
      <section id="upcoming-live" className="relative py-24 px-4 sm:px-8 border-t border-[#1E1E2C] bg-[#0A0A10]">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4">
            <div className="space-y-2">
              <span className="text-xs font-mono text-[#E8B74A] uppercase tracking-wider font-semibold flex items-center gap-2">
                <Clock className="w-3.5 h-3.5" />
                <span>[LIVE UPCOMING RADAR • AS OF {todayFormatted.toUpperCase()}]</span>
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                UPCOMING THEATRICAL RELEASES
              </h2>
              <p className="text-xs sm:text-sm text-[#9090AA]">
                Automatically filtered against today&apos;s date so only unreleased upcoming films appear here.
              </p>
            </div>

            <button
              onClick={() => {
                if (isAuthenticated) navigate('/upcoming');
                else openAuthModal();
              }}
              className="px-4 py-2 rounded-xl bg-[#151520] hover:bg-[#202030] border border-[#2A2A3A] hover:border-[#E8B74A]/60 text-white font-mono text-xs transition-all cursor-pointer flex items-center gap-2"
            >
              <span>EXPLORE FULL RADAR</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {(upcomingPortfolio.length > 0
              ? upcomingPortfolio.map((m) => ({
                  id: m.id,
                  title: m.primary_title,
                  date: m.release_date,
                  industry: m.industry,
                  forecast: m.expected_gross_usd,
                  days: m.days_to_release,
                  readiness: m.readiness_score,
                  posterPath: m.poster_path,
                }))
              : FALLBACK_HERO_PREVIEWS.map((m) => ({
                  id: m.id,
                  title: m.title,
                  date: m.releaseDate,
                  industry: m.industry,
                  forecast: m.expectedUsd,
                  days: m.daysToRelease,
                  readiness: 78,
                  posterPath: m.posterPath,
                }))
            ).map((m) => {
              const cardPoster = getPosterUrl(m.posterPath);
              return (
                <div
                  key={m.title}
                  onClick={() => {
                    if (isAuthenticated && m.id) navigate(`/movies/${m.id}`);
                    else handleEnterTerminal();
                  }}
                  className="rounded-2xl bg-[#0E0E16] border border-[#2A2A3A] hover:border-[#6C63FF]/50 transition-all flex flex-col justify-between overflow-hidden group cursor-pointer"
                >
                  {/* Movie Poster Thumbnail Banner */}
                  <div className="relative h-56 w-full bg-[#151520] overflow-hidden border-b border-[#1E1E2C]">
                    {cardPoster ? (
                      <img
                        src={cardPoster}
                        alt={m.title}
                        loading="lazy"
                        className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500"
                      />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-gradient-to-br from-[#161624] to-[#0B0B12]">
                        <Film className="w-8 h-8 text-[#5A5A72] mb-2" />
                        <span className="text-[11px] font-mono text-[#9090AA] line-clamp-1">{m.title}</span>
                      </div>
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0E0E16] via-transparent to-black/30 pointer-events-none" />
                    <div className="absolute top-3 left-3 right-3 flex items-center justify-between text-[11px] font-mono">
                      <span className="px-2 py-0.5 rounded-full bg-black/70 backdrop-blur-md border border-white/10 text-zinc-200">
                        {m.date}
                      </span>
                      <span className="px-2 py-0.5 rounded-full border text-[10px] text-emerald-300 bg-emerald-950/80 backdrop-blur-md border-emerald-500/40">
                        {m.days !== undefined && m.days !== null ? `In ${m.days}d` : m.industry}
                      </span>
                    </div>
                  </div>

                  <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                    <div className="space-y-1">
                      <h4 className="text-base font-bold text-white group-hover:text-[#E8B74A] transition-colors leading-snug line-clamp-1">
                        {m.title}
                      </h4>
                      <p className="text-[11px] font-mono text-[#5A5A72]">{m.industry}</p>
                    </div>

                    <div className="pt-3 border-t border-[#1E1E2C] flex items-baseline justify-between font-mono">
                      <div>
                        <span className="text-[10px] text-[#5A5A72] uppercase">Projected Gross</span>
                        <p className="text-lg font-extrabold text-[#E8B74A]">{formatCurrency(m.forecast, currency)}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] text-[#5A5A72] uppercase">Confidence</span>
                        <p className="text-sm font-bold text-zinc-300">{m.readiness}%</p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 6. CALL TO ACTION */}
      {/* ========================================================================= */}
      <section className="relative py-28 px-4 sm:px-8 border-t border-[#1E1E2C] bg-[#07070B] text-center">
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#111118] border border-[#2A2A3A] text-xs font-mono text-[#E8B74A]">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>READY FOR STUDIO &amp; ANALYST WORKFLOWS</span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
            START FORECASTING UPCOMING RELEASES
          </h2>

          <p className="text-sm text-[#9090AA] max-w-xl mx-auto leading-relaxed">
            Sign in to explore live box-office forecasts, compare upcoming titles side by side, and test production or release scenarios in seconds.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <button
              onClick={handleEnterTerminal}
              className="px-8 py-3.5 rounded-xl bg-gradient-to-r from-[#E8B74A] to-[#D49E28] hover:from-[#F3C766] hover:to-[#E8B74A] text-black font-extrabold text-sm transition-all cursor-pointer shadow-xl shadow-[#E8B74A]/25 flex items-center gap-2 group"
            >
              <span>{isAuthenticated ? 'CONTINUE TO DASHBOARD' : 'SIGN IN / OPEN APP'}</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 7. FOOTER */}
      {/* ========================================================================= */}
      <footer className="border-t border-[#1E1E2C] py-8 px-4 sm:px-8 bg-[#050508] text-xs font-mono text-[#5A5A72]">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>CINEMETRICS • Pre-Release Box-Office Intelligence &amp; Risk Analytics</p>
          <div className="flex items-center gap-4 text-[#9090AA]">
            <span className="flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5 text-[#E8B74A]" /> Hollywood &amp; Indian Cinema
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Flame className="w-3.5 h-3.5 text-amber-400" /> Live Upcoming Radar
            </span>
            <span>•</span>
            <span className="text-emerald-400">Synced {todayFormatted}</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
