import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from '../api/client';
import gsap from 'gsap';
import type { User, Brand, KnowledgeSummary, UserRole, GlobalAnalyticsSummary } from '../types';
import { useAuth } from '../context/AuthContext';
import {
  Shield,
  UserPlus,
  Users,
  Brain,
  CheckCircle,
  AlertCircle,
  BarChart3,
  Archive,
  TrendingUp,
  Clock,
  Sparkles,
  Trash2,
  Power,
  RefreshCw,
  Search,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';

export const AdminPage: React.FC = () => {
  const { user: currentUser } = useAuth();

  // Core Data States
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [userSearchQuery, setUserSearchQuery] = useState('');
  const [showAddUserModal, setShowAddUserModal] = useState(false);

  // Scalable Member Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const usersPerPage = 5;

  const [brand, setBrand] = useState<Brand | null>(null);
  const [knowledge, setKnowledge] = useState<KnowledgeSummary | null>(null);
  const [analytics, setAnalytics] = useState<GlobalAnalyticsSummary | null>(null);
  const [analyticsTimeframe, setAnalyticsTimeframe] = useState<'week' | 'month' | 'year' | 'all'>('month');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [syncFeedback, setSyncFeedback] = useState<string | null>(null);

  // New User Form State (Only 2 Roles: Creator or Administrator)
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState<UserRole>('member');
  const [userLoading, setUserLoading] = useState(false);
  const [userSuccess, setUserSuccess] = useState<string | null>(null);
  const [userError, setUserError] = useState<string | null>(null);

  // User Actions State
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);

  const analyticsSectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (analytics && analyticsSectionRef.current) {
      const cards = analyticsSectionRef.current.querySelectorAll('.kpi-card');
      if (cards.length > 0) {
        gsap.fromTo(
          cards,
          { opacity: 0, y: 14, scale: 0.98 },
          { opacity: 1, y: 0, scale: 1, duration: 0.35, stagger: 0.05, ease: 'power2.out' }
        );
      }
    }
  }, [analytics, analyticsTimeframe]);

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    setIsRefreshing(true);
    try {
      const [usersRes, brandRes, kgRes, analyticsRes] = await Promise.all([
        apiClient.get<User[]>('/admin/users').catch(() => ({ data: [] })),
        apiClient.get<Brand[]>('/admin/brands').then((r) => r.data[0] || null).catch(() => null),
        apiClient.get<KnowledgeSummary>('/admin/knowledge-graph/1').catch(() => null),
        apiClient.get<GlobalAnalyticsSummary>(`/admin/creator-analytics?timeframe=${analyticsTimeframe}`).catch(() => null),
      ]);

      if (usersRes.data) {
        setUsers(usersRes.data);
        if (usersRes.data.length > 0 && selectedUserId === null) {
          setSelectedUserId(usersRes.data[0].id);
        }
      }
      if (brandRes) {
        setBrand(brandRes);
      }
      if (kgRes && kgRes.data) {
        setKnowledge(kgRes.data);
      }
      if (analyticsRes && analyticsRes.data) {
        setAnalytics(analyticsRes.data);
      }
    } catch {
      // Fallback
    } finally {
      setIsRefreshing(false);
    }
  };

  // Explicit Timeframe Switcher
  const handleTimeframeChange = async (tf: 'week' | 'month' | 'year' | 'all') => {
    setAnalyticsTimeframe(tf);
    try {
      const res = await apiClient.get<GlobalAnalyticsSummary>(`/admin/creator-analytics?timeframe=${tf}`);
      if (res.data) {
        setAnalytics(res.data);
      }
    } catch {
      // Fallback
    }
  };

  const getTimelineTitle = () => {
    switch (analyticsTimeframe) {
      case 'week':
        return "This Week's Daily Output";
      case 'month':
        return "This Month's Weekly Breakdown";
      case 'year':
        return "This Year's Monthly Breakdown";
      case 'all':
        return 'All-Time Annual Activity';
    }
  };

  const getTimelineGridClass = (pointCount: number) => {
    if (analyticsTimeframe === 'week') return 'grid-cols-7';
    if (analyticsTimeframe === 'month') return pointCount === 5 ? 'grid-cols-5' : 'grid-cols-4';
    if (analyticsTimeframe === 'year') return 'grid-cols-6 sm:grid-cols-12';
    return 'grid-cols-4';
  };

  // Explicit Sync Handler with Clear Visual Status Feedback
  const handleSyncWorkspace = async () => {
    setIsRefreshing(true);
    setSyncFeedback(null);
    try {
      await fetchAdminData();
      const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setSyncFeedback(`Workspace synchronized at ${nowStr}. All creator counts & brand settings are up to date.`);
      setTimeout(() => setSyncFeedback(null), 5000);
    } catch {
      setSyncFeedback('Unable to sync with server. Please verify backend connection.');
      setTimeout(() => setSyncFeedback(null), 5000);
    } finally {
      setIsRefreshing(false);
    }
  };

  // 1. Handle Create User
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setUserError(null);
    setUserSuccess(null);

    if (newPassword.length < 6) {
      setUserError('Password must be at least 6 characters long.');
      return;
    }

    setUserLoading(true);

    try {
      const res = await apiClient.post<User>('/admin/users', {
        email: newEmail.trim().toLowerCase(),
        password: newPassword,
        role: newRole,
        brand_id: brand?.id || 1,
      });

      const displayRole = res.data.role === 'admin' ? 'ADMINISTRATOR' : 'CREATOR';
      setUserSuccess(`Successfully registered ${res.data.email} as ${displayRole}!`);
      setNewEmail('');
      setNewPassword('');
      setSelectedUserId(res.data.id);

      await fetchAdminData();
      setTimeout(() => {
        setUserSuccess(null);
        setShowAddUserModal(false);
      }, 2000);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        const messages = detail.map((d: any) => d.msg || 'Invalid field').join(' | ');
        setUserError(messages);
      } else if (typeof detail === 'string') {
        setUserError(detail);
      } else {
        setUserError('Failed to create team user. Please try again.');
      }
    } finally {
      setUserLoading(false);
    }
  };

  // 2. Handle User Status Toggle
  const handleToggleUserStatus = async (userToToggle: User) => {
    if (userToToggle.email === 'admin@company.com') {
      alert('The primary administrator account cannot be deactivated.');
      return;
    }

    setActionLoadingId(userToToggle.id);
    try {
      const res = await apiClient.patch<User>(`/admin/users/${userToToggle.id}/toggle-status`);
      setUsers((prev) => prev.map((u) => (u.id === res.data.id ? res.data : u)));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update user status.');
    } finally {
      setActionLoadingId(null);
    }
  };

  // 3. Handle Delete User
  const handleDeleteUser = async (userToDelete: User) => {
    if (userToDelete.email === 'admin@company.com') {
      alert('The primary administrator account cannot be deleted.');
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to remove user ${userToDelete.email}? If they have generated past posters, their account will be safely archived to protect post history.`
    );
    if (!confirmed) return;

    setActionLoadingId(userToDelete.id);
    try {
      await apiClient.delete(`/admin/users/${userToDelete.id}`);
      await fetchAdminData();
      if (selectedUserId === userToDelete.id) {
        setSelectedUserId(users.find((u) => u.id !== userToDelete.id)?.id || null);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete user.');
    } finally {
      setActionLoadingId(null);
    }
  };


  const getGreetingName = () => {
    if (currentUser?.email) {
      const prefix = currentUser.email.split('@')[0].toLowerCase();
      if (prefix === 'admin' || currentUser.role === 'admin') return 'Admin';
      if (prefix === 'creator' || currentUser.role === 'member') return 'Creator';
      return prefix.charAt(0).toUpperCase() + prefix.slice(1);
    }
    return 'Admin';
  };

  // Filtered member directory for vertical scrolling & pagination
  const filteredUsers = users.filter((u) =>
    u.email.toLowerCase().includes(userSearchQuery.trim().toLowerCase())
  );

  // Pagination calculation
  const totalPages = Math.max(1, Math.ceil(filteredUsers.length / usersPerPage));
  const paginatedUsers = filteredUsers.slice(
    (currentPage - 1) * usersPerPage,
    currentPage * usersPerPage
  );

  // Resolved active member for deep chart analysis
  const activeSelectedUser =
    users.find((u) => u.id === selectedUserId) || users[0] || null;

  const selectedCreatorAnalytics =
    analytics?.creators?.find((c) => c.creator_id === (activeSelectedUser?.id || selectedUserId)) ||
    analytics?.creators?.[0] ||
    null;

  const maxTimelineCount = Math.max(
    1,
    ...(selectedCreatorAnalytics?.timeline?.map((t) => t.published_count) || [1])
  );

  const selectedTimeframeCount =
    selectedCreatorAnalytics
      ? analyticsTimeframe === 'week'
        ? selectedCreatorAnalytics.published_this_week
        : analyticsTimeframe === 'month'
        ? selectedCreatorAnalytics.published_this_month
        : analyticsTimeframe === 'year'
        ? selectedCreatorAnalytics.published_this_year
        : selectedCreatorAnalytics.total_published
      : 0;


  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* 1. Header & Welcome Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-bold text-purple-800">
              <Shield className="h-3.5 w-3.5" /> Admin Portal
            </span>
            <span className="text-xs text-slate-300">•</span>
            <span className="text-xs font-semibold text-slate-500">42 WORKS AI Studio</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-900">
            Welcome, {getGreetingName()}
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-500 font-medium">
            Here's where things stand today across creator performance, publishing metrics, and brand identity.
          </p>
        </div>

        {/* Clean Header Action Buttons */}
        <div className="flex items-center gap-2.5 self-start sm:self-auto shrink-0">
          <a
            href="/"
            className="flex items-center gap-1.5 rounded-xl bg-[#FFC20E] hover:bg-[#e5ae0d] px-4 py-2 text-xs font-black text-slate-950 shadow-sm transition-all hover:scale-102"
          >
            <Sparkles className="h-4 w-4" />
            Create Poster
          </a>

          <button
            onClick={handleSyncWorkspace}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 px-3.5 py-2 text-xs font-bold text-slate-700 shadow-2xs transition-colors disabled:opacity-50 cursor-pointer"
            title="Refresh All Database Metrics"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin text-[#FFC20E]' : 'text-slate-600'}`} />
            {isRefreshing ? 'Syncing...' : 'Sync Data'}
          </button>
        </div>
      </div>

      {/* Sync Confirmation Banner */}
      {syncFeedback && (
        <div className="flex items-center justify-between rounded-2xl bg-emerald-50 border border-emerald-200 px-4 py-3 text-xs text-emerald-800 shadow-2xs animate-fadeIn">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 shrink-0 text-emerald-600" />
            <span className="font-semibold">{syncFeedback}</span>
          </div>
          <button
            onClick={() => setSyncFeedback(null)}
            className="text-emerald-700 hover:text-emerald-950 text-xs font-bold cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* 2. Top Summary KPI Overview Cards */}
      <div ref={analyticsSectionRef} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Published Live */}
        <div className="kpi-card rounded-3xl border border-slate-200 bg-white p-5 shadow-xs transition-all hover:shadow-md">
          <div className="flex items-center justify-between text-xs font-bold text-slate-500 mb-2">
            <span className="flex items-center gap-1.5 text-emerald-700">
              <TrendingUp className="h-4 w-4" /> Published Live
            </span>
            <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
              Live Posts
            </span>
          </div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-900">
              {analytics
                ? analyticsTimeframe === 'week'
                  ? analytics.published_this_week
                  : analyticsTimeframe === 'month'
                  ? analytics.published_this_month
                  : analyticsTimeframe === 'year'
                  ? analytics.published_this_year
                  : analytics.total_published
                : 0}
            </span>
            <span className="text-xs font-semibold text-slate-500">
              {analyticsTimeframe === 'week'
                ? 'this week'
                : analyticsTimeframe === 'month'
                ? 'this month'
                : analyticsTimeframe === 'year'
                ? 'this year'
                : 'total'}
            </span>
          </div>
          <p className="mt-2 text-[11px] text-slate-500 font-medium">
            Active on LinkedIn & Instagram business channels
          </p>
        </div>

        {/* Card 2: Total Generated Creations */}
        <div className="kpi-card rounded-3xl border border-slate-200 bg-white p-5 shadow-xs transition-all hover:shadow-md">
          <div className="flex items-center justify-between text-xs font-bold text-slate-500 mb-2">
            <span className="flex items-center gap-1.5 text-blue-700">
              <Sparkles className="h-4 w-4" /> Total Generated
            </span>
            <span className="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-bold text-blue-700 border border-blue-200">
              Creations
            </span>
          </div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-900">
              {analytics ? analytics.total_posters_generated : 0}
            </span>
            <span className="text-xs font-semibold text-slate-500">posters</span>
          </div>
          <p className="mt-2 text-[11px] text-slate-500 font-medium">
            AI-designed graphics, quotes, and social copy
          </p>
        </div>

        {/* Card 3: Scheduled Queue */}
        <div className="kpi-card rounded-3xl border border-slate-200 bg-white p-5 shadow-xs transition-all hover:shadow-md">
          <div className="flex items-center justify-between text-xs font-bold text-slate-500 mb-2">
            <span className="flex items-center gap-1.5 text-amber-700">
              <Clock className="h-4 w-4" /> Scheduled Queue
            </span>
            <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-bold text-amber-800 border border-amber-200">
              Upcoming
            </span>
          </div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-3xl font-black text-amber-600">
              {analytics ? analytics.total_scheduled : 0}
            </span>
            <span className="text-xs font-semibold text-slate-500">in queue</span>
          </div>
          <p className="mt-2 text-[11px] text-slate-500 font-medium">
            Automated calendar drops ready for release
          </p>
        </div>

        {/* Card 4: Active Team Members */}
        <div className="kpi-card rounded-3xl border border-slate-200 bg-white p-5 shadow-xs transition-all hover:shadow-md">
          <div className="flex items-center justify-between text-xs font-bold text-slate-500 mb-2">
            <span className="flex items-center gap-1.5 text-purple-700">
              <Users className="h-4 w-4" /> Team Members
            </span>
            <span className="rounded-full bg-purple-50 px-2 py-0.5 text-[10px] font-bold text-purple-700 border border-purple-200">
              Active
            </span>
          </div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-900">{users.length}</span>
            <span className="text-xs font-semibold text-slate-500">accounts</span>
          </div>
          <p className="mt-2 text-[11px] text-slate-500 font-medium">
            Admins & creators on the workspace
          </p>
        </div>
      </div>

      {/* 3. Team Member Management & Performance Analytics (Unified Single Container) */}
      <div className="rounded-3xl border border-slate-200 bg-white shadow-xs overflow-hidden">
        {/* Top Header of the Unified Container */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 sm:p-7 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-amber-50 text-[#FFC20E] border border-amber-200 shadow-xs">
              <BarChart3 className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-black text-slate-900">Creator Performance & Member Management</h2>
              <p className="text-xs text-slate-500 font-medium">
                Click any team member on the left to inspect their output analytics, activity chart, and account status.
              </p>
            </div>
          </div>

          {/* Quick Add Team Member Button */}
          <button
            onClick={() => setShowAddUserModal(true)}
            className="flex items-center gap-1.5 rounded-xl bg-[#FFC20E] hover:bg-[#e5ae0d] px-4 py-2 text-xs font-bold text-slate-950 shadow-xs transition-all hover:scale-102 cursor-pointer self-start sm:self-auto"
          >
            <UserPlus className="h-4 w-4" />
            Add Member
          </button>
        </div>

        {/* Unified 2-Pane Content in the Single Box */}
        <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[460px]">
          {/* Left Pane: Member List with Search & Vertical Scroll for Scalability */}
          <div className="lg:col-span-5 border-b lg:border-b-0 lg:border-r border-slate-100 bg-slate-50/50 p-5 sm:p-6 flex flex-col justify-between">
            <div className="space-y-3.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-purple-600" />
                  <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    Members ({users.length})
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 font-medium">Click to select</span>
              </div>

              {/* Search by email */}
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
                <input
                  type="text"
                  value={userSearchQuery}
                  onChange={(e) => {
                    setUserSearchQuery(e.target.value);
                    setCurrentPage(1);
                  }}
                  placeholder="Search by email..."
                  className="w-full rounded-xl border border-slate-200 bg-white pl-8 pr-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:border-[#FFC20E] focus:outline-none shadow-2xs"
                />
                {userSearchQuery && (
                  <button
                    onClick={() => setUserSearchQuery('')}
                    className="absolute right-2.5 top-2 text-slate-400 hover:text-slate-700 cursor-pointer"
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>

              {/* Scrollable Members List */}
              <div className="space-y-2 max-h-[350px] overflow-y-auto pr-1">
                {paginatedUsers.length > 0 ? (
                  paginatedUsers.map((u) => {
                    const isSelected = (activeSelectedUser?.id || selectedUserId) === u.id;

                    return (
                      <div
                        key={u.id}
                        onClick={() => setSelectedUserId(u.id)}
                        className={`rounded-2xl p-3.5 transition-all cursor-pointer border flex items-center justify-between gap-3 ${
                          isSelected
                            ? 'bg-amber-50/70 border-[#FFC20E] ring-2 ring-[#FFC20E]/40 shadow-xs'
                            : 'bg-white border-slate-200/80 hover:border-slate-300 hover:bg-slate-50/60'
                        }`}
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <div
                            className={`flex h-9 w-9 items-center justify-center rounded-xl font-bold text-xs uppercase shrink-0 transition-colors ${
                              isSelected
                                ? 'bg-[#FFC20E] text-slate-950 font-black'
                                : 'bg-slate-900 text-white'
                            }`}
                          >
                            {u.email.substring(0, 2)}
                          </div>
                          <div className="min-w-0">
                            <p className="font-bold text-xs text-slate-900 truncate">{u.email}</p>
                            <p className="text-[10px] text-slate-400 font-medium">
                              User ID #{u.id} • {u.is_active ? 'Active' : 'Inactive'}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <span
                            className={`rounded-md px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider ${
                              u.role === 'admin'
                                ? 'bg-purple-100 text-purple-700 border border-purple-200'
                                : 'bg-amber-100 text-amber-800 border border-amber-200'
                            }`}
                          >
                            {u.role === 'admin' ? 'ADMIN' : 'CREATOR'}
                          </span>
                          {isSelected && <ChevronRight className="h-4 w-4 text-[#b58705]" />}
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="p-6 text-center text-xs text-slate-400">
                    No members match "{userSearchQuery}".
                  </div>
                )}
              </div>
            </div>

            {/* Bottom Pagination for scaling to 100-200+ members */}
            <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-200/80 text-xs text-slate-600">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer text-[11px] font-semibold"
              >
                <ChevronLeft className="h-3.5 w-3.5" /> Prev
              </button>
              <span className="text-[11px] font-medium text-slate-500">
                Page {currentPage} of {totalPages} ({filteredUsers.length} total)
              </span>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer text-[11px] font-semibold"
              >
                Next <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          {/* Right Pane: Selected Member's Details, Metrics & Dynamic Chart (in SAME Box) */}
          <div className="lg:col-span-7 p-6 sm:p-7 flex flex-col justify-between space-y-5 bg-white">
            {activeSelectedUser ? (
              <>
                {/* Header of Selected Creator */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-4 border-b border-slate-100">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="flex h-11 w-11 sm:h-12 sm:w-12 items-center justify-center rounded-2xl bg-slate-900 text-white font-black text-sm uppercase shadow-xs shrink-0">
                      {activeSelectedUser.email.substring(0, 2)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-sm sm:text-base font-bold text-slate-900 truncate max-w-[180px] xs:max-w-[240px] sm:max-w-xs">
                          {activeSelectedUser.email}
                        </h3>
                        <span
                          className={`rounded-md px-2 py-0.5 text-[9px] font-bold uppercase shrink-0 ${
                            activeSelectedUser.role === 'admin'
                              ? 'bg-purple-100 text-purple-700'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {activeSelectedUser.role === 'admin' ? 'ADMIN' : 'CREATOR'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        User ID #{activeSelectedUser.id} • Joined{" "}
                        {new Date(activeSelectedUser.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex sm:flex-col items-center sm:items-end justify-between gap-1 pt-1 sm:pt-0 border-t sm:border-t-0 border-slate-100">
                    <span className="text-2xl sm:text-3xl font-black text-slate-900">{selectedTimeframeCount}</span>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      {analyticsTimeframe === 'week'
                        ? 'Posts This Week'
                        : analyticsTimeframe === 'month'
                        ? 'Posts This Month'
                        : analyticsTimeframe === 'year'
                        ? 'Posts This Year'
                        : 'Total Posts'}
                    </span>
                  </div>
                </div>

                {/* Timeframe Selector Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <span className="text-xs font-bold text-slate-700">{getTimelineTitle()}</span>
                  <div className="flex items-center gap-1 rounded-xl bg-slate-100 p-1 border border-slate-200 self-start sm:self-auto overflow-x-auto">
                    {(['week', 'month', 'year', 'all'] as const).map((tf) => (
                      <button
                        key={tf}
                        onClick={() => handleTimeframeChange(tf)}
                        className={`rounded-lg px-2.5 py-1 text-[11px] font-bold cursor-pointer transition-all ${
                          analyticsTimeframe === tf
                            ? 'bg-white text-slate-900 shadow-xs'
                            : 'text-slate-500 hover:text-slate-800'
                        }`}
                      >
                        {tf === 'week' ? 'Week' : tf === 'month' ? 'Month' : tf === 'year' ? 'Year' : 'All'}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Chart Box */}
                <div className="border border-slate-100 rounded-2xl bg-slate-50/60 p-4 min-h-[170px] flex items-end">
                  {selectedCreatorAnalytics?.timeline && selectedCreatorAnalytics.timeline.length > 0 ? (
                    <div
                      className={`grid ${getTimelineGridClass(
                        selectedCreatorAnalytics.timeline.length
                      )} gap-2 items-end w-full h-36`}
                    >
                      {selectedCreatorAnalytics.timeline.map((point, idx) => (
                        <div key={idx} className="group relative flex flex-col items-center gap-1.5 h-full justify-end">
                          <div
                            style={{
                              height: `${
                                point.published_count > 0
                                  ? Math.max(25, Math.round((point.published_count / maxTimelineCount) * 100))
                                  : 8
                              }%`,
                            }}
                            className={`w-full rounded-md transition-all ${
                              point.published_count > 0
                                ? 'bg-[#FFC20E] group-hover:bg-amber-500 shadow-xs'
                                : 'bg-slate-200/80'
                            }`}
                          />
                          <span className="text-[10px] font-semibold text-slate-500 group-hover:text-slate-900 truncate max-w-full text-center">
                            {point.label}
                          </span>
                          {point.published_count > 0 && (
                            <div className="absolute -top-7 hidden group-hover:flex items-center justify-center rounded bg-slate-900 px-2 py-0.5 text-[9px] font-bold text-white shadow-xs z-10 whitespace-nowrap">
                              {point.published_count} posted
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="h-32 flex items-center justify-center text-xs text-slate-400 w-full">
                      No publishing activity recorded for this period.
                    </div>
                  )}
                </div>

                {/* Account Actions Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-100">
                  <div className="flex items-center gap-3 text-xs text-slate-500">
                    <span className="flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5 text-slate-400" />
                      Scheduled: <strong>{selectedCreatorAnalytics?.scheduled_count || 0}</strong>
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Archive className="h-3.5 w-3.5 text-slate-400" />
                      Archived: <strong>{selectedCreatorAnalytics?.archived_count || 0}</strong>
                    </span>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-auto">
                    {/* Toggle Active Status */}
                    {activeSelectedUser.email !== 'admin@company.com' && (
                      <button
                        onClick={() => handleToggleUserStatus(activeSelectedUser)}
                        disabled={actionLoadingId === activeSelectedUser.id}
                        className={`flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs font-bold transition-colors cursor-pointer ${
                          activeSelectedUser.is_active
                            ? 'border-amber-200 bg-amber-50/70 text-amber-800 hover:bg-amber-100'
                            : 'border-emerald-200 bg-emerald-50 text-emerald-800 hover:bg-emerald-100'
                        }`}
                      >
                        <Power className="h-3.5 w-3.5" />
                        {activeSelectedUser.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    )}

                    {/* Delete User */}
                    {activeSelectedUser.email !== 'admin@company.com' && (
                      <button
                        onClick={() => handleDeleteUser(activeSelectedUser)}
                        disabled={actionLoadingId === activeSelectedUser.id}
                        className="flex items-center gap-1.5 rounded-xl border border-rose-200 bg-rose-50 hover:bg-rose-100 px-3 py-1.5 text-xs font-bold text-rose-700 transition-colors cursor-pointer"
                      >
                        <Trash2 className="h-3.5 w-3.5 text-rose-500" />
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-slate-400 text-xs">
                <Users className="h-8 w-8 mb-2 text-slate-300" />
                Select a member on the left to see their performance details.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 4. Team Memory & AI Learning Section */}
      <div className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-7 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-5">
              <div className="flex items-center gap-2.5">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-sky-50 text-sky-600 border border-sky-200">
                  <Brain className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Team Memory & AI Learning</h3>
                  <p className="text-xs text-slate-500 font-medium">Automatic RAG & Knowledge Graph.</p>
                </div>
              </div>
              <span className="rounded-full bg-sky-50 text-sky-700 border border-sky-200 px-2.5 py-0.5 text-[10px] font-bold">
                Connected
              </span>
            </div>

            <div className="space-y-4">
              {/* Approved Occasions */}
              <div>
                <p className="text-xs text-slate-700 font-bold mb-2">Approved Occasions in Memory:</p>
                <div className="flex flex-wrap gap-1.5">
                  {knowledge && knowledge.occasions && knowledge.occasions.length > 0 ? (
                    knowledge.occasions.map((occ) => (
                      <span
                        key={occ.id}
                        className="rounded-lg bg-slate-100 border border-slate-200 px-3 py-1 text-xs text-slate-700 font-medium hover:bg-slate-200 transition-colors"
                      >
                        {occ.name}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-400 italic">No occasions approved yet.</span>
                  )}
                </div>
              </div>

              {/* Top Performed Templates */}
              <div>
                <p className="text-xs text-slate-700 font-bold mb-2">Top Performed Templates:</p>
                <div className="space-y-2">
                  {knowledge && knowledge.top_templates && knowledge.top_templates.length > 0 ? (
                    knowledge.top_templates.map((tpl) => (
                      <div
                        key={tpl.id}
                        className="rounded-xl border border-slate-100 bg-slate-50 px-3.5 py-2.5 text-xs flex items-center justify-between hover:bg-slate-100/80 transition-colors"
                      >
                        <span className="font-bold text-slate-800 capitalize">
                          {tpl.template_name.replace(/_/g, ' ')}
                        </span>
                        <span className="rounded-md bg-emerald-50 text-emerald-700 px-2 py-0.5 text-[10px] font-bold border border-emerald-200">
                          {tpl.approval_count} approvals
                        </span>
                      </div>
                    ))
                  ) : (
                    <span className="text-xs text-slate-400 italic">No template metrics yet.</span>
                  )}
                </div>
              </div>

              {/* Brand Knowledge Base Integration */}
              <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4 text-xs text-slate-600 space-y-1.5">
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                  Vector Database RAG Status
                </span>
                <p className="text-slate-700 font-medium leading-relaxed">
                  Pinecone knowledge index <span className="font-mono text-purple-700 font-bold">poster-studio-knowledge</span> is active with 9 product chunks.
                </p>
                <p className="text-[11px] text-slate-400">
                  Pickachoo Mascot assistant utilizes this vector index to answer non-technical questions about studio tools.
                </p>
              </div>
            </div>
          </div>
        </div>

      {/* 5. Add Team Member Modal */}
      {showAddUserModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-purple-50 text-purple-600 border border-purple-200">
                  <UserPlus className="h-4 w-4" />
                </div>
                <h3 className="text-sm font-bold text-slate-900">Add New Team User</h3>
              </div>
              <button
                onClick={() => setShowAddUserModal(false)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-lg hover:bg-slate-100 cursor-pointer"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {userSuccess && (
              <div className="flex items-center gap-2 rounded-2xl bg-emerald-50 border border-emerald-200 p-3 text-xs text-emerald-800">
                <CheckCircle className="h-4 w-4 shrink-0 text-emerald-600" />
                <span className="font-semibold">{userSuccess}</span>
              </div>
            )}
            {userError && (
              <div className="flex items-center gap-2 rounded-2xl bg-rose-50 border border-rose-200 p-3 text-xs text-rose-800">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
                <span className="font-semibold">{userError}</span>
              </div>
            )}

            <form onSubmit={handleCreateUser} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-[#FFC20E] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Initial Password</label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-[#FFC20E] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Workspace Role</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value as UserRole)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-900 font-medium focus:border-[#FFC20E] focus:outline-none"
                >
                  <option value="member">Creator</option>
                  <option value="admin">Administrator</option>
                </select>
                <p className="mt-1 text-[11px] text-slate-400">
                  Creators generate posters. Administrators manage brand guidelines and team access.
                </p>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddUserModal(false)}
                  className="rounded-xl px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={userLoading}
                  className="flex items-center gap-1.5 rounded-xl bg-[#FFC20E] hover:bg-[#e5ae0d] px-4 py-2 text-xs font-bold text-slate-950 shadow-sm disabled:opacity-50 cursor-pointer"
                >
                  <UserPlus className="h-3.5 w-3.5" />
                  {userLoading ? 'Creating...' : 'Create Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
