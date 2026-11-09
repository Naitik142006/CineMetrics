import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Filter,
  SlidersHorizontal,
  ArrowUpDown,
  Calendar,
  Sparkles,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Clock,
  CheckCircle2,
} from 'lucide-react';
import { apiService } from '../services/api';
import { UpcomingMovieItem } from '../types';
import { MovieCard } from '../components/MovieCard';

export const UpcomingRadarPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [movies, setMovies] = useState<UpcomingMovieItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showGuide, setShowGuide] = useState(true);
  const [syncStatus, setSyncStatus] = useState<any>(null);
  const [syncing, setSyncing] = useState<boolean>(false);

  const initialSegment = searchParams.get('market_segment') || 'All';
  const initialSort = searchParams.get('sort_by') || 'forecast';
  const initialYear = searchParams.get('year') || 'All';

  const [segment, setSegment] = useState<string>(initialSegment);
  const [sortBy, setSortBy] = useState<string>(initialSort);
  const [yearFilter, setYearFilter] = useState<string>(initialYear);
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    async function fetchUpcoming() {
      try {
        setLoading(true);
        const data = await apiService.getUpcomingMovies({
          market_segment: segment === 'All' ? undefined : segment,
          sort_by: sortBy,
          limit: 150,
        });
        setMovies(data);
      } catch (err) {
        console.error('Failed to load upcoming movies:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchUpcoming();
  }, [segment, sortBy]);

  useEffect(() => {
    async function loadSync() {
      try {
        const s = await apiService.getSyncStatus();
        setSyncStatus(s);
      } catch (e) {
        console.warn('Sync status unavailable:', e);
      }
    }
    loadSync();
  }, []);

  const handleManualSync = async () => {
    try {
      setSyncing(true);
      await apiService.triggerSync(true, 30);
      const s = await apiService.getSyncStatus();
      setSyncStatus(s);
      const updatedMovies = await apiService.getUpcomingMovies({
        market_segment: segment === 'All' ? undefined : segment,
        sort_by: sortBy,
        limit: 150,
      });
      setMovies(updatedMovies);
    } catch (e) {
      console.error('Sync failed:', e);
    } finally {
      setSyncing(false);
    }
  };

  // Client-side filter for Year and Search query
  const filteredMovies = movies.filter((m) => {
    // Year filter
    if (yearFilter !== 'All') {
      const targetYear = parseInt(yearFilter, 10);
      if (m.release_year !== targetYear) {
        return false;
      }
    }

    // Text search query
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      m.primary_title.toLowerCase().includes(q) ||
      (m.director && m.director.toLowerCase().includes(q)) ||
      (m.lead_actor && m.lead_actor.toLowerCase().includes(q)) ||
      (m.industry && m.industry.toLowerCase().includes(q))
    );
  });

  const segments = ['All', 'Hollywood', 'Bollywood', 'Tollywood', 'Kollywood'];
  const years = ['All', '2026', '2027'];

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#E8B74A] uppercase tracking-wider mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>2026–2027 Marquee Releases • Theatrical AI Forecasting</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
            Upcoming Movies Intelligence Radar
          </h1>
          <p className="text-xs sm:text-sm text-[#9090AA] mt-1">
            Discover projected worldwide box office earnings, best-case vs worst-case ranges, and AI confidence for announced titles.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-xs text-[#9090AA]">Tracked 2026–2027 Titles</p>
            <p className="text-2xl font-extrabold font-mono text-[#E8B74A]">
              {filteredMovies.length} Films
            </p>
          </div>
        </div>
      </div>

      {/* Expandable Plain-English Guide */}
      <div className="glass-panel rounded-2xl p-4 sm:p-5 border border-[#2A2A3A] transition-all">
        <div
          className="flex items-center justify-between cursor-pointer"
          onClick={() => setShowGuide(!showGuide)}
        >
          <div className="flex items-center gap-2 text-sm font-bold text-white">
            <HelpCircle className="w-4 h-4 text-[#E8B74A]" />
            <span>How to understand these predictions in 30 seconds</span>
          </div>
          <button className="text-xs text-[#9090AA] flex items-center gap-1 hover:text-white">
            <span>{showGuide ? 'Hide Guide' : 'Show Guide'}</span>
            {showGuide ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>

        {showGuide && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 pt-4 border-t border-[#2A2A3A]/60">
            <div className="bg-[#15151E] p-3.5 rounded-xl border border-[#2A2A3A]/70 space-y-1">
              <p className="text-xs font-bold text-[#E8B74A]">1. Most Likely Gross</p>
              <p className="text-xs text-[#9090AA] leading-relaxed">
                The gold center number is the AI's primary forecast based on historical box office patterns across 10,000+ past movies.
              </p>
            </div>
            <div className="bg-[#15151E] p-3.5 rounded-xl border border-[#2A2A3A]/70 space-y-1">
              <p className="text-xs font-bold text-emerald-400">2. Best-Case vs Worst-Case</p>
              <p className="text-xs text-[#9090AA] leading-relaxed">
                The colored bar shows the expected range. 8 out of 10 times, the final box office lands between the conservative floor and breakout ceiling.
              </p>
            </div>
            <div className="bg-[#15151E] p-3.5 rounded-xl border border-[#2A2A3A]/70 space-y-1">
              <p className="text-xs font-bold text-blue-400">3. AI Confidence %</p>
              <p className="text-xs text-[#9090AA] leading-relaxed">
                Higher confidence (80%+) indicates official trailers are released, audience sentiment is measured, and budgets are confirmed.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Live Synchronization Status Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-[#111118] border border-[#2A2A3A] rounded-xl px-4 py-3 text-xs">
        <div className="flex items-center gap-2.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-bold text-white">Live Data Pipeline:</span>
          <span className="text-[#9090AA]">
            Auto-Sync Active (Every 7 Days via OMDb & YouTube Buzz)
          </span>
          {syncStatus?.last_sync_timestamp && (
            <span className="hidden md:inline text-[#5A5A72] border-l border-[#2A2A3A] pl-2.5">
              Last synced: {new Date(syncStatus.last_sync_timestamp).toLocaleDateString()}
            </span>
          )}
        </div>
        <button
          onClick={handleManualSync}
          disabled={syncing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#6C63FF]/20 hover:bg-[#6C63FF]/30 border border-[#6C63FF]/40 text-[#E8B74A] font-bold text-xs transition-all cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
          <span>{syncing ? 'Syncing OMDb...' : 'Sync Now'}</span>
        </button>
      </div>

      {/* Filter & Control Bar */}
      <div className="glass-panel rounded-2xl p-4 sm:p-5 border border-[#2A2A3A] space-y-4">
        {/* Row 1: Industry Pills + Year Filter + Sort */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Industry Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs text-[#9090AA] mr-1 font-mono">Industry:</span>
            {segments.map((seg) => (
              <button
                key={seg}
                onClick={() => {
                  setSegment(seg);
                  setSearchParams({ market_segment: seg, sort_by: sortBy, year: yearFilter });
                }}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                  segment === seg
                    ? 'bg-[#E8B74A] text-black font-bold shadow-[0_0_15px_rgba(232,183,74,0.3)]'
                    : 'bg-[#15151E] hover:bg-[#1A1A26] text-[#9090AA] hover:text-white border border-[#2A2A3A]'
                }`}
              >
                {seg}
              </button>
            ))}
          </div>

          {/* Sort Selector */}
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-[#9090AA]" />
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value);
                setSearchParams({ market_segment: segment, sort_by: e.target.value, year: yearFilter });
              }}
              className="bg-[#15151E] border border-[#2A2A3A] text-xs text-white rounded-xl px-3 py-1.5 focus:outline-none focus:border-[#6C63FF]"
            >
              <option value="forecast">Highest Projected Gross</option>
              <option value="date">Release Date (Chronological)</option>
              <option value="buzz">Most Viral Buzz (Trailers & Hype)</option>
              <option value="readiness">AI Confidence Score</option>
            </select>
          </div>
        </div>

        {/* Row 2: Year Pills & Quick Title Search */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-[#2A2A3A]/60">
          {/* Year Buttons */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#9090AA] font-mono">Release Year:</span>
            <div className="flex items-center gap-1">
              {years.map((y) => (
                <button
                  key={y}
                  onClick={() => {
                    setYearFilter(y);
                    setSearchParams({ market_segment: segment, sort_by: sortBy, year: y });
                  }}
                  className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold transition-all ${
                    yearFilter === y
                      ? 'bg-[#6C63FF] text-white font-bold'
                      : 'bg-[#15151E] text-[#9090AA] hover:text-white border border-[#2A2A3A]'
                  }`}
                >
                  {y === 'All' ? 'All (2026–2027)' : `${y} Releases`}
                </button>
              ))}
            </div>
          </div>

          {/* Search Box */}
          <div className="w-full sm:w-72">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search movie title, star, director..."
              className="w-full bg-[#15151E] border border-[#2A2A3A] rounded-xl px-3.5 py-1.5 text-xs text-white placeholder-[#5A5A72] focus:outline-none focus:border-[#6C63FF]"
            />
          </div>
        </div>
      </div>

      {/* Grid of Movie Cards */}
      {loading ? (
        <div className="py-20 text-center space-y-3">
          <div className="w-8 h-8 border-4 border-[#6C63FF] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs font-mono text-[#9090AA]">Updating radar with real-time predictions...</p>
        </div>
      ) : filteredMovies.length === 0 ? (
        <div className="glass-card rounded-2xl p-12 text-center text-[#9090AA]">
          <p className="text-base text-white font-semibold mb-1">No movies matched your filter criteria.</p>
          <p className="text-xs">Try selecting 'All' segments or searching for a different keyword.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMovies.map((movie) => (
            <MovieCard key={movie.id} movie={movie} />
          ))}
        </div>
      )}
    </div>
  );
};
