import React from 'react';
import { Link } from 'react-router-dom';
import { Play, TrendingUp, Calendar, Film } from 'lucide-react';
import { UpcomingMovieItem, MovieSummary } from '../types';
import { useCurrency } from '../context/CurrencyContext';
import { formatCurrency, getRiskBadgeClass } from '../utils/format';
import { PredictionIntervalBar } from './PredictionIntervalBar';

interface MovieCardProps {
  movie: UpcomingMovieItem | MovieSummary;
}

export const MovieCard: React.FC<MovieCardProps> = ({ movie }) => {
  const { currency } = useCurrency();

  const isUpcoming = 'readiness_score' in movie;
  const upcomingMovie = isUpcoming ? (movie as UpcomingMovieItem) : null;

  const expectedUsd = upcomingMovie
    ? upcomingMovie.expected_gross_usd
    : (movie as MovieSummary).box_office_gross_usd || 0.0;
  const pessUsd = upcomingMovie ? upcomingMovie.pessimistic_bound_80_usd : expectedUsd * 0.7;
  const optUsd = upcomingMovie ? upcomingMovie.optimistic_bound_80_usd : expectedUsd * 1.45;

  const riskClass = getRiskBadgeClass(upcomingMovie ? upcomingMovie.risk_assessment_tier : 'Safe');

  return (
    <div className="glass-card rounded-2xl overflow-hidden border border-[#2A2A3A] flex flex-col justify-between group hover:border-[#6C63FF]/50 transition-all duration-300">
      {/* Top Header & Poster Placeholder / Banner */}
      <div className="relative p-5 pb-3">
        {/* Industry & Readiness Pills */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-[#1A1A26] border border-[#2A2A3A] text-zinc-300">
            {movie.industry || 'Global'}
          </span>

          {upcomingMovie && (
            <span
              className={`text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full border ${
                upcomingMovie.readiness_score >= 80
                  ? 'bg-emerald-950/60 text-emerald-400 border-emerald-500/40'
                  : upcomingMovie.readiness_score >= 60
                  ? 'bg-amber-950/60 text-amber-400 border-amber-500/40'
                  : 'bg-zinc-800 text-zinc-400 border-zinc-700'
              }`}
            >
              PRS {upcomingMovie.readiness_score}
            </span>
          )}
        </div>

        {/* Title */}
        <Link to={`/movies/${movie.id}`}>
          <h3 className="font-bold text-lg text-white group-hover:text-[#E8B74A] transition-colors line-clamp-1">
            {movie.primary_title}
          </h3>
        </Link>

        {/* Talent & Date */}
        <p className="text-xs text-[#9090AA] mt-1 flex items-center gap-1.5">
          <Calendar className="w-3.5 h-3.5 text-[#5A5A72]" />
          <span>{movie.release_date || `${movie.release_year}`}</span>
          <span>•</span>
          <span className="truncate max-w-[150px]">{movie.director || 'Director TBD'}</span>
        </p>

        {/* Genres */}
        <div className="flex flex-wrap gap-1 mt-2.5">
          {(movie.genres || []).slice(0, 3).map((g, idx) => (
            <span
              key={idx}
              className="text-[10px] px-2 py-0.5 rounded bg-[#15151E] text-[#9090AA] border border-[#2A2A3A]/60"
            >
              {g}
            </span>
          ))}
        </div>
      </div>

      {/* Middle Financial Forecast Section */}
      <div className="px-5 py-3 bg-[#111118]/60 border-t border-b border-[#2A2A3A]/40 space-y-2.5">
        <div className="flex items-baseline justify-between">
          <span className="text-[11px] text-[#9090AA] uppercase font-mono">
            {isUpcoming ? 'Projected Worldwide' : 'Box-Office Gross'}
          </span>
          <span className="text-lg font-extrabold font-mono text-[#E8B74A]">
            {formatCurrency(expectedUsd, currency)}
          </span>
        </div>

        {/* Mini Conformal Confidence Bar */}
        {isUpcoming && (
          <PredictionIntervalBar
            expectedUsd={expectedUsd}
            pessimisticUsd={pessUsd}
            optimisticUsd={optUsd}
            compact={true}
          />
        )}
      </div>

      {/* Footer & Actions */}
      <div className="p-4 flex items-center justify-between gap-2">
        {upcomingMovie ? (
          <span
            className={`text-[11px] px-2.5 py-1 rounded-lg border font-medium ${riskClass.bg} ${riskClass.text} ${riskClass.border}`}
          >
            {upcomingMovie.risk_badge || upcomingMovie.risk_assessment_tier}
          </span>
        ) : (
          <span className="text-[11px] px-2.5 py-1 rounded-lg bg-[#1A1A26] text-zinc-300 border border-[#2A2A3A]">
            Historical Release
          </span>
        )}

        <div className="flex items-center gap-1.5">
          {movie.youtube_trailer_id && (
            <a
              href={`https://www.youtube.com/watch?v=${movie.youtube_trailer_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-xl bg-[#1A1A26] border border-[#2A2A3A] hover:border-red-500/50 hover:text-red-400 text-[#9090AA] transition-colors"
              title="Watch Official Trailer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
            </a>
          )}

          <Link
            to={`/movies/${movie.id}`}
            className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-[#6C63FF]/20 hover:bg-[#6C63FF]/30 border border-[#6C63FF]/40 text-xs font-semibold text-white transition-all"
          >
            <span>Dossier</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
