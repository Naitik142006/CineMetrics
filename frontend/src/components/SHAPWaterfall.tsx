import React from 'react';
import { useCurrency } from '../context/CurrencyContext';
import { formatCurrency } from '../utils/format';
import { SHAPFactor } from '../types';
import { CheckCircle2, TrendingUp, TrendingDown, Layers } from 'lucide-react';

interface SHAPWaterfallProps {
  baseRevenueUsd: number;
  finalRevenueUsd: number;
  positiveFactors: SHAPFactor[];
  negativeFactors: SHAPFactor[];
  additivityVerified: boolean;
  additivityError: number;
  narrativeSummary?: string;
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

  const maxImpact = Math.max(
    1,
    ...positiveFactors.map((f) => Math.abs(f.shap_impact_usd)),
    ...negativeFactors.map((f) => Math.abs(f.shap_impact_usd))
  );

  return (
    <div className="glass-card rounded-2xl p-6 border border-[#2A2A3A]">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6 pb-4 border-b border-[#2A2A3A]/60">
        <div className="flex items-center gap-2.5">
          <Layers className="w-5 h-5 text-[#E8B74A]" />
          <div>
            <h3 className="text-base font-bold text-white tracking-wide">
              TreeSHAP Additive Feature Waterfall
            </h3>
            <p className="text-xs text-[#9090AA]">
              Exact marginal dollar contribution of each feature to the final forecast
            </p>
          </div>
        </div>

        {additivityVerified && (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/40 text-[11px] text-emerald-400 font-mono">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Additivity Verified (Err: {additivityError.toExponential(1)})</span>
          </div>
        )}
      </div>

      {/* Base vs Final Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <div className="bg-[#15151E] rounded-xl p-4 border border-[#2A2A3A]/70 flex items-center justify-between">
          <div>
            <p className="text-xs text-[#9090AA] uppercase font-mono">Prior Base Expected Value (E[y])</p>
            <p className="text-lg font-bold font-mono text-zinc-300">
              {formatCurrency(baseRevenueUsd, currency)}
            </p>
          </div>
          <span className="text-[11px] px-2 py-0.5 rounded bg-[#2A2A3A] text-[#9090AA]">
            Dataset Prior
          </span>
        </div>

        <div className="bg-[#1A1A26] rounded-xl p-4 border border-[#E8B74A]/40 flex items-center justify-between relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-[#E8B74A] to-transparent" />
          <div>
            <p className="text-xs text-[#E8B74A] uppercase font-mono font-semibold">Final Modeled Output (ŷ)</p>
            <p className="text-xl font-extrabold font-mono text-[#E8B74A]">
              {formatCurrency(finalRevenueUsd, currency)}
            </p>
          </div>
          <span className="text-[11px] px-2 py-0.5 rounded bg-[#E8B74A]/20 text-[#E8B74A] font-bold">
            CatBoost v1
          </span>
        </div>
      </div>

      {/* Feature Contributions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Positive Drivers */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 uppercase tracking-wider">
            <TrendingUp className="w-4 h-4" />
            <span>Top Value Drivers (Accelerators)</span>
          </div>
          <div className="space-y-2.5">
            {positiveFactors.map((factor, idx) => {
              const widthPct = Math.min(100, Math.max(10, (Math.abs(factor.shap_impact_usd) / maxImpact) * 100));
              return (
                <div key={idx} className="bg-[#15151E]/90 rounded-xl p-3 border border-[#2A2A3A]/60">
                  <div className="flex justify-between items-center text-xs mb-1.5">
                    <span className="text-zinc-200 font-medium truncate pr-2">
                      {factor.feature_label}
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
                </div>
              );
            })}
          </div>
        </div>

        {/* Negative Drags */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-rose-400 uppercase tracking-wider">
            <TrendingDown className="w-4 h-4" />
            <span>Downside Constraints (Drags)</span>
          </div>
          <div className="space-y-2.5">
            {negativeFactors.map((factor, idx) => {
              const widthPct = Math.min(100, Math.max(10, (Math.abs(factor.shap_impact_usd) / maxImpact) * 100));
              return (
                <div key={idx} className="bg-[#15151E]/90 rounded-xl p-3 border border-[#2A2A3A]/60">
                  <div className="flex justify-between items-center text-xs mb-1.5">
                    <span className="text-zinc-200 font-medium truncate pr-2">
                      {factor.feature_label}
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
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Narrative Synthesis */}
      {narrativeSummary && (
        <div className="bg-[#111118] rounded-xl p-4 border border-[#2A2A3A] text-xs text-[#9090AA] leading-relaxed">
          <span className="font-semibold text-white block mb-1">Executive Attribution Summary:</span>
          {narrativeSummary}
        </div>
      )}
    </div>
  );
};
