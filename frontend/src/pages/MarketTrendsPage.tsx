import React, { useEffect, useState } from 'react';
import { TrendingUp, BarChart3, PieChart, Film, Globe } from 'lucide-react';
import { apiService } from '../services/api';
import { MarketTrendResponse } from '../types';
import { useCurrency } from '../context/CurrencyContext';
import { formatCurrency } from '../utils/format';

export const MarketTrendsPage: React.FC = () => {
  const { currency } = useCurrency();
  const [trends, setTrends] = useState<MarketTrendResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTrends() {
      try {
        setLoading(true);
        const data = await apiService.getMarketTrends();
        setTrends(data);
      } catch (err) {
        console.error('Failed to load market trends:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchTrends();
  }, []);

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3">
        <div className="w-10 h-10 border-4 border-[#6C63FF] border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-mono text-[#9090AA]">Aggregating Cross-Market Intelligence...</p>
      </div>
    );
  }

  if (!trends) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center text-[#9090AA]">
        <p>Market analytics currently unavailable.</p>
      </div>
    );
  }

  return (
    <div className="space-y-10 pb-20">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#6C63FF] uppercase tracking-wider mb-1">
          <Globe className="w-3.5 h-3.5" />
          <span>Cross-Industry Theatrical Dynamics</span>
        </div>
        <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
          Global Cinema Market Intelligence
        </h1>
        <p className="text-xs sm:text-sm text-[#9090AA] mt-1">
          Comparative empirical analysis across Hollywood, Bollywood, Tollywood, and Kollywood release universes.
        </p>
      </div>

      {/* Market Segments Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {trends.segments.map((seg) => (
          <div
            key={seg.segment_name}
            className="glass-card rounded-2xl p-6 border border-[#2A2A3A] space-y-4"
          >
            <div className="flex justify-between items-center">
              <span className="text-xs font-bold px-3 py-1 rounded-full bg-[#1A1A26] border border-[#2A2A3A] text-white">
                {seg.segment_name}
              </span>
              <span className="text-xs font-mono font-bold text-[#E8B74A]">
                {seg.market_share_pct.toFixed(1)}% Share
              </span>
            </div>

            <div>
              <p className="text-[11px] text-[#9090AA] uppercase font-mono">Total Box-Office Gross</p>
              <p className="text-xl font-extrabold font-mono text-white mt-0.5">
                {formatCurrency(seg.total_box_office_usd, currency)}
              </p>
            </div>

            <div className="space-y-2 pt-2 border-t border-[#2A2A3A]/60 text-xs">
              <div className="flex justify-between">
                <span className="text-[#9090AA]">Tracked Films:</span>
                <span className="font-mono text-white font-semibold">{seg.film_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#9090AA]">Commercial Hit Rate:</span>
                <span className="font-mono text-emerald-400 font-bold">{seg.hit_rate_pct}%</span>
              </div>
            </div>

            {/* Market Share Progress Bar */}
            <div className="h-1.5 w-full bg-[#15151E] rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[#6C63FF] to-[#E8B74A] rounded-full"
                style={{ width: `${Math.max(5, seg.market_share_pct)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

