import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  TrendingUp,
  ShieldAlert,
  Flame,
  ArrowRight,
  Database,
  Cpu,
  Layers,
  Zap,
  Film,
  Award,
} from 'lucide-react';
import { apiService } from '../services/api';
import { UpcomingDashboardResponse } from '../types';
import { MovieCard } from '../components/MovieCard';

export const DashboardPage: React.FC = () => {
  const [dashboard, setDashboard] = useState<UpcomingDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await apiService.getUpcomingDashboard();
        setDashboard(data);
      } catch (err: any) {
        console.error('Failed to load upcoming dashboard:', err);
        setError('Unable to connect to CineMetrics backend API. Please ensure the server is running.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3">
        <div className="w-10 h-10 border-4 border-[#6C63FF] border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-mono text-[#9090AA]">Loading Cinema Intelligence Dashboard...</p>
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="max-w-4xl mx-auto py-16 px-4 text-center">
        <div className="glass-card rounded-2xl p-8 border border-rose-500/30">
          <p className="text-rose-400 font-semibold mb-2">{error || 'Data unavailable'}</p>
          <p className="text-xs text-[#9090AA]">
            Ensure backend server is running on <code className="text-[#E8B74A]">http://localhost:8000</code>.
          </p>
        </div>
      </div>
    );
  }

  const { sections } = dashboard;
  const topGrossers = sections.top_predicted_grossers?.items || [];
  const viralLeaders = sections.highest_digital_buzz?.items || [];
  const highRisk = sections.high_risk_tentpoles?.items || [];
  const southTitans = sections.south_indian_powerhouses?.items || [];
  const bollywood = sections.bollywood_spotlight?.items || [];

  return (
    <div className="space-y-12 pb-16">
      {/* Hero Showcase Banner */}
      <section className="relative rounded-3xl overflow-hidden glass-panel border border-[#2A2A3A] p-8 lg:p-12">
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-[#6C63FF]/20 via-[#E8B74A]/10 to-transparent blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#E8B74A]/15 border border-[#E8B74A]/30 text-xs font-mono font-bold text-[#E8B74A]">
            <Sparkles className="w-3.5 h-3.5" />
            <span>2026–2027 Upcoming Theatrical Intelligence</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight">
            Predicting Box Office Hits & Blockbusters Before Release
          </h1>

          <p className="text-sm sm:text-base text-[#9090AA] leading-relaxed max-w-2xl">
            CineMetrics uses machine learning to forecast worldwide box office earnings for upcoming 2026–2027 movies. Discover projected revenues, best-case vs worst-case outcomes, and what drives success for every film—from Hollywood tentpoles to Pan-Indian spectacles.
          </p>

          <div className="flex flex-wrap gap-3 pt-2">
            <Link
              to="/upcoming"
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#E8B74A] to-[#C49A32] text-black font-bold text-sm hover:opacity-90 transition-opacity shadow-[0_0_20px_rgba(232,183,74,0.3)]"
            >
              <span>Explore 2026–2027 Radar</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              to="/simulate"
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#1A1A26] hover:bg-[#2A2A3A] border border-[#2A2A3A] text-white font-semibold text-sm transition-all"
            >
              <span>Launch Studio Simulator</span>
            </Link>
          </div>
        </div>

        {/* Engine KPI Stats Strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 pt-6 border-t border-[#2A2A3A]/60">
          <div className="flex items-center gap-3">
            <Database className="w-5 h-5 text-[#6C63FF]" />
            <div>
              <p className="text-[11px] text-[#9090AA] uppercase font-mono">Training Benchmark</p>
              <p className="text-lg font-bold text-white font-mono">10,800+ Past Films</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Film className="w-5 h-5 text-[#E8B74A]" />
            <div>
              <p className="text-[11px] text-[#9090AA] uppercase font-mono">Upcoming Tracked</p>
              <p className="text-lg font-bold text-[#E8B74A] font-mono">100+ 2026–2027 Titles</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Layers className="w-5 h-5 text-emerald-400" />
            <div>
              <p className="text-[11px] text-[#9090AA] uppercase font-mono">Uncertainty Coverage</p>
              <p className="text-lg font-bold text-emerald-400 font-mono">80% Range Guarantee</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Zap className="w-5 h-5 text-blue-400" />
            <div>
              <p className="text-[11px] text-[#9090AA] uppercase font-mono">Query Latency (p95)</p>
              <p className="text-lg font-bold text-blue-400 font-mono">&lt; 7.0 ms</p>
            </div>
          </div>
        </div>
      </section>

      {/* 3 Simple Steps Explainer Cards for General Users */}
      <section className="glass-card rounded-2xl p-6 border border-[#2A2A3A] space-y-4">
        <div className="flex items-center gap-2">
          <Award className="w-5 h-5 text-[#E8B74A]" />
          <h2 className="text-base font-bold text-white tracking-wide">
            How CineMetrics Predicts Box Office in 3 Simple Steps
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#15151E] rounded-xl p-4 border border-[#2A2A3A]/60 space-y-2">
            <div className="w-8 h-8 rounded-lg bg-[#E8B74A]/20 text-[#E8B74A] flex items-center justify-center font-bold text-sm">
              1
            </div>
            <h3 className="text-sm font-bold text-white">Multi-Signal Intelligence</h3>
            <p className="text-xs text-[#9090AA] leading-relaxed">
              We ingest confirmed production budgets, lead actor draw, director career hit rates, and real-time YouTube trailer views, likes, and comment sentiment.
            </p>
          </div>

          <div className="bg-[#15151E] rounded-xl p-4 border border-[#2A2A3A]/60 space-y-2">
            <div className="w-8 h-8 rounded-lg bg-[#6C63FF]/20 text-[#6C63FF] flex items-center justify-center font-bold text-sm">
              2
            </div>
            <h3 className="text-sm font-bold text-white">Realistic Box Office Range</h3>
            <p className="text-xs text-[#9090AA] leading-relaxed">
              Instead of a single misleading guess, the AI calculates a <strong className="text-zinc-200">Worst-Case Floor</strong>, <strong className="text-[#E8B74A]">Most Likely Gross</strong>, and <strong className="text-emerald-400">Best-Case Breakout</strong>.
            </p>
          </div>

          <div className="bg-[#15151E] rounded-xl p-4 border border-[#2A2A3A]/60 space-y-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-sm">
              3
            </div>
            <h3 className="text-sm font-bold text-white">Explainable Drivers</h3>
            <p className="text-xs text-[#9090AA] leading-relaxed">
              We show exactly what drives the prediction: which stars add value (+), how trailer buzz impacts opening momentum, and whether high production costs pose a risk (-).
            </p>
          </div>
        </div>
      </section>

      {/* Section 1: Projected Global Champions */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <TrendingUp className="w-5 h-5 text-[#E8B74A]" />
            <div>
              <h2 className="text-xl font-bold text-white tracking-wide">
                Projected 2026–2027 Box-Office Champions
              </h2>
              <p className="text-xs text-[#9090AA]">
                Upcoming marquee releases projected to command the highest worldwide theatrical revenues
              </p>
            </div>
          </div>
          <Link
            to="/upcoming?sort_by=forecast"
            className="text-xs text-[#6C63FF] hover:text-[#8B84FF] font-semibold flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {topGrossers.slice(0, 6).map((movie) => (
            <MovieCard key={movie.id} movie={movie} />
          ))}
        </div>
      </section>

      {/* Section 2: Digital Viral Velocity Leaders */}
      {viralLeaders.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Flame className="w-5 h-5 text-amber-500" />
              <div>
                <h2 className="text-xl font-bold text-white tracking-wide">
                  Most Hyped Releases (Highest Trailer Buzz)
                </h2>
                <p className="text-xs text-[#9090AA]">
                  Titles demonstrating maximum trailer velocity, like ratios, and positive audience buzz
                </p>
              </div>
            </div>
            <Link
              to="/upcoming?sort_by=buzz"
              className="text-xs text-[#6C63FF] hover:text-[#8B84FF] font-semibold flex items-center gap-1"
            >
              <span>View All</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {viralLeaders.slice(0, 6).map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>
        </section>
      )}

      {/* Section 3: South Indian Powerhouses */}
      {southTitans.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Sparkles className="w-5 h-5 text-[#E8B74A]" />
              <div>
                <h2 className="text-xl font-bold text-white tracking-wide">
                  South Indian Pan-India Titans
                </h2>
                <p className="text-xs text-[#9090AA]">
                  High-voltage releases from Tollywood (Telugu), Kollywood (Tamil), Sandalwood (Kannada), and Mollywood (Malayalam)
                </p>
              </div>
            </div>
            <Link
              to="/upcoming?market_segment=Tollywood"
              className="text-xs text-[#6C63FF] hover:text-[#8B84FF] font-semibold flex items-center gap-1"
            >
              <span>Explore South Radar</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {southTitans.slice(0, 6).map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>
        </section>
      )}

      {/* Section 4: Bollywood Spotlight */}
      {bollywood.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Film className="w-5 h-5 text-emerald-400" />
              <div>
                <h2 className="text-xl font-bold text-white tracking-wide">
                  Hindi Cinema Spotlight (Bollywood 2026–2027)
                </h2>
                <p className="text-xs text-[#9090AA]">
                  Upcoming marquee tentpoles and major franchise entries from Mumbai
                </p>
              </div>
            </div>
            <Link
              to="/upcoming?market_segment=Bollywood"
              className="text-xs text-[#6C63FF] hover:text-[#8B84FF] font-semibold flex items-center gap-1"
            >
              <span>Explore Bollywood Radar</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {bollywood.slice(0, 6).map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>
        </section>
      )}

      {/* Section 5: High Risk Downside Watch */}
      {highRisk.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <ShieldAlert className="w-5 h-5 text-rose-500" />
              <div>
                <h2 className="text-xl font-bold text-white tracking-wide">
                  High-Budget Downside Watch
                </h2>
                <p className="text-xs text-[#9090AA]">
                  Mega-budget investments requiring substantial box office multiples to recover production costs
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {highRisk.slice(0, 6).map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
};
