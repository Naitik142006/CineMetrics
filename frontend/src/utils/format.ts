import { CurrencyMode } from '../types';

export const DEFAULT_INR_RATE = 83.50;

export function formatCurrency(amountUsd: number, mode: CurrencyMode = 'USD'): string {
  if (amountUsd === undefined || amountUsd === null || isNaN(amountUsd)) {
    return mode === 'USD' ? '$0' : '₹0 Cr';
  }

  if (mode === 'INR') {
    const inrCrores = (amountUsd * DEFAULT_INR_RATE) / 10_000_000.0;
    if (inrCrores >= 10_000) {
      return `₹${(inrCrores / 1000).toFixed(1)}K Cr`;
    }
    return `₹${Math.round(inrCrores).toLocaleString('en-IN')} Cr`;
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

export function getPosterUrl(posterPath?: string | null): string | null {
  if (!posterPath || !posterPath.trim()) return null;
  const clean = posterPath.trim();
  const lower = clean.toLowerCase();
  if (lower === 'n/a' || lower === 'none' || lower === 'null' || lower === 'undefined') {
    return null;
  }
  if (clean.startsWith('http://') || clean.startsWith('https://')) {
    return clean;
  }
  const normalized = clean.startsWith('/') ? clean : `/${clean}`;
  return `https://image.tmdb.org/t/p/w500${normalized}`;
}

export function getDisplayYear(releaseYear?: number | null, releaseDate?: string | null): string {
  if (releaseDate) {
    const match = releaseDate.trim().match(/^((?:19|20)\d{2})\b/);
    if (match) {
      return match[1];
    }
  }
  if (releaseYear && releaseYear >= 1900 && releaseYear <= 2100) {
    return String(releaseYear);
  }
  return 'TBD';
}

const YOUTUBE_ID_RE = /^[A-Za-z0-9_-]{11}$/;

/**
 * Returns a safe YouTube watch URL only if trailerId is a valid 11-character YouTube video key.
 */
export function getYoutubeTrailerUrl(trailerId?: string | null): string | null {
  if (!trailerId) return null;
  const trimmed = trailerId.trim();
  if (trimmed.startsWith('Teaser_') || trimmed.startsWith('Trailer_')) return null;
  if (!YOUTUBE_ID_RE.test(trimmed)) return null;
  return `https://www.youtube.com/watch?v=${trimmed}`;
}


