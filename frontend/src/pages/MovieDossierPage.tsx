import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Calendar,
  User,
  Film,
  DollarSign,
  TrendingUp,
  ShieldAlert,
  Play,
  ArrowLeft,
  CheckCircle,
  HelpCircle,
  History,
  Sparkles,
  ShieldCheck,
  Award,
} from 'lucide-react';
import { apiService } from '../services/api';
import {
  MovieDetail,
  ActivePredictionResponse,
  SHAPWaterfallResponse,
  SimilarMovie,
} from '../types';
import { useCurrency } from '../context/CurrencyContext';
import { formatCurrency, getRiskBadgeClass, getSuccessCategoryBadge, getPosterUrl } from '../utils/format';
import { PredictionIntervalBar } from '../components/PredictionIntervalBar';
import { SHAPWaterfall } from '../components/SHAPWaterfall';

export const MovieDossierPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { currency } = useCurrency();

  const [movie, setMovie] = useState<MovieDetail | null>(null);
  const [prediction, setPrediction] = useState<ActivePredictionResponse | null>(null);
  const [explanation, setExplanation] = useState<SHAPWaterfallResponse | null>(null);
  const [similarMovies, setSimilarMovies] = useState<SimilarMovie[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [posterError, setPosterError] = useState(false);

  useEffect(() => {
    if (!id) return;

    async function loadDossier() {
      try {
        setLoading(true);
        setError(null);

        // Fetch movie details
        const movieData = await apiService.getMovieDetail(id!);
        setMovie(movieData);

        // Fetch prediction
        try {
          const predData = await apiService.getMoviePrediction(id!);
          setPrediction(predData);
        } catch (e) {
          console.warn('Prediction unavailable or suppressed:', e);
        }

        // Fetch SHAP explanation
        try {
          const explData = await apiService.getMovieExplanation(id!);
          setExplanation(explData);
        } catch (e) {
          console.warn('SHAP explanation unavailable:', e);
        }

        // Fetch similar movies
        try {
          const simData = await apiService.getSimilarMovies(id!, 4);
          setSimilarMovies(simData);
        } catch (e) {
          console.warn('Similar movies unavailable:', e);
        }

        // Fetch prediction revision history
        try {
          const histData = await apiService.getPredictionHistory(id!);
          setHistory(histData || []);
        } catch (e) {
          console.warn('History unavailable:', e);
        }
      } catch (err: any) {
        console.error('Failed to load movie dossier:', err);
        setError('Movie record could not be found.');
      } finally {
        setLoading(false);
      }
    }

    loadDossier();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3">
        <div className="w-10 h-10 border-4 border-[#6C63FF] border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-mono text-[#9090AA]">Assembling Movie Intelligence Dossier...</p>
      </div>
    );
  }

  if (error || !movie) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-4">
        <div className="glass-card rounded-2xl p-8 border border-rose-500/30">
          <p className="text-rose-400 font-semibold mb-2">{error || 'Movie not found'}</p>
          <Link to="/" className="text-xs text-[#6C63FF] hover:underline">
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const riskClass = getRiskBadgeClass(
    prediction?.financial_risk.risk_assessment_tier || 'Moderate Risk'
  );

  const confidenceScore = prediction?.readiness_score || 75;
  const confidenceBadge =
    confidenceScore >= 80
      ? 'High Confidence (80%+)'
      : confidenceScore >= 60
      ? 'Moderate Confidence'
      : 'Early Estimate';

  const posterUrl = !posterError ? getPosterUrl(movie.poster_path) : null;

  return (
    <div className="space-y-8 pb-20">
      {/* Back button */}
      <Link
        to="/upcoming"
        className="inline-flex items-center gap-2 text-xs font-semibold text-[#9090AA] hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Upcoming Radar</span>
      </Link>

      {/* Dossier Header Banner */}
      <div className="relative glass-panel rounded-3xl p-6 lg:p-8 border border-[#2A2A3A] overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-[#E8B74A]/15 to-[#6C63FF]/20 blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-start gap-6 lg:gap-8 justify-between">
          {/* Theatrical Poster */}
          <div className="w-40 sm:w-48 lg:w-52 aspect-[2/3] rounded-2xl overflow-hidden border border-[#2A2A3A] shadow-2xl flex-shrink-0 bg-[#12121A] relative group">
            {posterUrl ? (
              <img
                src={posterUrl}
                alt={movie.primary_title}
                onError={() => setPosterError(true)}
                className="w-full h-full object-cover object-center"
              />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-gradient-to-b from-[#1A1A28] to-[#0D0D14]">
                <Film className="w-12 h-12 text-zinc-600 mb-2" />
                <span className="text-xs font-semibold text-zinc-400 line-clamp-2">{movie.primary_title}</span>
                <span className="text-[10px] text-zinc-600 mt-1 uppercase tracking-wider">{movie.industry}</span>
              </div>
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none" />
          </div>

          {/* Dossier Core Info */}
          <div className="space-y-3 flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-[#1A1A26] border border-[#2A2A3A] text-zinc-300">
                {movie.industry}
              </span>
              <span className="text-xs font-bold px-3 py-1 rounded-full bg-[#E8B74A]/15 text-[#E8B74A] border border-[#E8B74A]/30">
                {movie.release_year || '2026'} Release
              </span>
              {movie.is_released ? (
                <span className="text-xs font-semibold px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/40 text-emerald-400">
                  Released Film
                </span>
              ) : (
                <span className="text-xs font-semibold px-3 py-1 rounded-full bg-blue-950/60 border border-blue-500/40 text-blue-400">
                  Theatrical Pre-Release
                </span>
              )}
              {prediction && (
                <span
                  title="Confidence based on metadata completeness, official trailer views, and confirmed talent"
                  className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-amber-950/60 border border-amber-500/40 text-amber-400 flex items-center gap-1"
                >
                  <Sparkles className="w-3 h-3" />
                  <span>AI Confidence: {confidenceScore}% ({confidenceBadge})</span>
                </span>
              )}
            </div>

            <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
              {movie.primary_title}
            </h1>

            {movie.overview && (
              <p className="text-sm text-[#9090AA] leading-relaxed max-w-2xl">{movie.overview}</p>
            )}

            {/* Metadata Pills */}
            <div className="flex flex-wrap items-center gap-4 text-xs text-[#9090AA] pt-2">
              <div className="flex items-center gap-1.5">
                <Calendar className="w-4 h-4 text-[#5A5A72]" />
                <span>{movie.release_date || `${movie.release_year}`}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <User className="w-4 h-4 text-[#5A5A72]" />
                <Link
                  to={`/talent/director/${encodeURIComponent(movie.director || '')}`}
                  className="hover:text-[#E8B74A] underline decoration-dotted"
                >
                  {movie.director || 'Unknown Director'}
                </Link>
              </div>
              <div className="flex items-center gap-1.5">
                <Film className="w-4 h-4 text-[#5A5A72]" />
                <Link
                  to={`/talent/actor/${encodeURIComponent(movie.lead_actor || '')}`}
                  className="hover:text-[#E8B74A] underline decoration-dotted"
                >
                  {movie.lead_actor || 'Unknown Lead'}
                </Link>
              </div>
            </div>
          </div>

          {/* Quick Action / Budget Highlight */}
          <div className="bg-[#15151E] rounded-2xl p-5 border border-[#2A2A3A] min-w-[200px] text-right space-y-3 self-start flex-shrink-0">
            <div>
              <p className="text-[11px] text-[#9090AA] uppercase font-mono">Reported Budget</p>
              <p className="text-xl font-bold font-mono text-white">
                {formatCurrency(movie.budget_usd, currency)}
              </p>
            </div>

            {movie.youtube_trailer_id && (
              <a
                href={`https://www.youtube.com/watch?v=${movie.youtube_trailer_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-red-600/20 hover:bg-red-600/30 border border-red-500/40 text-red-400 text-xs font-semibold transition-colors"
              >
                <Play className="w-4 h-4 fill-current" />
                <span>Watch Trailer</span>
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Prominent Executive AI Summary Box */}
      {prediction && (
        <div className="glass-card rounded-2xl p-5 sm:p-6 border border-[#E8B74A]/40 bg-gradient-to-r from-[#1A1A26] to-[#15151E] space-y-3">
          <div className="flex items-center gap-2 text-sm font-bold text-[#E8B74A]">
            <Award className="w-4 h-4 text-[#E8B74A]" />
            <span>AI Executive Verdict Summary</span>
          </div>
          <p className="text-sm text-zinc-200 leading-relaxed">
            {prediction.forecast.expected_gross_usd > movie.budget_usd * 2.5 ? (
              <>
                <strong className="text-white">{movie.primary_title}</strong> is projected to be a{' '}
                <span className="text-[#E8B74A] font-bold">highly profitable commercial winner</span>,
                with an estimated worldwide box office of{' '}
                <strong className="text-white">
                  {formatCurrency(prediction.forecast.expected_gross_usd, currency)}
                </strong>
                . Against an estimated budget of {formatCurrency(movie.budget_usd, currency)}, it is
                positioned to comfortably generate healthy theatrical profits.
              </>
            ) : (
              <>
                <strong className="text-white">{movie.primary_title}</strong> is projected to reach{' '}
                <strong className="text-white">
                  {formatCurrency(prediction.forecast.expected_gross_usd, currency)}
                </strong>{' '}
                worldwide against a budget of {formatCurrency(movie.budget_usd, currency)}. Meeting its
                break-even hurdle will depend heavily on opening weekend critical reviews and positive
                social sentiment.
              </>
            )}
          </p>
          <div className="flex flex-wrap items-center gap-4 text-xs text-[#9090AA] pt-1">
            <span>
              🎯 <strong className="text-zinc-300">Target Break-Even:</strong> {formatCurrency(movie.budget_usd * 2.2, currency)}
            </span>
            <span>
              📈 <strong className="text-zinc-300">Break-Even Probability:</strong>{' '}
              <span className="text-emerald-400 font-bold">
                {(prediction.financial_risk.prob_break_even * 100).toFixed(0)}%
              </span>
            </span>
            <span>
              🌟 <strong className="text-zinc-300">Predicted Verdict:</strong>{' '}
              <span className="text-[#E8B74A] font-bold">
                {prediction.success_classification.predicted_category}
              </span>
            </span>
          </div>
        </div>
      )}

      {/* Conformal Prediction Range & Financial Risk Pillars */}
      {prediction && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Conformal Forecast (2 columns) */}
          <div className="lg:col-span-2 space-y-6">
            <PredictionIntervalBar
              expectedUsd={prediction.forecast.expected_gross_usd}
              pessimisticUsd={prediction.forecast.pessimistic_bound_80_usd}
              optimisticUsd={prediction.forecast.optimistic_bound_80_usd}
              confidenceLevel={0.8}
            />

            {/* Likely Box Office Verdict Probabilities */}
            <div className="glass-card rounded-2xl p-5 border border-[#2A2A3A]">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h4 className="text-sm font-semibold text-white tracking-wide">
                    Likely Box Office Verdict (Outcome Probabilities)
                  </h4>
                  <p className="text-[11px] text-[#9090AA] mt-0.5">
                    How likely this film will achieve each commercial classification tier.
                  </p>
                </div>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#E8B74A]/15 text-[#E8B74A] border border-[#E8B74A]/30 font-semibold">
                  Most Likely: {prediction.success_classification.predicted_category}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {Object.entries(prediction.success_classification.probabilities).map(
                  ([tier, prob]) => {
                    const badge = getSuccessCategoryBadge(tier);
                    return (
                      <div
                        key={tier}
                        className={`rounded-xl p-3 border ${badge.bg} ${badge.border} flex flex-col justify-between`}
                      >
                        <p className={`text-xs font-semibold ${badge.text}`}>{tier}</p>
                        <p className="text-lg font-bold font-mono text-white mt-1">
                          {(prob * 100).toFixed(0)}%
                        </p>
                      </div>
                    );
                  }
                )}
              </div>
            </div>
          </div>

          {/* Financial Safety & Profitability Odds (1 column) */}
          <div className="glass-card rounded-2xl p-6 border border-[#2A2A3A] space-y-5">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-400" />
              <h3 className="text-sm font-bold text-white tracking-wide">
                Financial Safety & Profit Odds
              </h3>
            </div>

            <div className={`rounded-xl p-4 border ${riskClass.bg} ${riskClass.border} space-y-1`}>
              <p className="text-[11px] text-[#9090AA] uppercase font-mono">Investment Safety Rating</p>
              <p className={`text-base font-bold ${riskClass.text}`}>
                {prediction.financial_risk.risk_assessment_tier}
              </p>
              <p className="text-xs text-[#9090AA] pt-1">
                {prediction.financial_risk.break_even_status}
              </p>
            </div>

            <div className="space-y-3 pt-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-[#9090AA]">Chance to Break Even:</span>
                <span className="font-mono font-bold text-emerald-400">
                  {(prediction.financial_risk.prob_break_even * 100).toFixed(0)}%
                </span>
              </div>

              <div className="flex justify-between items-center text-xs">
                <span className="text-[#9090AA]">Chance to Double Budget (&gt;2.5x):</span>
                <span className="font-mono font-bold text-[#E8B74A]">
                  {(prediction.financial_risk.prob_commercial_profit * 100).toFixed(0)}%
                </span>
              </div>

              <div className="flex justify-between items-center text-xs">
                <span className="text-[#9090AA]">Risk of Severe Box Office Loss:</span>
                <span className="font-mono font-bold text-rose-400">
                  {(prediction.financial_risk.prob_catastrophic_disaster * 100).toFixed(0)}%
                </span>
              </div>
            </div>

            <Link
              to="/simulate"
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-[#6C63FF]/20 hover:bg-[#6C63FF]/30 border border-[#6C63FF]/40 text-xs font-bold text-white transition-all cursor-pointer block text-center"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#E8B74A]" />
              <span>🧪 Run What-If Budget & Cast Simulator</span>
            </Link>
          </div>
        </div>
      )}

      {/* TreeSHAP Explainability Section */}
      {explanation && (
        <SHAPWaterfall
          baseRevenueUsd={explanation.base_value_usd}
          finalRevenueUsd={explanation.final_predicted_revenue_usd}
          positiveFactors={explanation.top_positive_factors}
          negativeFactors={explanation.top_negative_factors}
          additivityVerified={explanation.additivity_axiom_verified}
          additivityError={explanation.additivity_error}
          narrativeSummary={explanation.narrative_summary}
        />
      )}

      {/* Trade Comparables: Similar Historical Films */}
      {similarMovies.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Film className="w-5 h-5 text-[#E8B74A]" />
            <h3 className="text-base font-bold text-white tracking-wide">
              Similar Historical Movies (Box Office Benchmarks)
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {similarMovies.map((sim) => (
              <div
                key={sim.id}
                className="bg-[#15151E] rounded-xl p-4 border border-[#2A2A3A] space-y-2 hover:border-[#6C63FF]/50 transition-colors"
              >
                <div className="flex items-center justify-between text-xs text-[#9090AA]">
                  <span>{sim.release_year}</span>
                  <span className="font-mono text-emerald-400">
                    {(sim.similarity_score * 100).toFixed(0)}% match
                  </span>
                </div>

                <Link
                  to={`/movies/${sim.id}`}
                  className="font-bold text-sm text-white hover:text-[#E8B74A] line-clamp-1 block"
                >
                  {sim.primary_title}
                </Link>

                <p className="text-xs text-[#9090AA] truncate">{sim.director || 'Unknown'}</p>

                <div className="pt-2 border-t border-[#2A2A3A]/60 flex justify-between items-baseline">
                  <span className="text-[10px] text-[#9090AA] uppercase font-mono">Grossed</span>
                  <span className="font-mono font-bold text-white text-xs">
                    {formatCurrency(sim.gross_usd, currency)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Forecast Revisions Timeline */}
      {history.length > 0 && (
        <div className="glass-card rounded-2xl p-6 border border-[#2A2A3A] space-y-4">
          <div className="flex items-center gap-2 text-white font-bold text-sm">
            <History className="w-4 h-4 text-[#E8B74A]" />
            <span>Forecast Evolution & Revision History</span>
          </div>

          <div className="space-y-2.5">
            {history.map((h, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 rounded-xl bg-[#15151E] border border-[#2A2A3A]/60 text-xs"
              >
                <div className="space-y-0.5">
                  <span className="font-semibold text-white block">{h.lifecycle_stage}</span>
                  <span className="text-[11px] text-[#9090AA]">
                    {h.change_attribution || 'Routine calibration'}
                  </span>
                </div>
                <div className="text-right font-mono">
                  <span className="text-white font-bold block">{formatCurrency(h.expected_gross_usd, currency)}</span>
                  {h.delta_pct !== 0 && (
                    <span
                      className={`text-[10px] ${
                        h.delta_pct > 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {h.delta_pct > 0 ? `+${h.delta_pct}%` : `${h.delta_pct}%`}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
