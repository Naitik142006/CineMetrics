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
} from 'lucide-react';
import { apiService } from '../services/api';
import {
  MovieDetail,
  ActivePredictionResponse,
  SHAPWaterfallResponse,
  SimilarMovie,
} from '../types';
import { useCurrency } from '../context/CurrencyContext';
import { formatCurrency, getRiskBadgeClass, getSuccessCategoryBadge } from '../utils/format';
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

  return (
    <div className="space-y-10 pb-20">
      {/* Back button */}
      <Link
        to="/upcoming"
        className="inline-flex items-center gap-2 text-xs font-semibold text-[#9090AA] hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Upcoming Radar</span>
      </Link>

      {/* Dossier Header Banner */}
      <div className="relative glass-panel rounded-3xl p-6 lg:p-10 border border-[#2A2A3A] overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-[#E8B74A]/15 to-[#6C63FF]/20 blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-3 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-[#1A1A26] border border-[#2A2A3A] text-zinc-300">
                {movie.industry}
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
                <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-amber-950/60 border border-amber-500/40 text-amber-400">
                  PRS {prediction.readiness_score}/100 • {prediction.prediction_stage}
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
          <div className="bg-[#15151E] rounded-2xl p-5 border border-[#2A2A3A] min-w-[220px] text-right space-y-3">
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
                <span>Official Trailer</span>
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Conformal Prediction & Risk Pillars */}
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

            {/* Success Tier Probabilities */}
            <div className="glass-card rounded-2xl p-5 border border-[#2A2A3A]">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-semibold text-white tracking-wide">
                  7-Tier Commercial Success Probabilities
                </h4>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#E8B74A]/15 text-[#E8B74A] border border-[#E8B74A]/30 font-semibold">
                  Predicted: {prediction.success_classification.predicted_category}
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

          {/* Financial Downside Risk Profile (1 column) */}
          <div className="glass-card rounded-2xl p-6 border border-[#2A2A3A] space-y-5">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-400" />
              <h3 className="text-sm font-bold text-white tracking-wide">
                Financial Downside Risk
              </h3>
            </div>

            <div className={`rounded-xl p-4 border ${riskClass.bg} ${riskClass.border} space-y-1`}>
              <p className="text-[11px] text-[#9090AA] uppercase font-mono">Risk Rating</p>
              <p className={`text-base font-bold ${riskClass.text}`}>
                {prediction.financial_risk.risk_assessment_tier}
              </p>
              <p className="text-xs text-[#9090AA] pt-1">
                {prediction.financial_risk.break_even_status}
              </p>
            </div>

            <div className="space-y-3 pt-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-[#9090AA]">P(Break-Even Recovery):</span>
                <span className="font-mono font-bold text-emerald-400">
                  {(prediction.financial_risk.prob_break_even * 100).toFixed(0)}%
                </span>
              </div>

              <div className="flex justify-between items-center text-xs">
                <span className="text-[#9090AA]">P(Commercial Profit &gt;2.5x):</span>
                <span className="font-mono font-bold text-[#E8B74A]">
                  {(prediction.financial_risk.prob_commercial_profit * 100).toFixed(0)}%
                </span>
              </div>

              <div className="flex justify-between items-center text-xs">
                <span className="text-[#9090AA]">P(Catastrophic Disaster):</span>
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
              <span>Simulate Counterfactuals</span>
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

      {/* Structurally Similar Movies */}
      {similarMovies.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Film className="w-5 h-5 text-[#E8B74A]" />
            <h3 className="text-lg font-bold text-white">
              Structurally Comparable Historical Releases
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {similarMovies.map((sim) => (
              <div
                key={sim.id}
                className="bg-[#15151E] rounded-xl p-4 border border-[#2A2A3A] hover:border-[#6C63FF]/50 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-[10px] px-2 py-0.5 rounded bg-[#1A1A26] text-[#9090AA]">
                      {sim.release_year} • {sim.industry}
                    </span>
                    <span className="text-[10px] text-[#6C63FF] font-mono font-bold">
                      {Math.round(sim.similarity_score * 100)}% Match
                    </span>
                  </div>
                  <h4 className="font-bold text-sm text-white line-clamp-1">{sim.primary_title}</h4>
                  <p className="text-xs text-[#9090AA] mt-0.5 truncate">{sim.director}</p>
                </div>

                <div className="mt-4 pt-3 border-t border-[#2A2A3A]/60 flex justify-between items-baseline">
                  <span className="text-[10px] text-[#5A5A72] uppercase font-mono">Gross</span>
                  <span className="text-sm font-bold font-mono text-[#E8B74A]">
                    {formatCurrency(sim.gross_usd, currency)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Prediction Revision History Audit Trail */}
      {history.length > 0 && (
        <section className="glass-card rounded-2xl p-6 border border-[#2A2A3A] space-y-4">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-[#6C63FF]" />
            <h3 className="text-base font-bold text-white">
              Prediction Lifecycle Evolution & Revision Audit
            </h3>
          </div>

          <div className="divide-y divide-[#2A2A3A]/60">
            {history.map((h, idx) => (
              <div key={idx} className="py-3 flex flex-wrap items-center justify-between gap-3 text-xs">
                <div>
                  <span className="font-semibold text-white mr-2">{h.prediction_stage}</span>
                  <span className="text-[#9090AA]">{h.change_attribution}</span>
                </div>
                <div className="flex items-center gap-4 font-mono">
                  <span className="text-white">{formatCurrency(h.expected_gross_usd, currency)}</span>
                  {h.delta_pct !== 0 && (
                    <span
                      className={
                        h.delta_pct > 0 ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'
                      }
                    >
                      {h.delta_pct > 0 ? `+${h.delta_pct.toFixed(1)}%` : `${h.delta_pct.toFixed(1)}%`}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

