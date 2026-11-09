import React from 'react';
import { useCurrency } from '../context/CurrencyContext';
import { formatCurrency } from '../utils/format';
import { ShieldCheck, Info } from 'lucide-react';

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
      <div className="w-full space-y-1.5">
        <div className="flex justify-between items-center text-[11px] font-mono">
          <span className="text-rose-400/90 font-medium" title="Worst-Case Floor">
            <span className="text-[9px] uppercase tracking-wider text-[#9090AA] block">Floor</span>
            {formatCurrency(pessimisticUsd, currency)}
          </span>
          <span className="text-[#E8B74A] font-extrabold text-xs text-center" title="Most Likely Target">
            <span className="text-[9px] uppercase tracking-wider text-[#E8B74A]/80 block">Most Likely</span>
            {formatCurrency(expectedUsd, currency)}
          </span>
          <span className="text-emerald-400/90 font-medium text-right" title="Best-Case Ceiling">
            <span className="text-[9px] uppercase tracking-wider text-[#9090AA] block">Ceiling</span>
            {formatCurrency(optimisticUsd, currency)}
          </span>
        </div>
        <div className="relative h-2 w-full bg-[#15151E] rounded-full overflow-hidden border border-[#2A2A3A]">
          {/* Conformal 80% Span */}
          <div
            className="absolute top-0 bottom-0 bg-gradient-to-r from-rose-500/30 via-[#E8B74A]/40 to-emerald-500/40 rounded-full"
            style={{ left: `${pessPct}%`, width: `${spanWidth}%` }}
          />
          {/* Expected Pin */}
          <div
            className="absolute top-0 bottom-0 w-1.5 bg-[#E8B74A] -ml-[3px] rounded-full shadow-[0_0_8px_#E8B74A]"
            style={{ left: `${expPct}%` }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card rounded-2xl p-6 border border-[#2A2A3A] space-y-5">
      {/* Header with Plain-English Explanation */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#2A2A3A]/60">
        <div className="flex items-center gap-2.5">
          <ShieldCheck className="w-5 h-5 text-[#E8B74A]" />
          <div>
            <h4 className="text-base font-bold text-white tracking-wide">
              Predicted Box Office Range (Best vs Worst Case)
            </h4>
            <p className="text-xs text-[#9090AA] mt-0.5">
              8 out of 10 times, the film's final gross will land inside this predicted corridor.
            </p>
          </div>
        </div>
        <span className="text-xs px-3 py-1 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-500/40 font-semibold font-mono">
          {Math.round(confidenceLevel * 100)}% Statistical Likelihood
        </span>
      </div>

      {/* 3 Pillars: Conservative Floor, Most Likely Target, Breakout Potential */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 text-center">
        {/* Conservative Floor */}
        <div className="bg-[#15151E] rounded-xl p-3.5 border border-rose-500/30 relative">
          <div className="flex items-center justify-center gap-1 text-[11px] text-rose-400 mb-1 font-semibold uppercase tracking-wider">
            <span className="w-2 h-2 rounded-full bg-rose-400" />
            <span>Worst-Case Floor</span>
          </div>
          <p className="text-lg sm:text-xl font-bold font-mono text-zinc-200">
            {formatCurrency(pessimisticUsd, currency)}
          </p>
          <p className="text-[10px] text-[#9090AA] mt-1">If reviews or word-of-mouth are cold</p>
        </div>

        {/* Most Likely Target */}
        <div className="bg-[#1A1A26] rounded-xl p-3.5 border border-[#E8B74A]/50 relative overflow-hidden shadow-[0_0_15px_rgba(232,183,74,0.1)]">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-[#E8B74A] to-transparent" />
          <div className="flex items-center justify-center gap-1 text-[11px] text-[#E8B74A] mb-1 font-bold uppercase tracking-wider">
            <span className="w-2 h-2 rounded-full bg-[#E8B74A] animate-pulse" />
            <span>Most Likely Gross</span>
          </div>
          <p className="text-xl sm:text-2xl font-extrabold font-mono text-[#E8B74A]">
            {formatCurrency(expectedUsd, currency)}
          </p>
          <p className="text-[10px] text-[#E8B74A]/80 mt-1 font-medium">Central AI forecast based on all signals</p>
        </div>

        {/* Breakout Ceiling */}
        <div className="bg-[#15151E] rounded-xl p-3.5 border border-emerald-500/30 relative">
          <div className="flex items-center justify-center gap-1 text-[11px] text-emerald-400 mb-1 font-semibold uppercase tracking-wider">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Best-Case Potential</span>
          </div>
          <p className="text-lg sm:text-xl font-bold font-mono text-emerald-400">
            {formatCurrency(optimisticUsd, currency)}
          </p>
          <p className="text-[10px] text-[#9090AA] mt-1">If viral audience hype explodes</p>
        </div>
      </div>

      {/* Visual Interval Bar */}
      <div className="pt-2">
        <div className="relative h-3.5 w-full bg-[#15151E] rounded-full overflow-hidden border border-[#2A2A3A]">
          {/* Conformal Span */}
          <div
            className="absolute top-0 bottom-0 bg-gradient-to-r from-rose-500/40 via-[#E8B74A]/50 to-emerald-500/50 rounded-full"
            style={{ left: `${pessPct}%`, width: `${spanWidth}%` }}
          />
          {/* Expected Pin */}
          <div
            className="absolute top-0 bottom-0 w-2 bg-[#E8B74A] -ml-1 rounded-full shadow-[0_0_10px_#E8B74A]"
            style={{ left: `${expPct}%` }}
          />
        </div>

        {/* Labels below */}
        <div className="flex justify-between items-center text-[11px] text-[#9090AA] mt-2 font-mono">
          <span className="text-rose-400">🔴 Floor: {formatCurrency(pessimisticUsd, currency)}</span>
          <span className="text-[#E8B74A] font-bold">🟡 Target: {formatCurrency(expectedUsd, currency)}</span>
          <span className="text-emerald-400">🟢 Ceiling: {formatCurrency(optimisticUsd, currency)}</span>
        </div>
      </div>
    </div>
  );
};
