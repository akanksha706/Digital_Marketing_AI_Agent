import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from '../api/client';
import type { Poster } from '../types';
import { ReviewModal } from './ReviewModal';
import gsap from 'gsap';
import {
  Sparkles,
  SlidersHorizontal,
  ArrowRight,
  Calendar,
  RotateCw,
  Globe,
  Link as LinkIcon,
  Upload,
  Image as ImageIcon,
  Video,
  X,
  AlertCircle,
} from 'lucide-react';

interface CalendarOccasion {
  id: string;
  name: string;
  date: string;
  category: string;
  badge: string;
  prompt: string;
  poster_prompt?: string;
  video_prompt?: string;
  time_tag: string;
  formatted_date: string;
}

// In-memory session cache for AI completions to keep keystrokes responsive without hardcoded lists
const sessionAutocompleteCache = new Map<string, string>();

export const StudioPage: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [activeFormat, setActiveFormat] = useState<'poster' | 'video'>('poster');
  const [aspectRatio, setAspectRatio] = useState('1:1');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStage, setGenerationStage] = useState(1);
  const [selectedPoster, setSelectedPoster] = useState<Poster | null>(null);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [modalInitialTab, setModalInitialTab] = useState<'poster' | 'linkedin' | 'instagram' | 'video'>('poster');
  const [modalInitialVideoUrl, setModalInitialVideoUrl] = useState<string | null>(null);
  const [modalInitialVideoModel, setModalInitialVideoModel] = useState<string>('');

  // Inline Notification / Error Banner (replaces intrusive alert popups)
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Smart Compose / Ghost Text State (Google Colab & Gmail Tab-to-Complete)
  const [ghostSuffix, setGhostSuffix] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const autocompleteTimerRef = useRef<any>(null);

  // Attached Web Link State
  const [attachedUrl, setAttachedUrl] = useState<string>('');
  const [showUrlInput, setShowUrlInput] = useState<boolean>(false);
  const [urlInputDraft, setUrlInputDraft] = useState<string>('');

  // Attached Custom Image State
  const [customImageFile, setCustomImageFile] = useState<File | null>(null);
  const [customImagePreview, setCustomImagePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Dynamic Upcoming Festivals Calendar State (Top 5 from Google Calendar)
  const [calendarOccasions, setCalendarOccasions] = useState<CalendarOccasion[]>([]);
  const [isLoadingCalendar, setIsLoadingCalendar] = useState(false);

  const heroRef = useRef<HTMLDivElement>(null);
  const orb1Ref = useRef<HTMLDivElement>(null);
  const orb2Ref = useRef<HTMLDivElement>(null);
  const progressLineRef = useRef<HTMLDivElement>(null);

  // GSAP Choreographed Master Entrance Timeline
  useEffect(() => {
    if (orb1Ref.current) {
      gsap.to(orb1Ref.current, {
        x: 40,
        y: -35,
        scale: 1.18,
        duration: 8,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
      });
    }
    if (orb2Ref.current) {
      gsap.to(orb2Ref.current, {
        x: -45,
        y: 30,
        scale: 1.12,
        duration: 9.5,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
        delay: 0.6,
      });
    }

    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

    if (heroRef.current) {
      tl.fromTo(
        heroRef.current.querySelector('.hero-badge'),
        { scale: 0.8, opacity: 0, y: -20 },
        { scale: 1, opacity: 1, y: 0, duration: 0.5, ease: 'back.out(2)' }
      )
        .fromTo(
          heroRef.current.querySelector('.hero-title'),
          { y: 35, opacity: 0 },
          { y: 0, opacity: 1, duration: 0.65 },
          '-=0.25'
        )
        .fromTo(
          heroRef.current.querySelector('.hero-subtitle'),
          { y: 20, opacity: 0 },
          { y: 0, opacity: 1, duration: 0.5 },
          '-=0.35'
        )
        .fromTo(
          heroRef.current.querySelector('.hero-prompt-box'),
          { y: 30, opacity: 0, scale: 0.97 },
          { y: 0, opacity: 1, scale: 1, duration: 0.6, ease: 'back.out(1.2)' },
          '-=0.3'
        )
        .fromTo(
          heroRef.current.querySelectorAll('.hero-chip'),
          { scale: 0.85, opacity: 0, y: 12 },
          { scale: 1, opacity: 1, y: 0, duration: 0.35, stagger: 0.05, ease: 'power2.out' },
          '-=0.2'
        );
    }
  }, []);

  // GSAP Progress Bar animation when generating
  useEffect(() => {
    if (isGenerating && progressLineRef.current) {
      gsap.fromTo(
        progressLineRef.current,
        { width: '5%' },
        {
          width: `${generationStage === 1 ? '38%' : generationStage === 2 ? '78%' : '96%'}`,
          duration: 1.8,
          ease: 'power2.out',
        }
      );
    }
  }, [isGenerating, generationStage]);

  const aspectRatios = [
    { label: '1:1 Square (Instagram & LinkedIn)', value: '1:1' },
    { label: '9:16 Reel / Story (Video & Reels)', value: '9:16' },
    { label: '4:5 Portrait (Instagram Standard)', value: '4:5' },
    { label: '16:9 Landscape (LinkedIn Article)', value: '16:9' },
  ];

  // Fetch upcoming 5 festivals dynamically from Google Calendar
  const fetchCalendarInspirations = async () => {
    setIsLoadingCalendar(true);
    try {
      const res = await apiClient.get<CalendarOccasion[]>('/posters/calendar-inspirations', {
        params: { limit: 5 },
      });
      if (res.data && res.data.length > 0) {
        setCalendarOccasions(res.data);
      }
    } catch (err) {
      console.warn('Google Calendar inspirations fetch error:', err);
    } finally {
      setIsLoadingCalendar(false);
    }
  };

  useEffect(() => {
    fetchCalendarInspirations();
  }, []);

  // Compute smart autocomplete continuation directly using the AI model
  const formatSuffix = (cont: string, currentText: string): string => {
    if (currentText.endsWith(' ') && cont.startsWith(' ')) {
      return cont.slice(1);
    }
    if (!currentText.endsWith(' ') && !cont.startsWith(' ') && !cont.startsWith(',')) {
      return ' ' + cont;
    }
    return cont;
  };

  const computeAutocomplete = (text: string) => {
    if (autocompleteTimerRef.current) clearTimeout(autocompleteTimerRef.current);
    const trimmed = text.trim();
    if (!trimmed || trimmed.length < 2) {
      setGhostSuffix('');
      return;
    }

    const key = text.toLowerCase();
    if (sessionAutocompleteCache.has(key)) {
      setGhostSuffix(formatSuffix(sessionAutocompleteCache.get(key)!, text));
      return;
    }

    autocompleteTimerRef.current = setTimeout(async () => {
      try {
        const res = await apiClient.get<{ completion: string }>('/posters/autocomplete', {
          params: { text },
        });
        if (res.data?.completion) {
          const comp = res.data.completion;
          sessionAutocompleteCache.set(key, comp);
          setGhostSuffix(formatSuffix(comp, text));
        } else {
          setGhostSuffix('');
        }
      } catch {
        setGhostSuffix('');
      }
    }, 150);
  };

  const handlePromptChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setPrompt(val);
    computeAutocomplete(val);

    // Auto-detect URL pasted directly into prompt
    const urlMatch = val.match(/https?:\/\/[^\s]+/i);
    if (urlMatch && !attachedUrl) {
      setAttachedUrl(urlMatch[0]);
    }

    // Auto-switch to video format if prompt mentions video/reel keywords
    if (/\b(create\s+video|make\s+video|generate\s+video|video\s+of|video\s+reel|wan\s*2|animation)\b/i.test(val)) {
      if (activeFormat !== 'video') {
        setActiveFormat('video');
        setAspectRatio('9:16');
      }
    }
  };

  const acceptAutocomplete = () => {
    if (!ghostSuffix) return;
    setPrompt((prev) => prev + ghostSuffix);
    setGhostSuffix('');
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab' && ghostSuffix) {
      e.preventDefault();
      acceptAutocomplete();
      return;
    }

    if (e.key === 'ArrowRight' && ghostSuffix) {
      const target = e.currentTarget;
      if (target.selectionStart === prompt.length) {
        e.preventDefault();
        acceptAutocomplete();
        return;
      }
    }

    if (e.key === 'Escape' && ghostSuffix) {
      e.preventDefault();
      setGhostSuffix('');
      return;
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if ((prompt.trim() || attachedUrl || customImageFile) && !isGenerating) {
        handleMainGenerate();
      }
      return;
    }

    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      if ((prompt.trim() || attachedUrl || customImageFile) && !isGenerating) {
        handleMainGenerate();
      }
      return;
    }
  };

  const handleImageFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setCustomImageFile(file);
      const previewUrl = URL.createObjectURL(file);
      setCustomImagePreview(previewUrl);
      setErrorMessage(null);
    }
  };

  const handleAddUrl = () => {
    if (urlInputDraft.trim()) {
      setAttachedUrl(urlInputDraft.trim());
      setUrlInputDraft('');
      setShowUrlInput(false);
      setErrorMessage(null);
    }
  };

  // Master Orchestrated Generation Action
  const handleMainGenerate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (isGenerating) return;

    const trimmedPrompt = prompt.trim();
    
    // Intelligently resolve web URL from attachedUrl state, draft input, or pasted directly in the prompt
    const urlFromPrompt = trimmedPrompt.match(/https?:\/\/[^\s"'<>]+/i)?.[0] || '';
    const resolvedUrl = (attachedUrl || urlInputDraft.trim() || urlFromPrompt).trim().replace(/[.,;:]+$/, '');
    
    // Clean user directive text by stripping the raw URL and separators if present
    let cleanDirective = trimmedPrompt;
    if (resolvedUrl && cleanDirective.includes(resolvedUrl)) {
      cleanDirective = cleanDirective.replace(resolvedUrl, '').replace(/::+/g, ' ').replace(/\s+/g, ' ').trim();
    }

    if (!trimmedPrompt && !resolvedUrl && !customImageFile) {
      setErrorMessage('Please enter a creative prompt, paste a web link, or attach an image.');
      return;
    }

    setErrorMessage(null);
    setIsGenerating(true);
    setGenerationStage(1);

    const timer1 = setTimeout(() => setGenerationStage(2), 2200);
    const timer2 = setTimeout(() => setGenerationStage(3), 4800);

    try {
      const isVideoDirective =
        activeFormat === 'video' ||
        /\b(video|reel|motion|clip|animate|animation|wan)\b/i.test(trimmedPrompt);

      // Branch 1: User uploaded a custom image (with prompt describing what to do)
      if (customImageFile) {
        const targetRatio = isVideoDirective && aspectRatio === '1:1' ? '9:16' : aspectRatio;
        const formData = new FormData();
        formData.append('image', customImageFile);
        formData.append('prompt', trimmedPrompt || 'Highlight and celebrate this featured visual asset in an elegant marketing poster');
        formData.append('aspect_ratio', targetRatio);

        const res = await apiClient.post<Poster>('/custom-creatives/upload-and-generate', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        clearTimeout(timer1);
        clearTimeout(timer2);
        setSelectedPoster(res.data);

        if (isVideoDirective) {
          try {
            const videoRes = await apiClient.post<any>('/videos/from-poster', {
              poster_id: res.data.id,
              duration_seconds: 14,
            });
            setModalInitialTab('video');
            setModalInitialVideoUrl(videoRes.data.video_url);
            setModalInitialVideoModel(videoRes.data.model_used);
          } catch (vidErr) {
            console.warn('Video animation from custom image fallback to poster view:', vidErr);
            setModalInitialTab('poster');
            setModalInitialVideoUrl(null);
          }
        } else {
          setModalInitialTab('poster');
          setModalInitialVideoUrl(null);
        }

        setReviewModalOpen(true);
        return;
      }

      // Branch 2: Web URL provided (Firecrawl scraper & blog synthesis)
      if (resolvedUrl) {
        if (!attachedUrl) {
          setAttachedUrl(resolvedUrl);
        }
        const targetRatio = isVideoDirective && aspectRatio === '1:1' ? '9:16' : aspectRatio;
        const res = await apiClient.post<any>('/campaigns/from-url', {
          url: resolvedUrl,
          aspect_ratio: targetRatio,
          custom_instructions: cleanDirective || undefined,
        });

        clearTimeout(timer1);
        clearTimeout(timer2);
        setSelectedPoster(res.data.poster);

        if (isVideoDirective) {
          try {
            const videoRes = await apiClient.post<any>('/videos/from-poster', {
              poster_id: res.data.poster.id,
              duration_seconds: 14,
            });
            setModalInitialTab('video');
            setModalInitialVideoUrl(videoRes.data.video_url);
            setModalInitialVideoModel(videoRes.data.model_used);
          } catch (vidErr) {
            console.warn('Video animation from URL fallback to poster view:', vidErr);
            setModalInitialTab('poster');
            setModalInitialVideoUrl(null);
          }
        } else {
          setModalInitialTab('poster');
          setModalInitialVideoUrl(null);
        }

        setReviewModalOpen(true);
        return;
      }

      // Branch 3: Actionable Video Reel requested (via Format toggle or prompt intent)
      if (isVideoDirective) {
        const videoRatio = aspectRatio === '1:1' ? '9:16' : aspectRatio;
        const res = await apiClient.post<any>('/videos/generate-from-prompt', {
          prompt: trimmedPrompt,
          aspect_ratio: videoRatio,
          duration_seconds: 14,
        });

        clearTimeout(timer1);
        clearTimeout(timer2);
        setSelectedPoster(res.data.poster);
        setModalInitialTab('video');
        setModalInitialVideoUrl(res.data.video.video_url);
        setModalInitialVideoModel(res.data.video.model_used);
        setReviewModalOpen(true);
        return;
      }

      // Branch 4: Standard Cinema-Grade Static Poster
      const res = await apiClient.post<Poster>('/posters/generate', {
        prompt: trimmedPrompt,
        brand_id: 1,
        aspect_ratio: aspectRatio,
      });

      clearTimeout(timer1);
      clearTimeout(timer2);
      setSelectedPoster(res.data);
      setModalInitialTab('poster');
      setModalInitialVideoUrl(null);
      setReviewModalOpen(true);
    } catch (err: any) {
      console.error('Creative synthesis error trace (for developers):', err);
      const detail = err.response?.data?.detail;
      let userMsg = 'Unable to create your creative right now. Please try again in a few moments.';
      if (typeof detail === 'string') {
        const lower = detail.toLowerCase();
        if (
          lower.includes('traceback') ||
          lower.includes('https://') ||
          lower.includes('client error') ||
          lower.includes('status code') ||
          lower.includes('internalservererror')
        ) {
          userMsg = 'Our creative AI service is temporarily busy. Please wait a moment and try again.';
        } else {
          userMsg = detail;
        }
      }
      setErrorMessage(userMsg);
    } finally {
      setIsGenerating(false);
      setGenerationStage(1);
    }
  };

  return (
    <div className="relative min-h-[calc(100vh-4rem)] bg-white pb-24 flex flex-col justify-between overflow-hidden">
      {/* Ambient Glowing Orbs */}
      <div
        ref={orb1Ref}
        className="pointer-events-none absolute -top-12 -left-12 h-96 w-96 rounded-full bg-gradient-to-tr from-amber-400/20 via-[#FFC20E]/15 to-transparent blur-3xl will-change-transform"
      />
      <div
        ref={orb2Ref}
        className="pointer-events-none absolute top-48 -right-20 h-96 w-96 rounded-full bg-gradient-to-bl from-amber-300/20 via-[#FFC20E]/10 to-transparent blur-3xl will-change-transform"
      />

      <div className="relative mx-auto max-w-4xl px-3 sm:px-6 lg:px-8 text-center flex-1 flex flex-col justify-center pt-6 sm:pt-10 lg:pt-14">
        {/* Hero Generator Header */}
        <div ref={heroRef} className="text-center">
          <div className="hero-badge inline-flex items-center gap-2 rounded-full border border-amber-300 bg-amber-50/90 backdrop-blur-xs px-3.5 py-1.5 text-xs font-bold text-amber-950 mb-4 sm:mb-6 shadow-xs max-w-full">
            <Sparkles className="h-3.5 w-3.5 text-[#FFC20E] shrink-0" />
            <span className="truncate">Cinematic Visual Storytelling & Social Dispatch Studio</span>
          </div>

          <h1 className="hero-title text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 leading-tight">
            <span className="bg-gradient-to-r from-amber-500 via-[#FFC20E] to-amber-600 bg-clip-text text-transparent">
              Creative Studio
            </span>
          </h1>

          <p className="hero-subtitle mt-3 sm:mt-4 text-sm sm:text-base md:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed px-2">
            Create studio-grade posters, video reels, and blog campaigns with just a prompt or web link.
          </p>

          {/* Format Selector Pill (Poster vs Actionable Video Reel) */}
          <div className="mt-8 flex items-center justify-center gap-2">
            <div className="inline-flex rounded-2xl bg-slate-100/90 p-1 border border-slate-200/90 shadow-inner">
              <button
                type="button"
                onClick={() => {
                  setActiveFormat('poster');
                  if (aspectRatio === '9:16') setAspectRatio('1:1');
                  if (/create\s+an\s+elegant\s+celebration\s+video/i.test(prompt)) {
                    setPrompt(prompt.replace(/\bvideo\b/gi, 'poster'));
                  }
                }}
                className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all cursor-pointer ${
                  activeFormat === 'poster'
                    ? 'bg-white text-slate-900 shadow-xs border border-slate-200/80 scale-100'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50/50'
                }`}
              >
                <ImageIcon className="h-3.5 w-3.5 text-amber-500" />
                <span>Static Poster</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setActiveFormat('video');
                  setAspectRatio('9:16');
                  if (/create\s+an\s+elegant\s+celebration\s+poster/i.test(prompt)) {
                    setPrompt(prompt.replace(/\bposter\b/gi, 'video'));
                  }
                }}
                className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all cursor-pointer ${
                  activeFormat === 'video'
                    ? 'bg-white text-slate-900 shadow-xs border border-slate-200/80 scale-100 font-extrabold'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50/50'
                }`}
              >
                <Video className="h-3.5 w-3.5 text-amber-500" />
                <span>Actionable Video Reel</span>
              </button>
            </div>
          </div>

          {/* Inline Error / Safety Warning Banner */}
          {errorMessage && (
            <div className="mt-6 mx-auto max-w-3xl rounded-2xl border border-amber-200 bg-amber-50/95 p-3.5 text-left text-xs text-amber-900 flex items-start justify-between gap-3 shadow-sm animate-in fade-in duration-200">
              <div className="flex items-start gap-2.5">
                <AlertCircle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-amber-950">Notice</p>
                  <p className="text-amber-800 mt-0.5 leading-relaxed">{errorMessage}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setErrorMessage(null)}
                className="text-amber-500 hover:text-amber-800 p-1 cursor-pointer"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Master Unified Prompt & Creation Canvas */}
          <div className="hero-prompt-box mt-6 mx-auto max-w-3xl text-left">
            <div className="rounded-3xl border border-slate-200/90 bg-white/95 backdrop-blur-sm p-3.5 shadow-xl shadow-slate-200/40 hover:border-[#FFC20E]/70 focus-within:border-[#FFC20E] focus-within:ring-4 focus-within:ring-[#FFC20E]/15 transition-all">
              {/* Active Attachments Tray */}
              {(attachedUrl || customImageFile) && (
                <div className="mb-3 flex flex-wrap items-center gap-2 p-1">
                  {attachedUrl && (
                    <div className="inline-flex items-center gap-2 rounded-xl bg-amber-50 border border-amber-200/80 px-3 py-1.5 text-xs text-amber-950 shadow-2xs max-w-full">
                      <Globe className="h-3.5 w-3.5 text-amber-600 shrink-0" />
                      <span className="font-medium truncate max-w-[150px] sm:max-w-[260px] md:max-w-[320px]" title={attachedUrl}>
                        {attachedUrl}
                      </span>
                      <button
                        type="button"
                        onClick={() => setAttachedUrl('')}
                        className="text-amber-700 hover:text-amber-950 p-0.5 cursor-pointer ml-1 shrink-0"
                        title="Remove link"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  )}

                  {customImageFile && (
                    <div className="inline-flex items-center gap-2 rounded-xl bg-emerald-50 border border-emerald-200/80 px-2.5 py-1 text-xs text-emerald-950 shadow-2xs max-w-full">
                      {customImagePreview && (
                        <img
                          src={customImagePreview}
                          alt="Thumbnail"
                          className="h-6 w-6 rounded-md object-cover border border-emerald-200 shrink-0"
                        />
                      )}
                      <span className="font-medium truncate max-w-[140px] sm:max-w-[220px]" title={customImageFile.name}>
                        {customImageFile.name}
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          setCustomImageFile(null);
                          setCustomImagePreview(null);
                        }}
                        className="text-emerald-700 hover:text-emerald-950 p-0.5 cursor-pointer ml-1 shrink-0"
                        title="Remove image"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Flyout Web Link Input Bar */}
              {showUrlInput && !attachedUrl && (
                <div className="mb-3 flex items-center gap-2 rounded-2xl border border-amber-200 bg-amber-50/60 p-2 text-xs">
                  <LinkIcon className="h-3.5 w-3.5 text-amber-600 ml-1.5 shrink-0" />
                  <input
                    type="url"
                    value={urlInputDraft}
                    onChange={(e) => setUrlInputDraft(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddUrl();
                      }
                    }}
                    placeholder="Paste article, product, or blog URL..."
                    className="w-full bg-transparent px-1.5 py-1 text-xs text-slate-900 placeholder-slate-400 focus:outline-none font-mono"
                    autoFocus
                  />
                  <button
                    type="button"
                    onClick={handleAddUrl}
                    disabled={!urlInputDraft.trim()}
                    className="rounded-xl bg-[#FFC20E] px-3 py-1 font-bold text-slate-950 disabled:opacity-40 cursor-pointer text-[11px]"
                  >
                    Add Link
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowUrlInput(false)}
                    className="text-slate-400 hover:text-slate-600 p-1 cursor-pointer"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              )}

              {/* Textarea Area with Ghost Autocomplete Mirror */}
              <div className="relative">
                <div
                  aria-hidden="true"
                  className="pointer-events-none absolute inset-0 z-0 overflow-hidden p-3.5 text-sm sm:text-base font-normal leading-relaxed whitespace-pre-wrap break-words font-sans"
                >
                  <span className="invisible select-none whitespace-pre-wrap">{prompt}</span>
                  {ghostSuffix && (
                    <span className="text-slate-400 select-none opacity-70 whitespace-pre-wrap animate-in fade-in duration-100 font-sans">
                      {ghostSuffix}
                      <span className="inline-flex items-center ml-2 rounded border border-slate-300/80 bg-slate-100/80 px-1.5 py-0.2 text-[10px] font-mono text-slate-500 opacity-90">
                        Tab ⇥
                      </span>
                    </span>
                  )}
                </div>

                <textarea
                  ref={textareaRef}
                  rows={3}
                  value={prompt}
                  onChange={handlePromptChange}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    customImageFile
                      ? "Describe what to create with this image (e.g. 'create a rabbit near this in the given image', 'place on luxury marble pedestal')..."
                      : attachedUrl
                      ? "Optional: Request a blog summary, executive highlights, or advertising hook for this URL..."
                      : activeFormat === 'video'
                      ? "Describe your short-form video reel ..."
                      : "Describe your campaign idea (e.g. 'Diwali celebration poster', 'AI product launch', 'Bhai Dooj tribute')..."
                  }
                  className="relative z-10 w-full resize-none rounded-2xl bg-transparent p-3.5 text-sm sm:text-base text-slate-900 placeholder-slate-400 focus:outline-none leading-relaxed font-sans"
                />
              </div>

              {/* Hidden File Input for Custom Image Uploads */}
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageFileChange}
                accept="image/png, image/jpeg, image/webp"
                className="hidden"
              />

              {/* Actions & Controls Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-t border-slate-100 pt-3 px-1 sm:px-2">
                <div className="flex flex-wrap items-center gap-2">
                  {/* Attach Web Link Button */}
                  <button
                    type="button"
                    onClick={() => setShowUrlInput((prev) => !prev)}
                    className={`inline-flex items-center gap-1.5 rounded-xl px-2.5 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
                      attachedUrl
                        ? 'bg-amber-100 text-amber-900 border border-amber-300'
                        : 'bg-slate-50 hover:bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-200'
                    }`}
                    title="Attach a webpage URL for Firecrawl scraping and blog generation"
                  >
                    <LinkIcon className="h-3.5 w-3.5 text-amber-500" />
                    <span>{attachedUrl ? 'Link Attached' : 'Attach URL'}</span>
                  </button>

                  {/* Upload Image Button */}
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className={`inline-flex items-center gap-1.5 rounded-xl px-2.5 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
                      customImageFile
                        ? 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                        : 'bg-slate-50 hover:bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-200'
                    }`}
                    title="Upload custom logo, product photo, or person"
                  >
                    <Upload className="h-3.5 w-3.5 text-emerald-500" />
                    <span>{customImageFile ? 'Asset Attached' : 'Add Image'}</span>
                  </button>

                  {/* Aspect Ratio Selector */}
                  <div className="flex items-center gap-1.5">
                    <SlidersHorizontal className="h-3.5 w-3.5 text-slate-400" />
                    <select
                      value={aspectRatio}
                      onChange={(e) => setAspectRatio(e.target.value)}
                      className="rounded-xl border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-700 hover:border-slate-300 focus:border-[#FFC20E] focus:outline-none shadow-2xs"
                    >
                      {aspectRatios.map((ar) => (
                        <option key={ar.value} value={ar.value}>
                          {ar.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Primary Master Action Button */}
                <button
                  type="button"
                  onClick={handleMainGenerate}
                  disabled={isGenerating || (!prompt.trim() && !attachedUrl && !customImageFile)}
                  className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-2xl px-5 sm:px-6 py-2.5 text-xs sm:text-sm font-bold bg-[#FFC20E] hover:bg-[#e6ad0a] text-slate-950 shadow-md shadow-[#FFC20E]/30 transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:scale-102 sm:hover:scale-105 active:scale-95 group cursor-pointer"
                >
                  {activeFormat === 'video' ? (
                    <Video className="h-4 w-4 text-slate-950 transition-transform group-hover:scale-110" />
                  ) : (
                    <Sparkles className="h-4 w-4 transition-transform group-hover:rotate-12" />
                  )}
                  <span>
                    {isGenerating
                      ? activeFormat === 'video'
                        ? 'Synthesizing Reel...'
                        : 'Synthesizing Creative...'
                      : activeFormat === 'video'
                      ? 'Synthesize Video Reel'
                      : attachedUrl
                      ? 'Generate from URL'
                      : customImageFile
                      ? 'Generate with Image'
                      : 'Generate Poster'}
                  </span>
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </button>
              </div>
            </div>

            {/* Dynamic Live Google Calendar Inspirations (Top 5 Nearest Festivals) */}
            <div className="mt-4 space-y-2 text-left">
              <div className="flex items-center gap-1.5 text-slate-700 text-xs font-bold">
                <Calendar className="h-3.5 w-3.5 text-amber-600" />
                <span>Upcoming Occasions (Auto-Calendar):</span>
                <button
                  type="button"
                  onClick={fetchCalendarInspirations}
                  title="Reload from Google Calendar"
                  className="ml-1 rounded-full border border-slate-200 bg-white p-1 text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors cursor-pointer"
                >
                  <RotateCw className={`h-3 w-3 ${isLoadingCalendar ? 'animate-spin text-amber-600' : ''}`} />
                </button>
              </div>

              {/* Top 5 Chips List */}
              <div className="flex flex-wrap items-center gap-2 text-xs pt-0.5">
                {calendarOccasions.slice(0, 5).map((occ) => (
                  <button
                    key={occ.id}
                    type="button"
                    onClick={() => {
                      const autoPrompt = activeFormat === 'video'
                        ? (occ.video_prompt || occ.prompt.replace(/\bposter\b/gi, 'video'))
                        : (occ.poster_prompt || occ.prompt);
                      setPrompt(autoPrompt);
                      setGhostSuffix('');
                      if (textareaRef.current) textareaRef.current.focus();
                    }}
                    title={`Click to draft creative for ${occ.name} (${occ.formatted_date})`}
                    className="hero-chip group rounded-full border border-slate-200 bg-white px-3.5 py-1 text-[11px] font-medium text-slate-700 hover:border-[#FFC20E] hover:bg-amber-50 hover:text-amber-950 transition-all shadow-2xs hover:scale-105 cursor-pointer flex items-center gap-1.5"
                  >
                    <span>{occ.name}</span>
                    {occ.time_tag && (
                      <span className="rounded-full bg-amber-100 text-amber-900 px-1.5 py-0.2 text-[9px] font-bold">
                        {occ.time_tag}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Live Staged Progress Loader with GSAP Timeline */}
        {isGenerating && (
          <div className="mt-8 mx-auto max-w-2xl rounded-3xl border border-amber-300 bg-gradient-to-b from-amber-50 to-white p-6 text-left shadow-2xl backdrop-blur-md animate-in fade-in zoom-in-95 duration-300">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="relative flex h-8 w-8 items-center justify-center rounded-xl bg-amber-100 text-amber-700">
                  <Sparkles className="h-4 w-4 animate-spin" />
                  <span className="absolute -inset-1 rounded-xl bg-amber-400/20 animate-ping" />
                </div>
                <div>
                  <h4 className="text-sm font-black text-slate-900">
                    {activeFormat === 'video' ? 'Synthesizing Actionable Video Reel' : 'Crafting Branded Visual Asset'}
                  </h4>
                  <p className="text-[11px] text-slate-500">Executing multi-stage neural rendering pipeline</p>
                </div>
              </div>
              <span className="rounded-full bg-amber-100 border border-amber-300 px-3 py-1 text-xs font-bold text-amber-900">
                Stage {generationStage} of 3
              </span>
            </div>

            <div className="h-2 w-full rounded-full bg-amber-100/70 overflow-hidden mb-5">
              <div
                ref={progressLineRef}
                className="h-full rounded-full bg-gradient-to-r from-amber-500 to-[#FFC20E] shadow-sm transition-all duration-700"
              />
            </div>

            <div className="space-y-3">
              <div className={`flex items-center gap-3 text-xs transition-all ${generationStage >= 1 ? 'text-slate-900 font-bold' : 'text-slate-400'}`}>
                <div className={`h-3 w-3 rounded-full flex items-center justify-center ${generationStage >= 1 ? 'bg-[#FFC20E] text-slate-950 font-bold text-[9px]' : 'bg-slate-200'}`}>
                  {generationStage > 1 ? '✓' : '1'}
                </div>
                <span>Synthesizing Cultural Hook, Caption & Brand Narrative</span>
              </div>
              <div className={`flex items-center gap-3 text-xs transition-all ${generationStage >= 2 ? 'text-slate-900 font-bold' : 'text-slate-400'}`}>
                <div className={`h-3 w-3 rounded-full flex items-center justify-center ${generationStage >= 2 ? 'bg-[#FFC20E] text-slate-950 font-bold text-[9px]' : 'bg-slate-200'}`}>
                  {generationStage > 2 ? '✓' : '2'}
                </div>
                <span>
                  {activeFormat === 'video'
                    ? 'Synthesizing Actionable Motion Reel & Cinematic Camera'
                    : 'Diffusing Photorealistic Visual Backdrop with Generative AI'}
                </span>
              </div>
              <div className={`flex items-center gap-3 text-xs transition-all ${generationStage >= 3 ? 'text-slate-900 font-bold' : 'text-slate-400'}`}>
                <div className={`h-3 w-3 rounded-full flex items-center justify-center ${generationStage >= 3 ? 'bg-[#FFC20E] text-slate-950 font-bold text-[9px]' : 'bg-slate-200'}`}>
                  3
                </div>
                <span>Compositing Golden-Ratio Typography, Quotes & 42 WORKS Logo</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Review & Social Dispatch Modal */}
      {selectedPoster && (
        <ReviewModal
          key={selectedPoster.id}
          poster={selectedPoster}
          isOpen={reviewModalOpen}
          onClose={() => setReviewModalOpen(false)}
          onUpdated={(updated) => {
            setSelectedPoster(updated);
          }}
          initialTab={modalInitialTab}
          initialVideoUrl={modalInitialVideoUrl}
          initialVideoModel={modalInitialVideoModel}
        />
      )}
    </div>
  );
};

export default StudioPage;
