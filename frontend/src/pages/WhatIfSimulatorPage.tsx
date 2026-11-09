import React, { useState, useEffect } from 'react';
import { Sliders, Sparkles, TrendingUp, TrendingDown, ArrowRight, ShieldCheck } from 'lucide-react';
import { apiService } from '../services/api';
import { UpcomingMovieItem, WhatIfSimulationResponse } from '../types';
import { useCurrency } from '../context/CurrencyContext';
import { formatCurrency, getRiskBadgeClass } from '../utils/format';
import { PredictionIntervalBar } from '../components/PredictionIntervalBar';

export const WhatIfSimulatorPage: React.FC = () => {
  const { currency } = useCurrency();

  const [upcomingMovies, setUpcomingMovies] = useState<UpcomingMovieItem[]>([]);
  const [selectedMovieId, setSelectedMovieId] = useState<string>('');
  const [budgetUsd, setBudgetUsd] = useState<number>(50_000_000);
  const [director, setDirector] = useState<string>('');
  const [leadActor, setLeadActor] = useState<string>('');
  const [trailerViews, setTrailerViews] = useState<number>(15_000_000);
  const [sentimentPolarity, setSentimentPolarity] = useState<number>(0.6);

  const [simulationResult, setSimulationResult] = useState<WhatIfSimulationResponse | null>(null);
  const [simulating, setSimulating] = useState(false);

  useEffect(() => {
    async function loadCandidates() {
      try {
        const list = await apiService.getUpcomingMovies({ limit: 30 });
        setUpcomingMovies(list);
        if (list.length > 0) {
          const first = list[0];
          setSelectedMovieId(first.id);
          setBudgetUsd(first.budget_usd || 50_000_000);
          setDirector(first.director || '');
          setLeadActor(first.lead_actor || '');
        }
      } catch (err) {
        console.error('Failed to load upcoming candidates:', err);
      }
    }
    loadCandidates();
  }, []);

  const handleMovieChange = (movieId: string) => {
    setSelectedMovieId(movieId);
    const match = upcomingMovies.find((m) => m.id === movieId);
    if (match) {
      setBudgetUsd(match.budget_usd || 50_000_000);
      setDirector(match.director || '');
      setLeadActor(match.lead_actor || '');
    }
  };

  const handleRunSimulation = async () => {
    if (!selectedMovieId) return;

    try {
      setSimulating(true);
      const res = await apiService.simulateWhatIf({
        base_movie_id: selectedMovieId,
        budget_usd_override: budgetUsd,
        director_override: director || undefined,
        lead_actor_override: leadActor || undefined,
        simulated_trailer_views: trailerViews,
        simulated_sentiment_polarity: sentimentPolarity,
      });
      setSimulationResult(res);
    } catch (err) {
      console.error('Simulation failed:', err);
    } finally {
      setSimulating(false);
    }
  };

  const directorOptions = [
    'Christopher Nolan',
    'S.S. Rajamouli',
    'James Cameron',
    'Prashanth Neel',
    'Denis Villeneuve',
    'Siddharth Anand',
    'Rajkumar Hirani',
    'Lokesh Kanagaraj',
    'Atlee',
  ];

  const actorOptions = [
    'Shah Rukh Khan',
    'Prabhas',
    'Tom Cruise',
    'Leonardo DiCaprio',
    'Allu Arjun',
    'Ranbir Kapoor',
    'Ram Charan',
    'Jr NTR',
    'Hrithik Roshan',
  ];

  return (
    <div className="space-y-10 pb-20">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#E8B74A] uppercase tracking-wider mb-1">
          <Sparkles className="w-3.5 h-3.5" />
          <span>In-Memory Counterfactual Perturbation (&lt;50ms)</span>
        </div>
        <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
          Studio What-If Scenario Simulator
        </h1>
        <p className="text-xs sm:text-sm text-[#9090AA] mt-1">
          Stress-test production budgets, director changes, star power swaps, and digital viral campaigns before capital commitment.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Controls Column (5 cols) */}
        <div className="lg:col-span-5 glass-panel rounded-3xl p-6 border border-[#2A2A3A] space-y-6">
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-[#2A2A3A] pb-3">
            <Sliders className="w-4 h-4 text-[#6C63FF]" />
            <span>Simulation Parameters</span>
          </div>

          {/* Select Base Movie */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#9090AA]">Select Base Upcoming Release</label>
            <select
              value={selectedMovieId}
              onChange={(e) => handleMovieChange(e.target.value)}
              className="w-full bg-[#15151E] border border-[#2A2A3A] text-xs text-white rounded-xl p-3 focus:outline-none focus:border-[#6C63FF]"
            >
              {upcomingMovies.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.primary_title} ({m.industry} • {m.release_date})
                </option>
              ))}
            </select>
          </div>

          {/* Budget Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-[#9090AA]">Production Budget Override</span>
              <span className="font-mono font-bold text-[#E8B74A]">
                {formatCurrency(budgetUsd, currency)}
              </span>
            </div>
            <input
              type="range"
              min={5_000_000}
              max={300_000_000}
              step={5_000_000}
              value={budgetUsd}
              onChange={(e) => setBudgetUsd(Number(e.target.value))}
              className="w-full accent-[#E8B74A] cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-[#5A5A72] font-mono">
              <span>$5M</span>
              <span>$150M</span>
              <span>$300M</span>
            </div>
          </div>

          {/* Director Swap */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#9090AA]">Director Pedigree Swap</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={director}
                onChange={(e) => setDirector(e.target.value)}
                placeholder="Enter or choose director..."
                className="flex-1 bg-[#15151E] border border-[#2A2A3A] text-xs text-white rounded-xl px-3 py-2 focus:outline-none focus:border-[#6C63FF]"
              />
              <select
                onChange={(e) => e.target.value && setDirector(e.target.value)}
                className="bg-[#15151E] border border-[#2A2A3A] text-xs text-[#9090AA] rounded-xl px-2 focus:outline-none"
              >
                <option value="">Quick Pick</option>
                {directorOptions.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Lead Actor Swap */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#9090AA]">Lead Star Power Swap</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={leadActor}
                onChange={(e) => setLeadActor(e.target.value)}
                placeholder="Enter or choose actor..."
                className="flex-1 bg-[#15151E] border border-[#2A2A3A] text-xs text-white rounded-xl px-3 py-2 focus:outline-none focus:border-[#6C63FF]"
              />
              <select
                onChange={(e) => e.target.value && setLeadActor(e.target.value)}
                className="bg-[#15151E] border border-[#2A2A3A] text-xs text-[#9090AA] rounded-xl px-2 focus:outline-none"
              >
                <option value="">Quick Pick</option>
                {actorOptions.map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Simulated Trailer Views */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-[#9090AA]">Simulated 24h Trailer Views</span>
              <span className="font-mono font-bold text-white">
                {(trailerViews / 1_000_000).toFixed(1)}M Views
              </span>
            </div>
            <input
              type="range"
              min={1_000_000}
              max={80_000_000}
              step={1_000_000}
              value={trailerViews}
              onChange={(e) => setTrailerViews(Number(e.target.value))}
              className="w-full accent-[#6C63FF] cursor-pointer"
            />
          </div>

          {/* Sentiment Polarity */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-[#9090AA]">Audience Sentiment Polarity</span>
              <span className="font-mono font-bold text-emerald-400">
                {(sentimentPolarity * 100).toFixed(0)}% Positive
              </span>
            </div>
            <input
              type="range"
              min={-0.5}
              max={1.0}
              step={0.05}
              value={sentimentPolarity}
              onChange={(e) => setSentimentPolarity(Number(e.target.value))}
              className="w-full accent-emerald-400 cursor-pointer"
            />
          </div>

          {/* Run Button */}
          <button
            onClick={handleRunSimulation}
            disabled={simulating || !selectedMovieId}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-[#E8B74A] to-[#6C63FF] text-black font-extrabold text-sm hover:opacity-90 transition-opacity flex items-center justify-center gap-2 cursor-pointer shadow-[0_0_20px_rgba(232,183,74,0.3)] disabled:opacity-50"
          >
            {simulating ? (
              <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-black" />
                <span>Evaluate Counterfactual Scenario</span>
              </>
            )}
          </button>
        </div>

        {/* Results Column (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {!simulationResult ? (
            <div className="glass-panel rounded-3xl p-12 text-center text-[#9090AA] flex flex-col items-center justify-center min-h-[450px]">
              <Sliders className="w-12 h-12 text-[#5A5A72] mb-3 animate-pulse" />
              <p className="text-base font-semibold text-white mb-1">
                Awaiting Simulation Execution
              </p>
              <p className="text-xs max-w-sm">
                Adjust the parameters on the left and click "Evaluate Counterfactual Scenario" to calculate instantaneous revenue deltas.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Verdict Card */}
              <div className="glass-card rounded-2xl p-6 border border-[#E8B74A]/40 space-y-3 relative overflow-hidden">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase font-mono font-bold text-[#E8B74A]">
                    Executive Strategic Verdict
                  </span>
                  <span className="text-[11px] font-mono text-[#9090AA]">
                    Evaluated in {simulationResult.execution_latency_ms} ms
                  </span>
                </div>

                <p className="text-base sm:text-lg font-bold text-white">
                  {simulationResult.delta_analysis.strategic_verdict}
                </p>

                <div className="flex flex-wrap items-center gap-4 text-xs font-mono pt-2 border-t border-[#2A2A3A]/60">
                  <span className="text-[#9090AA]">
                    {simulationResult.delta_analysis.roi_impact}
                  </span>
                  <span>•</span>
                  <span className="text-amber-400">
                    Risk: {simulationResult.delta_analysis.risk_shift}
                  </span>
                </div>
              </div>

              {/* Side by Side Comparison Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                {/* Baseline Scenario */}
                <div className="glass-card rounded-2xl p-5 border border-[#2A2A3A] space-y-3">
                  <span className="text-[11px] px-2.5 py-0.5 rounded bg-[#15151E] text-[#9090AA] font-mono">
                    Baseline Production
                  </span>
                  <div>
                    <p className="text-xs text-[#9090AA]">Expected Gross</p>
                    <p className="text-2xl font-extrabold font-mono text-zinc-300">
                      {formatCurrency(simulationResult.baseline_scenario.expected_gross_usd, currency)}
                    </p>
                  </div>
                  <div className="space-y-1.5 pt-2 border-t border-[#2A2A3A]/60 text-xs">
                    <div className="flex justify-between">
                      <span className="text-[#9090AA]">P(Break-Even):</span>
                      <span className="font-mono text-white">
                        {(simulationResult.baseline_scenario.prob_break_even * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#9090AA]">Risk Rating:</span>
                      <span className="font-mono text-zinc-300">
                        {simulationResult.baseline_scenario.risk_assessment_tier}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Simulated Scenario */}
                <div className="glass-card rounded-2xl p-5 border border-[#6C63FF]/50 space-y-3 bg-[#1A1A26]/80">
                  <div className="flex justify-between items-center">
                    <span className="text-[11px] px-2.5 py-0.5 rounded bg-[#6C63FF]/20 text-[#6C63FF] font-mono font-bold">
                      Perturbed Scenario
                    </span>
                    <span
                      className={`text-xs font-mono font-bold ${
                        simulationResult.delta_analysis.percentage_change >= 0
                          ? 'text-emerald-400'
                          : 'text-rose-400'
                      }`}
                    >
                      {simulationResult.delta_analysis.percentage_change >= 0 ? '+' : ''}
                      {simulationResult.delta_analysis.percentage_change}%
                    </span>
                  </div>

                  <div>
                    <p className="text-xs text-[#E8B74A]">Projected Gross</p>
                    <p className="text-2xl font-extrabold font-mono text-[#E8B74A]">
                      {formatCurrency(simulationResult.simulated_scenario.expected_gross_usd, currency)}
                    </p>
                  </div>

                  <div className="space-y-1.5 pt-2 border-t border-[#2A2A3A]/60 text-xs">
                    <div className="flex justify-between">
                      <span className="text-[#9090AA]">P(Break-Even):</span>
                      <span className="font-mono text-emerald-400 font-bold">
                        {(simulationResult.simulated_scenario.prob_break_even * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#9090AA]">Risk Rating:</span>
                      <span className="font-mono text-[#E8B74A]">
                        {simulationResult.simulated_scenario.risk_assessment_tier}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Conformal Uncertainty Shift */}
              <PredictionIntervalBar
                expectedUsd={simulationResult.simulated_scenario.expected_gross_usd}
                pessimisticUsd={simulationResult.simulated_scenario.pessimistic_bound_80_usd}
                optimisticUsd={simulationResult.simulated_scenario.optimistic_bound_80_usd}
                confidenceLevel={0.8}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

