import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { X, Lock, CheckCircle, AlertCircle } from 'lucide-react';

interface ChangePasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ChangePasswordModal: React.FC<ChangePasswordModalProps> = ({ isOpen, onClose }) => {
  const { changePassword } = useAuth();
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match.');
      return;
    }
    if (newPassword.length < 6) {
      setError('New password must be at least 6 characters long.');
      return;
    }

    setLoading(true);
    try {
      await changePassword(oldPassword, newPassword);
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setOldPassword('');
        setNewPassword('');
        setConfirmPassword('');
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to change password. Please check your current password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 border border-amber-200 text-amber-700 font-bold">
            <Lock className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">Change Password</h3>
            <p className="text-xs text-slate-500 font-medium">Update your account login credentials</p>
          </div>
        </div>

        {success ? (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <CheckCircle className="h-12 w-12 text-emerald-600 mb-2 animate-bounce" />
            <p className="text-sm font-semibold text-emerald-800">Password updated successfully!</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="flex items-center gap-2 rounded-lg bg-rose-50 border border-rose-200 p-3 text-xs text-rose-800">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Current Password</label>
              <input
                type="password"
                required
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:border-[#FFC20E] focus:outline-none focus:ring-1 focus:ring-[#FFC20E]"
                placeholder="••••••••"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">New Password (min 6 chars)</label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:border-[#FFC20E] focus:outline-none focus:ring-1 focus:ring-[#FFC20E]"
                placeholder="••••••••"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Confirm New Password</label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:border-[#FFC20E] focus:outline-none focus:ring-1 focus:ring-[#FFC20E]"
                placeholder="••••••••"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3">
              <button
                type="button"
                onClick={onClose}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:text-slate-900 shadow-xs transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex items-center gap-2 rounded-xl bg-[#FFC20E] hover:bg-[#e5ae0d] px-5 py-2 text-xs font-bold text-slate-950 disabled:opacity-50 shadow-xs transition-colors"
              >
                {loading ? 'Updating...' : 'Save Password'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
