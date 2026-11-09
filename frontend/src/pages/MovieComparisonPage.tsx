import React, { useState, useEffect } from 'react';
import { Columns3, Sparkles, TrendingUp, ShieldAlert, Film, Check, ArrowRight } from 'lucide-react';
import { apiService } from '../services/api';
import { UpcomingMovieItem, ActivePredictionResponse } from '../types';
import { useCurrency } from '../context/CurrencyContext';
import { formatCurrency, getRiskBadgeClass } from '../utils/format';
import { PredictionIntervalBar } from '../components/PredictionIntervalBar';

export const MovieComparisonPage: React.FC = () => {
  const { currency } = useCurrency();

  const [candidates, setCandidates] = useState<UpcomingMovieItem[]>([]);
  const [movieAId, setMovieAId] = useState<string>('');
  const [movieBId, setMovieBId] = useState<string>('');

  const [predA, setPredA] = useState<ActivePredictionResponse | null>(null);
  const [predB, setPredB] = useState<ActivePredictionResponse | null>(null);
  const [loadingA, setLoadingA] = useState(false);
  const [loadingB, setLoadingB] = useState(false);

  useEffect(() => {
    async function loadList() {
      try {
        const list = await apiService.getUpcomingMovies({ limit: 40 });
        setCandidates(list);
        if (list.length >= 2) {
          setMovieAId(list[0].id);
          setMovieBId(list[1].id);
        }
      } catch (err) {
        console.error('Failed to load upcoming candidates:', err);
      }
    }
    loadList();
  }, []);

  useEffect(() => {
    if (!movieAId) return;
    async function loadA() {
      try {
        setLoadingA(true);
        const p = await apiService.getMoviePrediction(movieAId);
        setPredA(p);
      } catch (err) {
        console.warn('Pred A failed:', err);
      } finally {
        setLoadingA(false);
      }
    }
    loadA();
  }, [movieAId]);

  useEffect(() => {
    if (!movieBId) return;
    async function loadB() {
      try {
        setLoadingB(true);
        const p = await apiService.getMoviePrediction(movieBId);
        setPredB(p);
      } catch (err) {
        console.warn('Pred B failed:', err);
      } finally {
        setLoadingB(false);
      }
    }
    loadB();
  }, [movieBId]);

  const movieA = candidates.find((m) => m.id === movieAId);
  const movieB = candidates.find((m) => m.id === movieBId);

  // Advantage Analysis
  const expA = predA ? predA.forecast.expected_gross_usd : (movieA?.expected_gross_usd || 0);
  const expB = predB ? predB.forecast.expected_gross_usd : (movieB?.expected_gross_usd || 0);
  const diffUsd = Math.abs(expA - expB);
  const leaderTitle = expA >= expB ? movieA?.primary_title : movieB?.primary_title;

  return (
    <div className="space-y-10 pb-20">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#6C63FF] uppercase tracking-wider mb-1">
          <Columns3 className="w-3.5 h-3.5" />
          <span>Theatrical Box-Office Face-Off</span>
        </div>
        <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
          Head-to-Head Movie Intelligence Comparison
        </h1>
        <p className="text-xs sm:text-sm text-[#9090AA] mt-1">
          Direct comparative analysis of projected revenues, conformal uncertainty intervals, capital risk, and talent equity.
        </p>
      </div>

      {/* Comparison Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Selector A */}
        <div className="glass-panel rounded-2xl p-4 border border-[#2A2A3A] space-y-2">
          <label className="text-xs font-bold text-[#E8B74A] uppercase font-mono">Contender A</label>
          <select
            value={movieAId}
            onChange={(e) => setMovieAId(e.target.value)}
            className="w-full bg-[#15151E] border border-[#2A2A3A] text-xs text-white rounded-xl p-3 focus:outline-none focus:border-[#E8B74A]"
          >
            {candidates.map((m) => (
              <option key={m.id} value={m.id}>
                {m.primary_title} ({m.industry} • {m.release_date})
              </option>
            ))}
          </select>
        </div>

        {/* Selector B */}
        <div className="glass-panel rounded-2xl p-4 border border-[#2A2A3A] space-y-2">
          <label className="text-xs font-bold text-[#6C63FF] uppercase font-mono">Contender B</label>
          <select
            value={movieBId}
            onChange={(e) => setMovieBId(e.target.value)}
            className="w-full bg-[#15151E] border border-[#2A2A3A] text-xs text-white rounded-xl p-3 focus:outline-none focus:border-[#6C63FF]"
          >
            {candidates.map((m) => (
              <option key={m.id} value={m.id}>
                {m.primary_title} ({m.industry} • {m.release_date})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Advantage Banner */}
      {movieA && movieB && (
        <div className="glass-card rounded-2xl p-6 border border-[#E8B74A]/40 flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="text-xs font-mono uppercase font-bold text-[#E8B74A] block mb-1">
              Comparative Revenue Edge
            </span>
            <p className="text-lg font-bold text-white">
              <span className="text-[#E8B74A]">{leaderTitle}</span> holds an estimated +{formatCurrency(diffUsd, currency)} ({Math.abs(((expA - expB) / Math.max(expB, 1)) * 100).toFixed(1)}%) theatrical advantage.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-[#9090AA]">
            <span>Model: CatBoost v1.0.0</span>
            <span>•</span>
            <span>80% Conformal Calibration</span>
          </div>
        </div>
      )}

      {/* Side by Side Dossier Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Card A */}
        {movieA && (
          <div className="glass-panel rounded-3xl p-6 border border-[#E8B74A]/30 space-y-6">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[10px] px-2.5 py-1 rounded bg-[#E8B74A]/15 text-[#E8B74A] font-bold font-mono">
                  Contender A • {movieA.industry}
                </span>
                <h3 className="text-2xl font-extrabold text-white mt-2">{movieA.primary_title}</h3>
                <p className="text-xs text-[#9090AA] mt-0.5">{movieA.director} • Starring {movieA.lead_actor}</p>
              </div>
              <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-[#1A1A26] border border-[#2A2A3A] text-white">
                PRS {movieA.readiness_score}
              </span>
            </div>

            <div className="bg-[#15151E] rounded-2xl p-4 border border-[#2A2A3A] space-y-1">
              <p className="text-[11px] text-[#9090AA] uppercase font-mono">Projected Worldwide Gross</p>
              <p className="text-2xl font-extrabold font-mono text-[#E8B74A]">
                {formatCurrency(expA, currency)}
              </p>
            </div>

            {/* Conformal Bar */}
            <PredictionIntervalBar
              expectedUsd={expA}
              pessimisticUsd={predA?.forecast.pessimistic_bound_80_usd || expA * 0.7}
              optimisticUsd={predA?.forecast.optimistic_bound_80_usd || expA * 1.45}
              compact={true}
            />

            {/* Metrics List */}
            <div className="space-y-3 pt-2 text-xs divide-y divide-[#2A2A3A]/60">
              <div className="flex justify-between pt-2">
                <span className="text-[#9090AA]">Reported Budget:</span>
                <span className="font-mono text-white font-bold">{formatCurrency(movieA.budget_usd, currency)}</span>
              </div>
              <div className="flex justify-between pt-2">
                <span className="text-[#9090AA]">Risk Rating:</span>
                <span className="font-mono text-zinc-300">{movieA.risk_assessment_tier}</span>
              </div>
              <div className="flex justify-between pt-2">
                <span className="text-[#9090AA]">Break-Even Probability:</span>
                <span className="font-mono text-emerald-400 font-bold">
                  {predA ? (predA.financial_risk.prob_break_even * 100).toFixed(0) : '75'}%
                </span>
              </div>
              <div className="flex justify-between pt-2">
                <span className="text-[#9090AA]">Digital Buzz Score:</span>
                <span className="font-mono text-[#E8B74A] font-bold">{movieA.buzz_score.toFixed(1)} / 100</span>
              </div>
            </div>
          </div>
        )}

        {/* Card B */}
        {movieB && (
          <div className="glass-panel rounded-3xl p-6 border border-[#6C63FF]/30 space-y-6">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[10px] px-2.5 py-1 rounded bg-[#6C63FF]/15 text-[#6C63FF] font-bold font-mono">
                  Contender B • {movieB.industry}
                </span>
                <h3 className="text-2xl font-extrabold text-white mt-2">{movieB.primary_title}</h3>
                <p className="text-xs text-[#9090AA] mt-0.5">{movieB.director} • Starring {movieB.lead_actor}</p>
              </div>
              <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-[#1A1A26] border border-[#2A2A3A] text-white">
                PRS {movieB.readiness_score}
              </span>
            </div>

            <div className="bg-[#15151E] rounded-2xl p-4 border border-[#2A2A3A] space-y-1">
              <p className="text-[11px] text-[#9090AA] uppercase font-mono">Projected Worldwide Gross</p>
              <p className="text-2xl font-extrabold font-mono text-[#6C63FF]">
                {formatCurrency(expB, currency)}
              </p>
            </div>

            {/* Conformal Bar */}
            <PredictionIntervalBar
              expectedUsd={expB}
              pessimisticUsd={predB?.forecast.pessimistic_bound_80_usd || expB * 0.7}
              optimisticUsd={predB?.forecast.optimistic_bound_80_usd || expB * 1.45}
              compact={true}
            />

            {/* Metrics List */}
            <div className="space-y-3 pt-2 text-xs divide-y divide-[#2A2A3A]/60">
              <div className="flex justify-between pt-2">
                <span className="text-[#9090AA]">Reported Budget:</span>
                <span className="font-mono text-white font-bold">{formatCurrency(movieB.budget_usd, currency)}</span>
              </div>
              <div className="flex justify-between pt-2">
                <span className="text-[#9090AA]">Risk Rating:</span>
                <span className="font-mono text-zinc-300">{movieB.risk_assessment_tier}</span>
              </div>
              <div className="flex justify-between pt-2">
                <span className="text-[#9090AA]">Break-Even Probability:</span>
                <span className="font-mono text-emerald-400 font-bold">
                  {predB ? (predB.financial_risk.prob_break_even * 100).toFixed(0) : '75'}%
                </span>
              </div>
              <div className="flex justify-between pt-2">
                <span className="text-[#9090AA]">Digital Buzz Score:</span>
                <span className="font-mono text-[#E8B74A] font-bold">{movieB.buzz_score.toFixed(1)} / 100</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

