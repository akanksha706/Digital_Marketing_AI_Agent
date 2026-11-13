import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../api/client';
import { Lock, Mail, ArrowRight, AlertCircle, KeyRound, X, CheckCircle2 } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Forgot Password Modal State
  const [forgotOpen, setForgotOpen] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotMessage, setForgotMessage] = useState<string | null>(null);
  const [forgotError, setForgotError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password. Please verify your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setForgotError(null);
    setForgotLoading(true);
    try {
      const res = await apiClient.post('/auth/forgot-password', {
        email: forgotEmail.trim(),
      });
      setForgotMessage(res.data?.message || 'Password reset instructions have been dispatched.');
    } catch (err: any) {
      setForgotError(err.response?.data?.detail || 'Failed to request password reset. Please try again.');
    } finally {
      setForgotLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-slate-50 px-4 py-12">
      {/* Subtle warm background elements */}
      <div className="absolute top-0 inset-x-0 h-96 bg-gradient-to-b from-[#FFC20E]/10 via-[#FFC20E]/5 to-transparent pointer-events-none" />

      <div className="relative w-full max-w-md">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex h-16 w-16 items-center justify-center p-1 mb-4">
            <img src="/42works_logo.png" alt="42 WORKS" className="h-full w-full object-contain drop-shadow-sm" />
          </div>
          <h1 className="text-2xl font-black tracking-tight text-slate-900">42 WORKS Studio</h1>
        </div>

        {/* Card */}
        <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-xl shadow-slate-200/50">
          {error && (
            <div className="mb-5 flex items-center gap-2.5 rounded-xl bg-rose-50 border border-rose-200 p-3.5 text-xs text-rose-700">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 pl-10 pr-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-[#FFC20E] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#FFC20E]/20 transition-all"
                  placeholder="name@company.com"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold text-slate-700">Password</label>
                <button
                  type="button"
                  onClick={() => {
                    setForgotEmail(email);
                    setForgotMessage(null);
                    setForgotError(null);
                    setForgotOpen(true);
                  }}
                  className="text-xs font-semibold text-amber-700 hover:text-amber-800 hover:underline transition-colors"
                >
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 pl-10 pr-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-[#FFC20E] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#FFC20E]/20 transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="pt-2 flex justify-center">
              <button
                type="submit"
                disabled={loading}
                className="flex items-center justify-center gap-2 rounded-xl bg-[#FFC20E] hover:bg-[#e6ad0a] px-8 py-2.5 text-xs font-bold text-slate-950 shadow-md shadow-[#FFC20E]/20 transition-all disabled:opacity-50 min-w-[150px]"
              >
                {loading ? (
                  <span>Signing in...</span>
                ) : (
                  <>
                    <span>Sign In</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        <p className="mt-6 text-center text-xs text-slate-500 font-medium">
          Copyright © 42Works Info Solutions Pvt Ltd 2026. All Rights Reserved.{' '}
          <a
            href="https://42works.net/privacy-policy/"
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-slate-700 hover:text-amber-600 underline decoration-slate-300 hover:decoration-amber-500 transition-colors ml-0.5"
          >
            Privacy Policy
          </a>
        </p>
      </div>

      {/* Forgot Password Modal */}
      {forgotOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="w-full max-w-sm rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-50 text-[#FFC20E] border border-amber-200/80">
                  <KeyRound className="h-4 w-4" />
                </div>
                <h3 className="text-sm font-bold text-slate-900">Reset Password</h3>
              </div>
              <button
                onClick={() => setForgotOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {forgotMessage ? (
              <div className="space-y-4">
                <div className="flex items-start gap-2.5 rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-xs text-emerald-800">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5" />
                  <p className="leading-relaxed">{forgotMessage}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setForgotOpen(false)}
                  className="w-full rounded-xl bg-[#FFC20E] hover:bg-[#e5ae0d] py-2 text-xs font-bold text-slate-950 transition-colors shadow-sm"
                >
                  Back to Sign In
                </button>
              </div>
            ) : (
              <form onSubmit={handleForgotSubmit} className="space-y-4">
                <p className="text-xs text-slate-500 leading-relaxed">
                  Enter your registered work email to receive password reset instructions.
                </p>

                {forgotError && (
                  <div className="flex items-center gap-2 rounded-xl bg-rose-50 border border-rose-200 p-3 text-xs text-rose-700">
                    <AlertCircle className="h-4 w-4 shrink-0 text-rose-500" />
                    <span>{forgotError}</span>
                  </div>
                )}

                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 mb-1">Email Address</label>
                  <input
                    type="email"
                    required
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-[#FFC20E] focus:outline-none focus:ring-1 focus:ring-[#FFC20E]"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setForgotOpen(false)}
                    className="rounded-xl px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={forgotLoading || !forgotEmail.trim()}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-[#FFC20E] hover:bg-[#e5ae0d] px-4 py-2 text-xs font-bold text-slate-950 shadow-sm disabled:opacity-50 transition-colors"
                  >
                    <KeyRound className="h-3.5 w-3.5" />
                    <span>{forgotLoading ? 'Sending...' : 'Send Reset Link'}</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
