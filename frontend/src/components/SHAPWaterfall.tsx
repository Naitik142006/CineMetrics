import React, { useState } from 'react';
import { useCurrency } from '../context/CurrencyContext';
import { formatCurrency } from '../utils/format';
import { SHAPFactor } from '../types';
import { CheckCircle2, TrendingUp, TrendingDown, Sparkles, Brain, Code } from 'lucide-react';

interface SHAPWaterfallProps {
  baseRevenueUsd: number;
  finalRevenueUsd: number;
  positiveFactors: SHAPFactor[];
  negativeFactors: SHAPFactor[];
  additivityVerified: boolean;
  additivityError: number;
  narrativeSummary?: string;
}

// Friendly human translations for ML feature names
function humanizeFeatureLabel(label: string): string {
  const l = (label || '').toLowerCase();
  if (l.includes('lead actor') || l.includes('actor prior')) return 'Star Power & Lead Cast Appeal';
  if (l.includes('director') || l.includes('director prior')) return "Director's Proven Hit Track Record";
  if (l.includes('sequel') || l.includes('franchise')) return 'Established Franchise Equity & Fanbase';
  if (l.includes('buzz') || l.includes('trailer') || l.includes('view count')) return 'Viral Trailer Engagement & Social Buzz';
  if (l.includes('budget')) return 'Production Scale & Budget Size';
  if (l.includes('holiday') || l.includes('summer')) return 'Prime Festive / Holiday Release Corridor';
  if (l.includes('sentiment') || l.includes('polarity')) return 'Positive Audience Word-of-Mouth Sentiment';
  if (l.includes('studio')) return 'Major Studio Distribution Power';
  if (l.includes('runtime')) return 'Theatrical Runtime & Show Scheduling';
  if (l.includes('industry')) return 'Domestic & Global Market Demand';
  return label;
}

export const SHAPWaterfall: React.FC<SHAPWaterfallProps> = ({
  baseRevenueUsd,
  finalRevenueUsd,
  positiveFactors,
  negativeFactors,
  additivityVerified,
  additivityError,
  narrativeSummary,
}) => {
  const { currency } = useCurrency();
  const [viewMode, setViewMode] = useState<'simple' | 'technical'>('simple');

  const maxImpact = Math.max(
    1,
    ...positiveFactors.map((f) => Math.abs(f.shap_impact_usd)),
    ...negativeFactors.map((f) => Math.abs(f.shap_impact_usd))
  );

  return (
    <div className="glass-card rounded-2xl p-6 border border-[#2A2A3A] space-y-6">
      {/* Header with View Mode Toggle */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#2A2A3A]/60">
        <div className="flex items-center gap-2.5">
          <Brain className="w-5 h-5 text-[#E8B74A]" />
          <div>
            <h3 className="text-base font-bold text-white tracking-wide">
              {viewMode === 'simple'
                ? 'What Drives This Box Office Forecast?'
                : 'TreeSHAP Additive Feature Waterfall'}
            </h3>
            <p className="text-xs text-[#9090AA]">
              {viewMode === 'simple'
                ? 'Key factors boosting or limiting this film\'s predicted earnings.'
                : 'Exact marginal dollar contribution of each feature to the final forecast.'}
            </p>
          </div>
        </div>

        {/* View Switcher Pill */}
        <div className="flex items-center bg-[#15151E] p-1 rounded-xl border border-[#2A2A3A]">
          <button
            onClick={() => setViewMode('simple')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              viewMode === 'simple'
                ? 'bg-[#E8B74A] text-black font-bold shadow-sm'
                : 'text-[#9090AA] hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Simple View</span>
          </button>
          <button
            onClick={() => setViewMode('technical')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              viewMode === 'technical'
                ? 'bg-[#6C63FF] text-white font-bold shadow-sm'
                : 'text-[#9090AA] hover:text-white'
            }`}
          >
            <Code className="w-3.5 h-3.5" />
            <span>Data Science Mode</span>
          </button>
        </div>
      </div>

      {/* Comparison Cards: Baseline vs Final Prediction */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-[#15151E] rounded-xl p-4 border border-[#2A2A3A]/70 flex items-center justify-between">
          <div>
            <p className="text-xs text-[#9090AA] uppercase font-mono">
              {viewMode === 'simple' ? 'Average Theatrical Film Baseline' : 'Prior Base Expected Value E[y]'}
            </p>
            <p className="text-lg font-bold font-mono text-zinc-300 mt-0.5">
              {formatCurrency(baseRevenueUsd, currency)}
            </p>
            <p className="text-[10px] text-[#9090AA] mt-1">
              {viewMode === 'simple' ? 'Standard average across 10,000+ past movies' : 'Null model conditional expectation'}
            </p>
          </div>
          <span className="text-[11px] px-2.5 py-1 rounded-lg bg-[#2A2A3A] text-zinc-300 font-mono text-center">
            Benchmark
          </span>
        </div>

        <div className="bg-[#1A1A26] rounded-xl p-4 border border-[#E8B74A]/40 flex items-center justify-between relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-[#E8B74A] to-transparent" />
          <div>
            <p className="text-xs text-[#E8B74A] uppercase font-mono font-semibold">
              {viewMode === 'simple' ? 'Final Predicted Box Office' : 'Final Modeled Output (ŷ)'}
            </p>
            <p className="text-xl font-extrabold font-mono text-[#E8B74A] mt-0.5">
              {formatCurrency(finalRevenueUsd, currency)}
            </p>
            <p className="text-[10px] text-[#E8B74A]/80 mt-1">
              {viewMode === 'simple' ? 'After combining all stars, buzz & budget' : 'CatBoost regression output'}
            </p>
          </div>
          <span className="text-[11px] px-2.5 py-1 rounded-lg bg-[#E8B74A]/20 text-[#E8B74A] font-bold">
            Target
          </span>
        </div>
      </div>

      {/* Feature Contributions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Positive Drivers */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 uppercase tracking-wider">
            <TrendingUp className="w-4 h-4" />
            <span>
              {viewMode === 'simple'
                ? '🚀 What Boosts the Box Office (+)'
                : 'Top Value Drivers (Accelerators)'}
            </span>
          </div>
          <div className="space-y-2.5">
            {positiveFactors.map((factor, idx) => {
              const widthPct = Math.min(100, Math.max(10, (Math.abs(factor.shap_impact_usd) / maxImpact) * 100));
              const displayLabel =
                viewMode === 'simple'
                  ? humanizeFeatureLabel(factor.feature_label || factor.feature_name)
                  : factor.feature_label || factor.feature_name;

              return (
                <div key={idx} className="bg-[#15151E]/90 rounded-xl p-3 border border-[#2A2A3A]/60">
                  <div className="flex justify-between items-center text-xs mb-1.5">
                    <span className="text-zinc-200 font-medium truncate pr-2">
                      {displayLabel}
                    </span>
                    <span className="font-mono font-bold text-emerald-400 shrink-0">
                      +{formatCurrency(factor.shap_impact_usd, currency)}
                    </span>
                  </div>
                  <div className="h-2 w-full bg-[#0A0A0F] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full transition-all duration-500"
                      style={{ width: `${widthPct}%` }}
                    />
                  </div>
                  {viewMode === 'technical' && (
                    <div className="flex justify-between items-center text-[10px] text-[#5A5A72] font-mono mt-1">
                      <span>Feature: {factor.feature_name}</span>
                      <span>log10: +{factor.shap_value_log10.toFixed(4)}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Negative Drags */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-rose-400 uppercase tracking-wider">
            <TrendingDown className="w-4 h-4" />
            <span>
              {viewMode === 'simple'
                ? '⚠️ What Holds It Back / Drag (-)'
                : 'Downside Constraints (Drags)'}
            </span>
          </div>
          <div className="space-y-2.5">
            {negativeFactors.map((factor, idx) => {
              const widthPct = Math.min(100, Math.max(10, (Math.abs(factor.shap_impact_usd) / maxImpact) * 100));
              const displayLabel =
                viewMode === 'simple'
                  ? humanizeFeatureLabel(factor.feature_label || factor.feature_name)
                  : factor.feature_label || factor.feature_name;

              return (
                <div key={idx} className="bg-[#15151E]/90 rounded-xl p-3 border border-[#2A2A3A]/60">
                  <div className="flex justify-between items-center text-xs mb-1.5">
                    <span className="text-zinc-200 font-medium truncate pr-2">
                      {displayLabel}
                    </span>
                    <span className="font-mono font-bold text-rose-400 shrink-0">
                      -{formatCurrency(Math.abs(factor.shap_impact_usd), currency)}
                    </span>
                  </div>
                  <div className="h-2 w-full bg-[#0A0A0F] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-rose-600 to-rose-400 rounded-full transition-all duration-500"
                      style={{ width: `${widthPct}%` }}
                    />
                  </div>
                  {viewMode === 'technical' && (
                    <div className="flex justify-between items-center text-[10px] text-[#5A5A72] font-mono mt-1">
                      <span>Feature: {factor.feature_name}</span>
                      <span>log10: {factor.shap_value_log10.toFixed(4)}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Technical Mathematical Validation in Technical Mode */}
      {viewMode === 'technical' && additivityVerified && (
        <div className="flex items-center justify-between p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-xs font-mono text-emerald-400">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>SHAP Efficiency Axiom Satisfied: Exact Additivity Verified</span>
          </div>
          <span className="text-[#9090AA]">Machine Error: {additivityError.toExponential(1)}</span>
        </div>
      )}

      {/* Narrative Synthesis */}
      {narrativeSummary && (
        <div className="bg-[#111118] rounded-xl p-4 border border-[#2A2A3A] text-xs text-[#9090AA] leading-relaxed">
          <span className="font-semibold text-white block mb-1">💡 Key Takeaway:</span>
          {narrativeSummary}
        </div>
      )}
    </div>
  );
};
