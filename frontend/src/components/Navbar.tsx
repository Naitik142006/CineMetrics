import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Film,
  Search,
  Sliders,
  TrendingUp,
  Calendar,
  Sparkles,
  DollarSign,
  Activity,
  X,
  Columns3,
  LogOut,
  UserCheck,
  Compass,
} from 'lucide-react';
import { useCurrency } from '../context/CurrencyContext';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/api';
import { MovieSummary } from '../types';

export const Navbar: React.FC = () => {
  const { currency, toggleCurrency } = useCurrency();
  const { isAuthenticated, user, logout, openAuthModal } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Hide the application navbar on the standalone 3D landing page
  if (location.pathname === '/landing') {
    return null;
  }

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<MovieSummary[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Debounced search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await apiService.searchMovies({ q: searchQuery, limit: 6 });
        setSearchResults(res.movies || []);
        setShowDropdown(true);
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setIsSearching(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Click outside listener
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navLinks = [
    { name: 'Dashboard', path: '/', icon: Sparkles },
    { name: 'Upcoming Radar', path: '/upcoming', icon: Calendar },
    { name: 'What-If Simulator', path: '/simulate', icon: Sliders },
    { name: 'Compare', path: '/compare', icon: Columns3 },
    { name: 'Market Intelligence', path: '/market', icon: TrendingUp },
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-[#2A2A3A]/70 px-4 lg:px-8 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-3 group shrink-0">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#E8B74A] via-[#C49A32] to-[#6C63FF] p-[2px] transition-transform duration-300 group-hover:scale-105">
            <div className="w-full h-full bg-[#0A0A0F] rounded-[10px] flex items-center justify-center">
              <Film className="w-5 h-5 text-[#E8B74A] group-hover:rotate-6 transition-transform" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-xl tracking-tight text-white font-mono">
                Cine<span className="text-[#E8B74A]">Metrics</span>
              </span>
              <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-[#6C63FF]/20 text-[#6C63FF] border border-[#6C63FF]/30">
                AI
              </span>
            </div>
            <p className="text-[10px] text-[#9090AA] tracking-wider hidden sm:block">
              Box-Office Forecasting Engine
            </p>
          </div>
        </Link>

        {/* Global Search Bar */}
        <div ref={searchRef} className="relative flex-1 max-w-md hidden md:block">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9090AA]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
              placeholder="Search movies, directors, actors..."
              className="w-full bg-[#15151E] border border-[#2A2A3A] rounded-xl pl-10 pr-9 py-2 text-sm text-white placeholder-[#5A5A72] focus:outline-none focus:border-[#6C63FF] focus:ring-1 focus:ring-[#6C63FF] transition-all"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#5A5A72] hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Search Dropdown */}
          {showDropdown && searchResults.length > 0 && (
            <div className="absolute left-0 right-0 top-full mt-2 bg-[#1A1A26] border border-[#2A2A3A] rounded-xl shadow-2xl overflow-hidden z-50">
              <div className="p-2 divide-y divide-[#2A2A3A]/40">
                {searchResults.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => {
                      setShowDropdown(false);
                      setSearchQuery('');
                      navigate(`/movies/${m.id}`);
                    }}
                    className="w-full text-left px-3 py-2.5 rounded-lg hover:bg-[#111118] transition-colors flex items-center justify-between group"
                  >
                    <div>
                      <p className="text-sm font-semibold text-white group-hover:text-[#E8B74A] transition-colors">
                        {m.primary_title}
                      </p>
                      <p className="text-xs text-[#9090AA]">
                        {m.release_year} • {m.industry} • {m.director || 'Unknown Director'}
                      </p>
                    </div>
                    <span className="text-xs px-2 py-0.5 rounded bg-[#2A2A3A] text-[#9090AA]">
                      {m.is_released ? 'Released' : 'Upcoming'}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Navigation Links */}
        <nav className="flex items-center gap-1 sm:gap-2">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-[#6C63FF]/15 text-[#E8B74A] border border-[#6C63FF]/30'
                    : 'text-[#9090AA] hover:text-white hover:bg-[#1A1A26]'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-[#E8B74A]' : 'text-[#9090AA]'}`} />
                <span className="hidden xl:inline">{link.name}</span>
              </Link>
            );
          })}

          {/* Dual Currency Pill Toggle */}
          <button
            onClick={toggleCurrency}
            title="Toggle Currency Mode (USD vs INR)"
            className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-[#1A1A26] border border-[#2A2A3A] hover:border-[#E8B74A]/60 text-xs font-mono font-bold transition-all text-white ml-1 cursor-pointer"
          >
            <DollarSign className="w-3.5 h-3.5 text-[#E8B74A]" />
            <span className={currency === 'USD' ? 'text-[#E8B74A]' : 'text-[#9090AA]'}>USD</span>
            <span className="text-[#5A5A72]">/</span>
            <span className={currency === 'INR' ? 'text-[#E8B74A]' : 'text-[#9090AA]'}>INR</span>
          </button>

          {/* 3D Showcase Link */}
          <Link
            to="/landing"
            title="View 3D Animated Landing Showcase"
            className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-[#1A1A26] border border-[#2A2A3A] hover:border-[#6C63FF]/60 text-xs font-mono text-[#9090AA] hover:text-white transition-all ml-1"
          >
            <Compass className="w-3.5 h-3.5 text-[#6C63FF]" />
            <span className="hidden lg:inline">[Showcase]</span>
          </Link>

          {/* User Session / Sign Out Pill */}
          {isAuthenticated ? (
            <div className="flex items-center gap-2 ml-1">
              <div
                title={`Signed in as ${user?.name} (${user?.role})`}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-[#181824] border border-[#6C63FF]/40 text-xs font-mono text-zinc-200"
              >
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span className="hidden sm:inline font-semibold">{user?.avatarInitials || 'EX'}</span>
              </div>
              <button
                onClick={() => {
                  logout();
                  navigate('/landing');
                }}
                title="Sign Out"
                className="p-1.5 rounded-xl bg-[#1A1A26] border border-[#2A2A3A] hover:border-red-500/50 hover:text-red-400 text-[#9090AA] transition-all cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={openAuthModal}
              className="px-3 py-1.5 rounded-xl bg-[#6C63FF] hover:bg-[#574FCC] text-white text-xs font-semibold transition-all ml-1 cursor-pointer flex items-center gap-1"
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </button>
          )}
        </nav>
      </div>
    </header>
  );
};
