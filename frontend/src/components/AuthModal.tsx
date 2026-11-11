import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Film,
  Lock,
  Mail,
  User,
  ArrowRight,
  ShieldCheck,
  X,
  AlertCircle,
} from 'lucide-react';

export const AuthModal: React.FC = () => {
  const { showAuthModal, closeAuthModal, loginWithCredentials, registerAccount } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode] = useState<'signin' | 'register'>('signin');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!showAuthModal) return null;

  const switchMode = (nextMode: 'signin' | 'register') => {
    setMode(nextMode);
    setErrorMsg(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsSubmitting(true);

    try {
      if (mode === 'signin') {
        await loginWithCredentials(email, password);
      } else {
        await registerAccount(name, email, password);
      }
      setPassword('');
      navigate('/dashboard');
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail ||
        (err?.code === 'ERR_NETWORK'
          ? 'Cannot reach the CineMetrics server. Please ensure the backend is running.'
          : 'Authentication failed. Please check your details and try again.');
      setErrorMsg(typeof detail === 'string' ? detail : 'Invalid credentials or input format.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn"
      onClick={closeAuthModal}
    >
      <div
        className="relative w-full max-w-md bg-[#0F0F16] border border-[#2A2A3A] rounded-2xl shadow-2xl p-6 sm:p-8 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Subtle background glow */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-[#6C63FF]/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-[#E8B74A]/15 rounded-full blur-3xl pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={closeAuthModal}
          aria-label="Close Sign In Modal"
          className="absolute top-4 right-4 p-2 text-[#9090AA] hover:text-white rounded-lg hover:bg-[#1A1A26] transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#E8B74A] to-[#6C63FF] p-[2px]">
            <div className="w-full h-full bg-[#0F0F16] rounded-[10px] flex items-center justify-center">
              <Film className="w-5 h-5 text-[#E8B74A]" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-lg text-white font-mono">
                Cine<span className="text-[#E8B74A]">Metrics</span>
              </span>
              <span className="text-[9px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-[#6C63FF]/20 text-[#6C63FF] border border-[#6C63FF]/30">
                PRO // 2.0
              </span>
            </div>
            <p className="text-xs text-[#9090AA]">
              {mode === 'signin' ? 'Sign in to access the platform' : 'Create your CineMetrics account'}
            </p>
          </div>
        </div>

        {/* Mode Switcher: Sign In vs Create Account */}
        <div className="flex p-1 bg-[#15151E] rounded-xl border border-[#2A2A3A] mb-5">
          <button
            type="button"
            onClick={() => switchMode('signin')}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              mode === 'signin'
                ? 'bg-[#6C63FF] text-white shadow-md'
                : 'text-[#9090AA] hover:text-white'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => switchMode('register')}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              mode === 'register'
                ? 'bg-[#6C63FF] text-white shadow-md'
                : 'text-[#9090AA] hover:text-white'
            }`}
          >
            Create Account
          </button>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3 rounded-xl bg-red-950/50 border border-red-500/40 text-xs text-red-300 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <div>
              <label className="block text-xs font-medium text-[#9090AA] mb-1.5">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5A5A72]" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  minLength={2}
                  placeholder="Enter your name"
                  className="w-full bg-[#15151E] border border-[#2A2A3A] rounded-xl pl-9 pr-3 py-2 text-sm text-white placeholder-[#5A5A72] focus:outline-none focus:border-[#6C63FF]"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-[#9090AA] mb-1.5">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5A5A72]" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                autoComplete="email"
                className="w-full bg-[#15151E] border border-[#2A2A3A] rounded-xl pl-9 pr-3 py-2 text-sm text-white placeholder-[#5A5A72] focus:outline-none focus:border-[#6C63FF]"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-[#9090AA] mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5A5A72]" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={mode === 'register' ? 6 : 1}
                placeholder={mode === 'register' ? 'Minimum 6 characters' : 'Enter your password'}
                autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
                className="w-full bg-[#15151E] border border-[#2A2A3A] rounded-xl pl-9 pr-3 py-2 text-sm text-white placeholder-[#5A5A72] focus:outline-none focus:border-[#6C63FF]"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-[#6C63FF] to-[#574FCC] hover:from-[#7B73FF] hover:to-[#6C63FF] disabled:opacity-60 text-white font-semibold text-sm transition-all shadow-lg shadow-[#6C63FF]/25 flex items-center justify-center gap-2 cursor-pointer mt-2"
          >
            {isSubmitting ? (
              <span>{mode === 'signin' ? 'Signing In...' : 'Creating Account...'}</span>
            ) : (
              <>
                <span>{mode === 'signin' ? 'Sign In' : 'Create Account & Sign In'}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Security badge at bottom */}
        <div className="mt-6 pt-4 border-t border-[#2A2A3A]/60 flex items-center justify-between text-[11px] text-[#5A5A72]">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Encrypted PBKDF2 Session</span>
          </span>
          <span>CineMetrics v2.0</span>
        </div>
      </div>
    </div>
  );
};
