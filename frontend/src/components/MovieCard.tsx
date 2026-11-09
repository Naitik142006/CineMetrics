import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Play, Calendar, Sparkles, Film } from 'lucide-react';
import { UpcomingMovieItem, MovieSummary } from '../types';
import { useCurrency } from '../context/CurrencyContext';
import { formatCurrency, getRiskBadgeClass, getPosterUrl } from '../utils/format';
import { PredictionIntervalBar } from './PredictionIntervalBar';

interface MovieCardProps {
  movie: UpcomingMovieItem | MovieSummary;
}

export const MovieCard: React.FC<MovieCardProps> = ({ movie }) => {
  const { currency } = useCurrency();
  const [imgError, setImgError] = useState(false);

  const isUpcoming = 'readiness_score' in movie;
  const upcomingMovie = isUpcoming ? (movie as UpcomingMovieItem) : null;

  const expectedUsd = upcomingMovie
    ? upcomingMovie.expected_gross_usd
    : (movie as MovieSummary).box_office_gross_usd || 0.0;
  const pessUsd = upcomingMovie ? upcomingMovie.pessimistic_bound_80_usd : expectedUsd * 0.7;
  const optUsd = upcomingMovie ? upcomingMovie.optimistic_bound_80_usd : expectedUsd * 1.45;

  const riskClass = getRiskBadgeClass(upcomingMovie ? upcomingMovie.risk_assessment_tier : 'Safe');

  const readinessScore = upcomingMovie ? upcomingMovie.readiness_score : 100;
  const confidenceLabel =
    readinessScore >= 80
      ? 'High Confidence'
      : readinessScore >= 60
      ? 'Good Confidence'
      : 'Early Estimate';

  const posterUrl = !imgError ? getPosterUrl(movie.poster_path) : null;

  const renderStageBadge = () => {
    if (!upcomingMovie) {
      return (
        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-950/80 backdrop-blur-md text-emerald-300 border border-emerald-500/40">
          Released
        </span>
      );
    }

    const days = upcomingMovie.days_to_release;
    const isStage4 = upcomingMovie.is_stage4_active || (days !== undefined && days !== null && days > 0 && days <= 7);

    if (isStage4) {
      return (
        <span
          title={`Stage 4 Advance Pre-Sales Active • Days to Release: ${days ?? '<7'}d • High Precision Bayesian Posterior (R² ≥ 0.925)`}
          className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-purple-950/90 text-purple-300 border border-purple-500/70 shadow-lg shadow-purple-500/20 backdrop-blur-md flex items-center gap-1 animate-pulse"
        >
          <Sparkles className="w-2.5 h-2.5" />
          <span>Stage 4 {days ? `(T-${days}d)` : '(R²≥0.92)'}</span>
        </span>
      );
    }

    if (days !== undefined && days !== null && days <= 30) {
      return (
        <span
          title={`Stage 3 Pre-Release Blitz • Days to Release: ${days}d • Multi-Modal Ensemble Prior`}
          className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-blue-950/80 text-blue-300 border border-blue-500/50 backdrop-blur-md flex items-center gap-1"
        >
          <span>Stage 3 (T-{days}d)</span>
        </span>
      );
    }

    if (days !== undefined && days !== null && days <= 90) {
      return (
        <span
          title={`Stage 2 Teaser Campaign • Days to Release: ${days}d • Buzz & Sentiment Prior`}
          className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-amber-950/80 text-amber-300 border border-amber-500/50 backdrop-blur-md flex items-center gap-1"
        >
          <span>Stage 2 (T-{days}d)</span>
        </span>
      );
    }

    return (
      <span
        title={`Stage 1 Announcement Prior • Days to Release: ${days ?? '>90'}d • Structural Talent Prior`}
        className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-zinc-900/80 text-zinc-300 border border-zinc-700 backdrop-blur-md flex items-center gap-1"
      >
        <span>Stage 1 {days ? `(T-${days}d)` : 'Prior'}</span>
      </span>
    );
  };

  return (
    <div className="glass-card rounded-2xl overflow-hidden border border-[#2A2A3A] flex flex-col justify-between group hover:border-[#E8B74A]/50 transition-all duration-300">
      {/* Top Poster Image Container */}
      <div className="relative h-56 w-full overflow-hidden bg-[#101018]">
        {posterUrl ? (
          <img
            src={posterUrl}
            alt={movie.primary_title}
            loading="lazy"
            onError={() => setImgError(true)}
            className="w-full h-full object-cover object-top transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-[#1A1A28] via-[#12121A] to-[#0A0A10] p-4 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_40%,rgba(108,99,255,0.12),transparent_70%)]" />
            <Film className="w-10 h-10 text-zinc-600 mb-2 group-hover:text-[#E8B74A] transition-colors" />
            <span className="text-xs font-semibold text-zinc-300 line-clamp-1">{movie.primary_title}</span>
            <span className="text-[10px] text-zinc-500 mt-1 uppercase tracking-wider">{movie.industry || 'Cinema'}</span>
          </div>
        )}

        {/* Gradient Overlay for Readable Badges */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#12121A] via-[#12121A]/20 to-black/60 pointer-events-none" />

        {/* Floating Top Badges */}
        <div className="absolute top-3 left-3 right-3 flex items-center justify-between gap-2 z-10">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-black/70 backdrop-blur-md border border-white/10 text-zinc-200">
              {movie.industry || 'Global'}
            </span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#E8B74A]/25 backdrop-blur-md text-[#E8B74A] border border-[#E8B74A]/40">
              {movie.release_year || '2026'}
            </span>
          </div>

          {renderStageBadge()}
        </div>

        {/* Trailer Play Button Overlay */}
        {movie.youtube_trailer_id && (
          <a
            href={`https://www.youtube.com/watch?v=${movie.youtube_trailer_id}`}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="absolute bottom-3 right-3 z-10 p-2.5 rounded-full bg-black/70 backdrop-blur-md border border-white/20 text-white hover:bg-red-600 hover:border-red-500 transition-all shadow-lg group/play"
            title="Watch Official Trailer"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
          </a>
        )}
      </div>

      {/* Card Content & Metadata */}
      <div className="p-4 pb-3 flex-1 flex flex-col justify-between">
        <div>
          {/* Title */}
          <Link to={`/movies/${movie.id}`}>
            <h3 className="font-bold text-base text-white group-hover:text-[#E8B74A] transition-colors line-clamp-1">
              {movie.primary_title}
            </h3>
          </Link>

          {/* Talent & Date */}
          <p className="text-xs text-[#9090AA] mt-1 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-[#5A5A72]" />
            <span>{movie.release_date || `${movie.release_year}`}</span>
            <span>•</span>
            <span className="truncate max-w-[140px]">{movie.director || 'Director TBD'}</span>
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
      </div>

      {/* Middle Financial Forecast Section */}
      <div className="px-4 py-3 bg-[#111118]/60 border-t border-b border-[#2A2A3A]/40 space-y-2">
        <div className="flex items-baseline justify-between">
          <span className="text-[11px] text-[#9090AA] uppercase font-mono font-medium">
            {isUpcoming ? 'Most Likely Gross' : 'Theatrical Gross'}
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
      <div className="p-3.5 flex items-center justify-between gap-2">
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
