import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Filter, SlidersHorizontal, ArrowUpDown, Calendar, Sparkles } from 'lucide-react';
import { apiService } from '../services/api';
import { UpcomingMovieItem } from '../types';
import { MovieCard } from '../components/MovieCard';

export const UpcomingRadarPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [movies, setMovies] = useState<UpcomingMovieItem[]>([]);
  const [loading, setLoading] = useState(true);

  const initialSegment = searchParams.get('market_segment') || 'All';
  const initialSort = searchParams.get('sort_by') || 'date';

  const [segment, setSegment] = useState<string>(initialSegment);
  const [sortBy, setSortBy] = useState<string>(initialSort);
  const [minReadiness, setMinReadiness] = useState<number>(0);
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    async function fetchUpcoming() {
      try {
        setLoading(true);
        const data = await apiService.getUpcomingMovies({
          market_segment: segment === 'All' ? undefined : segment,
          sort_by: sortBy,
          min_readiness: minReadiness > 0 ? minReadiness : undefined,
          limit: 60,
        });
        setMovies(data);
      } catch (err) {
        console.error('Failed to load upcoming movies:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchUpcoming();
  }, [segment, sortBy, minReadiness]);

  // Client-side text filter if user typed in quick query
  const filteredMovies = movies.filter((m) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      m.primary_title.toLowerCase().includes(q) ||
      m.director.toLowerCase().includes(q) ||
      m.lead_actor.toLowerCase().includes(q) ||
      m.industry.toLowerCase().includes(q)
    );
  });

  const segments = ['All', 'Bollywood', 'Tollywood', 'Kollywood', 'Hollywood'];

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#E8B74A] uppercase tracking-wider mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Autonomous Pipeline • Continuous Ingestion</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
            Upcoming Releases Intelligence Radar
          </h1>
          <p className="text-xs sm:text-sm text-[#9090AA] mt-1">
            Tracking theatrical releases with dynamic Prediction Readiness Scores (PRS) and calibrated conformal bands.
          </p>
        </div>

        <div className="text-right">
          <p className="text-xs text-[#9090AA]">Tracked Active Titles</p>
          <p className="text-2xl font-extrabold font-mono text-[#E8B74A]">
            {filteredMovies.length} Films
          </p>
        </div>
      </div>

      {/* Filter & Control Bar */}
      <div className="glass-panel rounded-2xl p-4 sm:p-5 border border-[#2A2A3A] space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Industry Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5">
            {segments.map((seg) => (
              <button
                key={seg}
                onClick={() => {
                  setSegment(seg);
                  setSearchParams({ market_segment: seg, sort_by: sortBy });
                }}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
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
                setSearchParams({ market_segment: segment, sort_by: e.target.value });
              }}
              className="bg-[#15151E] border border-[#2A2A3A] text-xs text-white rounded-xl px-3 py-1.5 focus:outline-none focus:border-[#6C63FF]"
            >
              <option value="date">Release Date (Chronological)</option>
              <option value="forecast">Projected Gross (Highest)</option>
              <option value="buzz">Digital Viral Velocity</option>
              <option value="readiness">Prediction Readiness Score</option>
            </select>
          </div>
        </div>

        {/* Second Row: Minimum Readiness & Quick Title Filter */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-[#2A2A3A]/60">
          <div className="flex items-center gap-3">
            <span className="text-xs text-[#9090AA] font-mono">Min Readiness:</span>
            <div className="flex items-center gap-1">
              {[0, 40, 60, 80].map((score) => (
                <button
                  key={score}
                  onClick={() => setMinReadiness(score)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all ${
                    minReadiness === score
                      ? 'bg-[#6C63FF] text-white font-bold'
                      : 'bg-[#15151E] text-[#9090AA] hover:text-white border border-[#2A2A3A]'
                  }`}
                >
                  {score === 0 ? 'All' : `PRS ≥ ${score}`}
                </button>
              ))}
            </div>
          </div>

          <div className="w-full sm:w-64">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter by title, talent..."
              className="w-full bg-[#15151E] border border-[#2A2A3A] rounded-xl px-3 py-1.5 text-xs text-white placeholder-[#5A5A72] focus:outline-none focus:border-[#6C63FF]"
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
          <p className="text-xs">Try relaxing your minimum readiness threshold or selecting 'All' segments.</p>
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

