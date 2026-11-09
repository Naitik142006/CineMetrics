import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { User, Award, ArrowLeft, Film, DollarSign } from 'lucide-react';
import { apiService } from '../services/api';
import { TalentDossierResponse } from '../types';
import { useCurrency } from '../context/CurrencyContext';
import { formatCurrency } from '../utils/format';

export const TalentDossierPage: React.FC = () => {
  const { role, name } = useParams<{ role: string; name: string }>();
  const { currency } = useCurrency();

  const [dossier, setDossier] = useState<TalentDossierResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!name) return;

    async function loadTalent() {
      try {
        setLoading(true);
        setError(null);
        const data =
          role === 'director'
            ? await apiService.getDirectorDossier(name!)
            : await apiService.getActorDossier(name!);
        setDossier(data);
      } catch (err: any) {
        console.error('Failed to load talent dossier:', err);
        setError(`No box-office track record found for ${role} '${name}'.`);
      } finally {
        setLoading(false);
      }
    }

    loadTalent();
  }, [role, name]);

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3">
        <div className="w-10 h-10 border-4 border-[#6C63FF] border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-mono text-[#9090AA]">Loading Talent Box-Office Track Record...</p>
      </div>
    );
  }

  if (error || !dossier) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-4">
        <div className="glass-card rounded-2xl p-8 border border-rose-500/30">
          <p className="text-rose-400 font-semibold mb-2">{error || 'Talent record not found'}</p>
          <Link to="/" className="text-xs text-[#6C63FF] hover:underline">
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10 pb-20">
      <Link
        to="/"
        className="inline-flex items-center gap-2 text-xs font-semibold text-[#9090AA] hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Dashboard</span>
      </Link>

      {/* Talent Header Banner */}
      <div className="glass-panel rounded-3xl p-8 border border-[#2A2A3A] relative overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-[#1A1A26] border border-[#2A2A3A] text-zinc-300">
                {dossier.role}
              </span>
              <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-[#E8B74A]/15 border border-[#E8B74A]/30 text-[#E8B74A]">
                {dossier.star_power_tier}
              </span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
              {dossier.person_name}
            </h1>

            <p className="text-xs text-[#9090AA] font-mono">
              Tracked across {dossier.total_films_tracked} canonical theatrical releases
            </p>
          </div>

          <div className="bg-[#15151E] rounded-2xl p-5 border border-[#2A2A3A] text-right space-y-1">
            <p className="text-[11px] text-[#9090AA] uppercase font-mono">Cumulative Career Gross</p>
            <p className="text-2xl font-extrabold font-mono text-[#E8B74A]">
              {formatCurrency(dossier.career_cumulative_gross_usd, currency)}
            </p>
          </div>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="glass-card rounded-2xl p-5 border border-[#2A2A3A] text-center">
          <p className="text-xs text-[#9090AA] uppercase font-mono mb-1">Average Gross Per Film</p>
          <p className="text-xl font-extrabold font-mono text-white">
            {formatCurrency(dossier.career_cumulative_gross_usd / Math.max(dossier.total_films_tracked, 1), currency)}
          </p>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-[#2A2A3A] text-center">
          <p className="text-xs text-[#9090AA] uppercase font-mono mb-1">Career Median ROI</p>
          <p className="text-xl font-extrabold font-mono text-emerald-400">
            {dossier.career_median_roi.toFixed(2)}x
          </p>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-[#2A2A3A] text-center">
          <p className="text-xs text-[#9090AA] uppercase font-mono mb-1">Commercial Hit Ratio</p>
          <p className="text-xl font-extrabold font-mono text-[#E8B74A]">
            {(dossier.commercial_hit_rate * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Filmography Highlights */}
      <div className="glass-card rounded-2xl p-6 border border-[#2A2A3A] space-y-4">
        <h3 className="text-base font-bold text-white">Filmography Box-Office Track Record</h3>
        <div className="divide-y divide-[#2A2A3A]/60">
          {dossier.filmography_highlights.map((film, idx) => (
            <div key={idx} className="py-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div>
                <span className="font-bold text-white text-sm block">{film.title}</span>
                <span className="text-[#9090AA]">{film.year} • Multiplier: {film.roi_multiplier}x</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-xs px-2.5 py-1 rounded bg-[#1A1A26] border border-[#2A2A3A] text-zinc-300">
                  {film.success_category}
                </span>
                <span className="font-mono font-bold text-white text-sm">
                  {formatCurrency(film.gross_usd, currency)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
