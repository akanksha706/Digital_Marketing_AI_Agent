import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { Poster, PostStatus } from '../types';
import { ReviewModal } from './ReviewModal';
import { AppreciativePoster } from '../components/AppreciativePoster';
import { Layers, Search, Eye, Clock, Trash2, Archive, RotateCcw, Filter, ChevronDown, Sparkles, Plus } from 'lucide-react';
import gsap from 'gsap';

const STATUS_OPTIONS: { id: PostStatus; label: string; color: string }[] = [
  { id: 'in_review', label: 'In Review', color: 'bg-amber-400' },
  { id: 'approved', label: 'Approved', color: 'bg-blue-500' },
  { id: 'published', label: 'Published', color: 'bg-emerald-500' },
  { id: 'scheduled', label: 'Scheduled', color: 'bg-purple-500' },
];

export const LibraryPage: React.FC = () => {
  const [posters, setPosters] = useState<Poster[]>([]);
  const [viewMode, setViewMode] = useState<'active' | 'archived'>('active');
  const [selectedStatuses, setSelectedStatuses] = useState<PostStatus[]>([]);
  const [filterDropdownOpen, setFilterDropdownOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedPoster, setSelectedPoster] = useState<Poster | null>(null);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const gridRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchPosters();
  }, []);

  // Close filter dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setFilterDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchPosters = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get<Poster[]>('/posters?limit=100&include_archived=true');
      setPosters(res.data);
    } catch {
      // Dev fallback
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDirect = async (poster: Poster) => {
    if (poster.status === 'published') {
      const confirmed = confirm(
        'This poster was already published to social media.\n\nIt will be moved to your Published Vault so your active studio stays clean, while preserving your AI Knowledge Graph & Admin analytics metrics.\n\nMove to Published Vault?'
      );
      if (!confirmed) return;

      try {
        setPosters((prev) => prev.filter((p) => p.id !== poster.id));
        await apiClient.delete(`/posters/${poster.id}`);
        fetchPosters();
      } catch (err: any) {
        if (err.response?.status !== 404) {
          alert(err.response?.data?.detail || 'Failed to archive poster.');
        }
        fetchPosters();
      }
    } else {
      const confirmed = confirm('Are you sure you want to permanently delete this unpublished draft?');
      if (!confirmed) return;

      try {
        setPosters((prev) => prev.filter((p) => p.id !== poster.id));
        await apiClient.delete(`/posters/${poster.id}?force_hard_delete=true`);
        fetchPosters();
      } catch (err: any) {
        if (err.response?.status !== 404) {
          alert(err.response?.data?.detail || 'Failed to delete poster.');
        }
        fetchPosters();
      }
    }
  };

  const handleRestorePoster = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    try {
      await apiClient.patch(`/posters/${id}/archive?archive=false`);
      fetchPosters();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to restore poster.');
    }
  };

  const handleDeletePermanent = async (poster: Poster) => {
    const confirmed = confirm(
      'Are you sure you want to permanently purge this poster from the database and vault? This action cannot be undone.'
    );
    if (!confirmed) return;

    try {
      setPosters((prev) => prev.filter((p) => p.id !== poster.id));
      await apiClient.delete(`/posters/${poster.id}?force_hard_delete=true`);
      fetchPosters();
    } catch (err: any) {
      if (err.response?.status !== 404) {
        alert(err.response?.data?.detail || 'Failed to permanently delete poster.');
      }
      fetchPosters();
    }
  };

  const activeCount = posters.filter((p) => !p.is_archived).length;
  const archivedCount = posters.filter((p) => p.is_archived).length;

  const toggleStatus = (status: PostStatus) => {
    setSelectedStatuses((prev) =>
      prev.includes(status) ? prev.filter((s) => s !== status) : [...prev, status]
    );
  };

  const handleSelectAll = () => {
    if (selectedStatuses.length === STATUS_OPTIONS.length) {
      setSelectedStatuses([]);
    } else {
      setSelectedStatuses(STATUS_OPTIONS.map((s) => s.id));
    }
  };

  const filterLabel =
    selectedStatuses.length === 0 || selectedStatuses.length === STATUS_OPTIONS.length
      ? 'All Statuses'
      : selectedStatuses.length === 1
      ? STATUS_OPTIONS.find((s) => s.id === selectedStatuses[0])?.label
      : `${selectedStatuses.length} Statuses`;

  const filteredPosters = posters.filter((p) => {
    const matchesArchived = viewMode === 'archived' ? p.is_archived : !p.is_archived;
    const matchesFilter =
      selectedStatuses.length === 0 ||
      selectedStatuses.length === STATUS_OPTIONS.length ||
      selectedStatuses.includes(p.status);
    const matchesSearch =
      p.prompt.toLowerCase().includes(search.toLowerCase()) ||
      p.headline.toLowerCase().includes(search.toLowerCase());
    return matchesArchived && matchesFilter && matchesSearch;
  });

  // GSAP entrance stagger animation whenever filtered results or load finishes
  useEffect(() => {
    if (!loading && gridRef.current) {
      const cards = gridRef.current.querySelectorAll('.poster-card');
      if (cards.length > 0) {
        gsap.fromTo(
          cards,
          { opacity: 0, y: 28, scale: 0.95 },
          { opacity: 1, y: 0, scale: 1, duration: 0.5, stagger: 0.06, ease: 'back.out(1.4)' }
        );
      }
    }
  }, [loading, selectedStatuses, search, viewMode, posters.length]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      {/* Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-6 mb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <Layers className="h-6 w-6 text-[#FFC20E]" />
            <h1 className="text-2xl font-black tracking-tight text-slate-900">Creative Asset Library</h1>
          </div>
          <p className="mt-1 text-xs text-slate-500 font-medium">
            Review, inspect typography, and manage social dispatch across brand campaigns
          </p>
        </div>

        <Link
          to="/"
          className="inline-flex items-center gap-2 self-start sm:self-auto rounded-xl bg-[#FFC20E] hover:bg-[#e5ae0d] px-4 py-2 text-xs font-bold text-slate-950 shadow-sm transition-all hover:scale-105"
        >
          <Plus className="h-4 w-4" />
          <span>Create New Poster</span>
        </Link>
      </div>

      {/* Dedicated Toolbar Row */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-slate-50/70 p-2.5 sm:px-4 mb-8 shadow-xs">
        {/* Workspace Active vs Published Vault Switch */}
        <div className="flex items-center rounded-xl bg-white border border-slate-200 p-1 text-xs shadow-2xs self-start md:self-auto">
          <button
            onClick={() => setViewMode('active')}
            className={`rounded-lg px-3.5 py-1.5 font-bold transition-all ${
              viewMode === 'active'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Active Studio ({activeCount})
          </button>
          <button
            onClick={() => setViewMode('archived')}
            className={`flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 font-bold transition-all ${
              viewMode === 'archived'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
            title="Archived Published Posters (Preserves AI Knowledge Graph & Metrics)"
          >
            <Archive className="h-3.5 w-3.5" />
            Published Vault ({archivedCount})
          </button>
        </div>

        {/* Search & Filters Controls Group */}
        <div className="flex flex-wrap sm:flex-nowrap items-center gap-2.5 w-full md:w-auto">
          {/* Search Bar */}
          <div className="relative flex-1 sm:w-64">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by prompt or headline..."
              className="w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-[#FFC20E] focus:ring-1 focus:ring-[#FFC20E] focus:outline-none shadow-2xs"
            />
          </div>

          {/* Concise Status Filter Dropdown with Multi-Select Checkboxes */}
          <div className="relative shrink-0" ref={dropdownRef}>
            <button
              onClick={() => setFilterDropdownOpen(!filterDropdownOpen)}
              className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-800 shadow-2xs hover:border-[#FFC20E] transition-all"
            >
              <Filter className="h-3.5 w-3.5 text-slate-500" />
              <span>{filterLabel}</span>
              {selectedStatuses.length > 0 && selectedStatuses.length < STATUS_OPTIONS.length && (
                <span className="flex h-4 w-4 items-center justify-center rounded-full bg-[#FFC20E] text-[10px] font-black text-slate-900">
                  {selectedStatuses.length}
                </span>
              )}
              <ChevronDown
                className={`h-3.5 w-3.5 text-slate-400 transition-transform ${
                  filterDropdownOpen ? 'rotate-180' : ''
                }`}
              />
            </button>

            {filterDropdownOpen && (
              <div className="absolute right-0 mt-2 w-52 rounded-2xl border border-slate-200 bg-white p-2 shadow-xl z-30">
                <div className="px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Filter by Status
                </div>

                {/* All Statuses Checkbox */}
                <label className="flex items-center gap-2.5 rounded-xl px-2.5 py-1.5 text-xs font-bold text-slate-800 hover:bg-slate-50 cursor-pointer transition-colors">
                  <input
                    type="checkbox"
                    checked={
                      selectedStatuses.length === 0 ||
                      selectedStatuses.length === STATUS_OPTIONS.length
                    }
                    onChange={handleSelectAll}
                    className="rounded border-slate-300 text-amber-500 focus:ring-[#FFC20E] h-4 w-4 accent-[#FFC20E]"
                  />
                  <span>All Statuses</span>
                </label>

                <div className="my-1 border-t border-slate-100" />

                {/* Individual Checkbox Options */}
                {STATUS_OPTIONS.map((opt) => {
                  const isChecked = selectedStatuses.includes(opt.id);
                  return (
                    <label
                      key={opt.id}
                      className="flex items-center justify-between rounded-xl px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-2.5">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => toggleStatus(opt.id)}
                          className="rounded border-slate-300 text-amber-500 focus:ring-[#FFC20E] h-4 w-4 accent-[#FFC20E]"
                        />
                        <span className="capitalize">{opt.label}</span>
                      </div>
                      <span className={`h-2 w-2 rounded-full ${opt.color}`} />
                    </label>
                  );
                })}

                {selectedStatuses.length > 0 && (
                  <div className="mt-2 border-t border-slate-100 pt-1.5 px-1">
                    <button
                      onClick={() => setSelectedStatuses([])}
                      className="w-full text-center py-1 text-[11px] font-bold text-slate-500 hover:text-slate-900 transition-colors"
                    >
                      Reset to All
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Grid or Empty State */}
      {loading ? (
        <div className="py-20 text-center text-xs text-slate-400 font-medium">Loading creative library...</div>
      ) : filteredPosters.length === 0 ? (
        <div className="mx-auto max-w-md my-12 rounded-3xl border border-slate-200/80 bg-white p-10 text-center shadow-xs">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-50 text-[#FFC20E] border border-amber-200/80 shadow-xs mb-4">
            {viewMode === 'archived' ? <Archive className="h-7 w-7" /> : <Sparkles className="h-7 w-7" />}
          </div>
          <h3 className="text-base font-black text-slate-900">
            {viewMode === 'archived' ? 'Published Vault is Empty' : 'Your Library is Fresh & Ready'}
          </h3>
          <p className="mt-2 text-xs text-slate-500 leading-relaxed">
            {viewMode === 'archived'
              ? 'Only posters published to LinkedIn or Instagram that you hide from your active board are stored here to preserve your AI Knowledge Graph and Admin metrics. Unpublished drafts are always permanently deleted.'
              : 'You have not generated any posters yet in this workspace. Describe your campaign topic in the Studio to generate your first visual.'}
          </p>
          {viewMode === 'active' && (
            <div className="mt-6 flex justify-center">
              <Link
                to="/"
                className="inline-flex items-center gap-2 rounded-xl bg-[#FFC20E] hover:bg-[#e5ae0d] px-5 py-2.5 text-xs font-bold text-slate-950 shadow-md shadow-[#FFC20E]/20 transition-all hover:scale-105"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>Generate Your First Poster</span>
              </Link>
            </div>
          )}
        </div>
      ) : (
        <div ref={gridRef} className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {filteredPosters.map((poster) => (
            <div
              key={poster.id}
              onClick={() => {
                setSelectedPoster(poster);
                setReviewOpen(true);
              }}
              className="poster-card group cursor-pointer rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs hover:border-[#FFC20E] hover:shadow-lg transition-all"
            >
              <AppreciativePoster
                src={poster.final_poster_url}
                alt={poster.headline}
                aspectRatio="aspect-square"
              >
                <div className="absolute inset-0 bg-gradient-to-t from-slate-900/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-between p-3 pointer-events-auto">
                  <span className="flex items-center gap-1.5 rounded-xl bg-[#FFC20E] px-3 py-1.5 text-xs font-bold text-slate-950 shadow-md">
                    <Eye className="h-3.5 w-3.5" /> Inspect
                  </span>

                  {viewMode === 'archived' ? (
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={(e) => handleRestorePoster(e, poster.id)}
                        title="Restore to Active Studio"
                        className="flex items-center gap-1 rounded-xl bg-white/90 hover:bg-white px-2.5 py-1.5 text-xs font-bold text-slate-800 shadow-md transition-all hover:scale-105 cursor-pointer"
                      >
                        <RotateCcw className="h-3.5 w-3.5 text-slate-700" /> Restore
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeletePermanent(poster);
                        }}
                        title="Permanently Purge from Database"
                        className="flex h-8 w-8 items-center justify-center rounded-xl bg-white/90 hover:bg-rose-50 text-slate-700 hover:text-rose-600 shadow-md transition-all hover:scale-105 cursor-pointer"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteDirect(poster);
                      }}
                      title={poster.status === 'published' ? 'Move to Published Vault (keeps metrics)' : 'Delete draft permanently'}
                      className="flex h-8 w-8 items-center justify-center rounded-xl bg-white/90 hover:bg-rose-50 text-slate-700 hover:text-rose-600 shadow-md transition-all hover:scale-105 cursor-pointer"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </AppreciativePoster>

              <div className="p-4">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span
                    className={`rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                      poster.status === 'published'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : poster.status === 'approved'
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : poster.status === 'scheduled'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-slate-100 text-slate-600 border border-slate-200'
                    }`}
                  >
                    {poster.status.replace('_', ' ')}
                  </span>
                  <span className="flex items-center gap-1 text-[11px] text-slate-400">
                    <Clock className="h-3 w-3" />
                    {new Date(poster.created_at).toLocaleDateString()}
                  </span>
                </div>

                <h3 className="line-clamp-1 text-xs font-bold text-slate-900">{poster.headline}</h3>
                <p className="mt-1 line-clamp-2 text-[11px] text-slate-500 leading-relaxed">{poster.caption}</p>
                {poster.is_archived && (
                  <div className="mt-2 text-[10px] font-bold text-amber-700/80 flex items-center gap-1">
                    <Archive className="h-2.5 w-2.5 text-amber-600" /> Published Vault • Preserved in AI Memory & Analytics
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Review & Dispatch Modal */}
      {selectedPoster && (
        <ReviewModal
          poster={selectedPoster}
          isOpen={reviewOpen}
          onClose={() => setReviewOpen(false)}
          onUpdated={(updated) => {
            setSelectedPoster(updated);
            fetchPosters();
          }}
          onDeleted={() => {
            fetchPosters();
          }}
        />
      )}
    </div>
  );
};
