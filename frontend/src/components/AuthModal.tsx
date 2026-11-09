import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Film,
  Lock,
  Mail,
  ArrowRight,
  Sparkles,
  ShieldCheck,
  X,
  KeyRound,
  CheckCircle2,
} from 'lucide-react';

export const AuthModal: React.FC = () => {
  const { showAuthModal, closeAuthModal, login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('executive@cinemetrics.ai');
  const [password, setPassword] = useState('••••••••••••');
  const [activeTab, setActiveTab] = useState<'demo' | 'credentials'>('demo');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!showAuthModal) return null;

  const handleSignIn = (demoRole?: string) => {
    setIsSubmitting(true);
    setTimeout(() => {
      login(email, demoRole || 'Studio Executive');
      setIsSubmitting(false);
      navigate('/');
    }, 400);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
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
          className="absolute top-4 right-4 p-2 text-[#9090AA] hover:text-white rounded-lg hover:bg-[#1A1A26] transition-colors"
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
            <p className="text-xs text-[#9090AA]">Terminal Access Authorization</p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex p-1 bg-[#15151E] rounded-xl border border-[#2A2A3A] mb-6">
          <button
            onClick={() => setActiveTab('demo')}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              activeTab === 'demo'
                ? 'bg-[#6C63FF] text-white shadow-md'
                : 'text-[#9090AA] hover:text-white'
            }`}
          >
            ⚡ 1-Click Fast Access
          </button>
          <button
            onClick={() => setActiveTab('credentials')}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              activeTab === 'credentials'
                ? 'bg-[#6C63FF] text-white shadow-md'
                : 'text-[#9090AA] hover:text-white'
            }`}
          >
            🔑 Credentials Sign-In
          </button>
        </div>

        {/* Tab 1: Instant Demo Access */}
        {activeTab === 'demo' ? (
          <div className="space-y-4">
            <p className="text-xs text-[#9090AA] leading-relaxed">
              Select a pre-configured role to enter the CineMetrics intelligence suite with pre-loaded portfolio credentials:
            </p>

            <div className="space-y-2.5">
              <button
                onClick={() => handleSignIn('Studio Chief / Distribution Lead')}
                disabled={isSubmitting}
                className="w-full p-3 rounded-xl bg-[#1A1A26] border border-[#2A2A3A] hover:border-[#E8B74A]/70 text-left transition-all hover:bg-[#202030] group cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-[#E8B74A]" />
                    <span className="text-sm font-semibold text-white group-hover:text-[#E8B74A] transition-colors">
                      Studio Distribution Chief
                    </span>
                  </div>
                  <ArrowRight className="w-4 h-4 text-[#9090AA] group-hover:text-white group-hover:translate-x-1 transition-all" />
                </div>
                <p className="text-[11px] text-[#9090AA] mt-1 ml-4.5">
                  Full portfolio clearance • TreeSHAP access • Stage 4 pre-sales override
                </p>
              </button>

              <button
                onClick={() => handleSignIn('Senior Quantitative Film Analyst')}
                disabled={isSubmitting}
                className="w-full p-3 rounded-xl bg-[#1A1A26] border border-[#2A2A3A] hover:border-[#6C63FF]/70 text-left transition-all hover:bg-[#202030] group cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-[#6C63FF]" />
                    <span className="text-sm font-semibold text-white group-hover:text-[#6C63FF] transition-colors">
                      Quantitative Film Analyst
                    </span>
                  </div>
                  <ArrowRight className="w-4 h-4 text-[#9090AA] group-hover:text-white group-hover:translate-x-1 transition-all" />
                </div>
                <p className="text-[11px] text-[#9090AA] mt-1 ml-4.5">
                  Conformal risk engine • What-If simulator • Model benchmarking
                </p>
              </button>
            </div>
          </div>
        ) : (
          /* Tab 2: Standard Credentials */
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSignIn();
            }}
            className="space-y-4"
          >
            <div>
              <label className="block text-xs font-medium text-[#9090AA] mb-1.5">
                Studio Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5A5A72]" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="executive@studio.com"
                  className="w-full bg-[#15151E] border border-[#2A2A3A] rounded-xl pl-9 pr-3 py-2 text-sm text-white placeholder-[#5A5A72] focus:outline-none focus:border-[#6C63FF]"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[#9090AA] mb-1.5">
                Session Token / Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5A5A72]" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••••••"
                  className="w-full bg-[#15151E] border border-[#2A2A3A] rounded-xl pl-9 pr-3 py-2 text-sm text-white placeholder-[#5A5A72] focus:outline-none focus:border-[#6C63FF]"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-[#6C63FF] to-[#574FCC] hover:from-[#7B73FF] hover:to-[#6C63FF] text-white font-semibold text-sm transition-all shadow-lg shadow-[#6C63FF]/25 flex items-center justify-center gap-2 cursor-pointer mt-2"
            >
              {isSubmitting ? (
                <span>Authenticating Session...</span>
              ) : (
                <>
                  <span>Sign In to Terminal</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        )}

        {/* Security badge at bottom */}
        <div className="mt-6 pt-4 border-t border-[#2A2A3A]/60 flex items-center justify-between text-[11px] text-[#5A5A72]">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>SHA-256 Auth Active</span>
          </span>
          <span>CineMetrics v2.0-Production</span>
        </div>
      </div>
    </div>
  );
};

