import { CurrencyMode } from '../types';

export const DEFAULT_INR_RATE = 83.50;

export function formatCurrency(amountUsd: number, mode: CurrencyMode = 'USD'): string {
  if (amountUsd === undefined || amountUsd === null || isNaN(amountUsd)) {
    return mode === 'USD' ? '$0' : '₹0 Cr';
  }

  if (mode === 'INR') {
    const inrCrores = (amountUsd * DEFAULT_INR_RATE) / 100_000_000.0;
    if (inrCrores >= 1000) {
      return `₹${(inrCrores / 1000).toFixed(2)}K Cr`;
    }
    return `₹${inrCrores.toLocaleString('en-IN', { maximumFractionDigits: 1 })} Cr`;
  }

  // USD Formatting
  if (amountUsd >= 1_000_000_000) {
    return `$${(amountUsd / 1_000_000_000).toFixed(2)}B`;
  }
  if (amountUsd >= 1_000_000) {
    return `$${(amountUsd / 1_000_000).toFixed(1)}M`;
  }
  if (amountUsd >= 1_000) {
    return `$${(amountUsd / 1_000).toFixed(0)}K`;
  }
  return `$${amountUsd.toFixed(0)}`;
}

export function getRiskBadgeClass(tier: string): { bg: string; text: string; border: string } {
  const lower = (tier || '').toLowerCase();
  if (lower.includes('low') || lower.includes('favorable') || lower.includes('safe')) {
    return {
      bg: 'bg-emerald-950/60',
      text: 'text-emerald-400',
      border: 'border-emerald-500/30',
    };
  }
  if (lower.includes('moderate') || lower.includes('medium')) {
    return {
      bg: 'bg-amber-950/60',
      text: 'text-amber-400',
      border: 'border-amber-500/30',
    };
  }
  if (lower.includes('high') || lower.includes('critical') || lower.includes('disaster')) {
    return {
      bg: 'bg-rose-950/60',
      text: 'text-rose-400',
      border: 'border-rose-500/30',
    };
  }
  return {
    bg: 'bg-indigo-950/60',
    text: 'text-indigo-400',
    border: 'border-indigo-500/30',
  };
}

export function getSuccessCategoryBadge(cat: string): { bg: string; text: string; border: string } {
  switch (cat) {
    case 'Blockbuster':
      return { bg: 'bg-amber-500/20', text: 'text-amber-300', border: 'border-amber-400/40' };
    case 'Super Hit':
      return { bg: 'bg-emerald-500/20', text: 'text-emerald-300', border: 'border-emerald-400/40' };
    case 'Hit':
      return { bg: 'bg-teal-500/20', text: 'text-teal-300', border: 'border-teal-400/40' };
    case 'Average':
      return { bg: 'bg-blue-500/20', text: 'text-blue-300', border: 'border-blue-400/40' };
    case 'Below Average':
      return { bg: 'bg-yellow-500/20', text: 'text-yellow-300', border: 'border-yellow-400/40' };
    case 'Flop':
      return { bg: 'bg-orange-500/20', text: 'text-orange-300', border: 'border-orange-400/40' };
    case 'Disaster':
      return { bg: 'bg-red-500/20', text: 'text-red-300', border: 'border-red-400/40' };
    default:
      return { bg: 'bg-zinc-800', text: 'text-zinc-300', border: 'border-zinc-700' };
  }
}

