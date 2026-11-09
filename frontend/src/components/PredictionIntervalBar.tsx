import React from 'react';
import { useCurrency } from '../context/CurrencyContext';
import { formatCurrency } from '../utils/format';
import { ShieldCheck } from 'lucide-react';

interface PredictionIntervalBarProps {
  expectedUsd: number;
  pessimisticUsd: number;
  optimisticUsd: number;
  confidenceLevel?: number;
  compact?: boolean;
}

export const PredictionIntervalBar: React.FC<PredictionIntervalBarProps> = ({
  expectedUsd,
  pessimisticUsd,
  optimisticUsd,
  confidenceLevel = 0.8,
  compact = false,
}) => {
  const { currency } = useCurrency();

  // Normalized percentages for the bar visualization
  const minVal = Math.max(0, pessimisticUsd * 0.85);
  const maxVal = optimisticUsd * 1.15;
  const range = maxVal - minVal || 1.0;

  const pessPct = Math.max(0, Math.min(100, ((pessimisticUsd - minVal) / range) * 100));
  const expPct = Math.max(0, Math.min(100, ((expectedUsd - minVal) / range) * 100));
  const optPct = Math.max(0, Math.min(100, ((optimisticUsd - minVal) / range) * 100));
  const spanWidth = Math.max(5, optPct - pessPct);

  if (compact) {
    return (
      <div className="w-full space-y-1">
        <div className="flex justify-between text-[11px] text-[#9090AA] font-mono">
          <span>{formatCurrency(pessimisticUsd, currency)}</span>
          <span className="text-[#E8B74A] font-bold">{formatCurrency(expectedUsd, currency)}</span>
          <span>{formatCurrency(optimisticUsd, currency)}</span>
        </div>
        <div className="relative h-2 w-full bg-[#15151E] rounded-full overflow-hidden border border-[#2A2A3A]">
          {/* Conformal 80% Span */}
          <div
            className="absolute top-0 bottom-0 bg-gradient-to-r from-blue-500/40 via-[#6C63FF]/50 to-emerald-500/40 rounded-full"
            style={{ left: `${pessPct}%`, width: `${spanWidth}%` }}
          />
          {/* Expected Pin */}
          <div
            className="absolute top-0 bottom-0 w-1 bg-[#E8B74A] -ml-0.5 rounded-full shadow-[0_0_8px_#E8B74A]"
            style={{ left: `${expPct}%` }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card rounded-2xl p-5 border border-[#2A2A3A]">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-[#6C63FF]" />
          <h4 className="text-sm font-semibold text-white tracking-wide">
            Conformal Prediction Uncertainty Interval
          </h4>
        </div>
        <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#6C63FF]/15 text-[#6C63FF] border border-[#6C63FF]/30 font-mono font-medium">
          {Math.round(confidenceLevel * 100)}% Coverage Guarantee
        </span>
      </div>

      {/* Numerical Pillars */}
      <div className="grid grid-cols-3 gap-3 mb-6 text-center">
        <div className="bg-[#15151E] rounded-xl p-3 border border-[#2A2A3A]/60">
          <p className="text-[11px] text-[#9090AA] mb-0.5 uppercase tracking-wider">
            Pessimistic Bound (80%)
          </p>
          <p className="text-base sm:text-lg font-bold font-mono text-zinc-300">
            {formatCurrency(pessimisticUsd, currency)}
          </p>
        </div>

        <div className="bg-[#1A1A26] rounded-xl p-3 border border-[#E8B74A]/40 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-[#E8B74A] to-transparent" />
          <p className="text-[11px] text-[#E8B74A] mb-0.5 uppercase tracking-wider font-semibold">
            Expected Revenue
          </p>
          <p className="text-lg sm:text-xl font-extrabold font-mono text-[#E8B74A]">
            {formatCurrency(expectedUsd, currency)}
          </p>
        </div>

        <div className="bg-[#15151E] rounded-xl p-3 border border-[#2A2A3A]/60">
          <p className="text-[11px] text-[#9090AA] mb-0.5 uppercase tracking-wider">
            Optimistic Bound (80%)
          </p>
          <p className="text-base sm:text-lg font-bold font-mono text-emerald-400">
            {formatCurrency(optimisticUsd, currency)}
          </p>
        </div>
      </div>

      {/* Visual Interval Bar */}
      <div className="relative pt-6 pb-2">
        {/* Track */}
        <div className="h-3 w-full bg-[#15151E] rounded-full overflow-hidden border border-[#2A2A3A]">
          {/* Conformal Span */}
          <div
            className="absolute top-6 bottom-2 bg-gradient-to-r from-blue-500/40 via-[#6C63FF]/60 to-emerald-500/50 rounded-full border-t border-b border-[#6C63FF]/50"
            style={{ left: `${pessPct}%`, width: `${spanWidth}%` }}
          />
          {/* Expected Pin */}
          <div
            className="absolute top-5 bottom-1 w-1.5 bg-[#E8B74A] -ml-[3px] rounded-full shadow-[0_0_12px_#E8B74A]"
            style={{ left: `${expPct}%` }}
          />
        </div>

        {/* Labels below */}
        <div className="flex justify-between items-center text-[10px] text-[#5A5A72] mt-2 font-mono">
          <span>Worst-Case Floor</span>
          <span>Point Forecast (CatBoost)</span>
          <span>Bull-Case Ceiling</span>
        </div>
      </div>
    </div>
  );
};
