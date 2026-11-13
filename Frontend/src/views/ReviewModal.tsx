import React, { useState, useEffect, useRef } from 'react';
import type { Poster } from '../types';
import { apiClient } from '../api/client';
import gsap from 'gsap';
import {
  X,
  CheckCircle2,
  Calendar,
  Send,
  Copy,
  Check,
  RefreshCw,
  Eye,
  Download,
  AlertCircle,
  Clock,
  Sparkles,
  Trash2,
  Move,
  Maximize2,
  RotateCcw,
  RotateCw,
  Video,
  Play,
  Loader2,
  Palette,
  Sun,
  Moon,
} from 'lucide-react';
import { LinkedinIcon, InstagramIcon } from '../components/SocialIcons';

const getCleanErrorMessage = (err: any, fallback: string): string => {
  console.error('Error details (developer console):', err);
  const detail = err.response?.data?.detail;
  if (typeof detail === 'string') {
    const lower = detail.toLowerCase();
    if (
      lower.includes('traceback') ||
      lower.includes('https://') ||
      lower.includes('client error') ||
      lower.includes('status code') ||
      lower.includes('internalservererror')
    ) {
      return fallback;
    }
    return detail;
  }
  return fallback;
};

interface ReviewModalProps {
  poster: Poster;
  isOpen: boolean;
  onClose: () => void;
  onUpdated: (updated: Poster) => void;
  onDeleted?: (posterId: number) => void;
  initialTab?: 'poster' | 'linkedin' | 'instagram' | 'video';
  initialVideoUrl?: string | null;
  initialVideoModel?: string;
}

export const ReviewModal: React.FC<ReviewModalProps> = ({
  poster,
  isOpen,
  onClose,
  onUpdated,
  onDeleted,
  initialTab,
  initialVideoUrl,
  initialVideoModel: _initialVideoModel,
}) => {
  const [currentPoster, setCurrentPoster] = useState<Poster>(poster);
  const [viewArtOnly, setViewArtOnly] = useState(false);
  const [copiedCaption, setCopiedCaption] = useState(false);
  const modalCardRef = useRef<HTMLDivElement>(null);

  // Smooth GSAP reveal on modal open
  useEffect(() => {
    if (isOpen && modalCardRef.current) {
      gsap.fromTo(
        modalCardRef.current,
        { scale: 0.94, opacity: 0, y: 14 },
        { scale: 1, opacity: 1, y: 0, duration: 0.35, ease: 'power3.out' }
      );
    }
  }, [isOpen]);

  // Helper parsers to ensure quotes and hashtags always format cleanly
  const cleanQuoteText = (q?: string | null): string => {
    if (!q) return '';
    return q.trim().replace(/^["'“”]+|["'“”]+$/g, '').trim();
  };

  // Resolves quote from poster.quote, poster.story_quote, or extracts an inspiring line from caption
  const resolveQuote = (p: Poster): string => {
    const raw = (p as any).quote || (p as any).story_quote;
    if (raw && cleanQuoteText(raw)) {
      return cleanQuoteText(raw);
    }
    // Extract first meaningful reflection sentence from caption if quote is blank
    if (p.caption) {
      const sentences = p.caption
        .split(/[.!?\n]/)
        .map((s) => s.trim())
        .filter((s) => s.length > 15 && s.length < 130 && !s.startsWith('#'));
      if (sentences.length > 0) {
        return cleanQuoteText(sentences[0]);
      }
    }
    return 'Where shadows fade, eternal light and wisdom begin.';
  };

  const parseHashtagsList = (tags: any): string[] => {
    if (Array.isArray(tags)) {
      return tags.map((t) => (t.startsWith('#') ? t : `#${t}`));
    }
    if (typeof tags === 'string') {
      try {
        const parsed = JSON.parse(tags);
        if (Array.isArray(parsed)) {
          return parsed.map((t) => (t.startsWith('#') ? t : `#${t}`));
        }
      } catch {
        return tags.split(/\s+/).filter(Boolean).map((t) => (t.startsWith('#') ? t : `#${t}`));
      }
    }
    return [];
  };

  // In-place edit state
  const [headline, setHeadline] = useState(poster.headline);
  const [quote, setQuote] = useState(resolveQuote(poster));
  const [caption, setCaption] = useState(poster.caption);
  const [hashtagsText, setHashtagsText] = useState(parseHashtagsList(poster.hashtags).join(' '));
  const [isRecomposing, setIsRecomposing] = useState(false);
  const [recomposeSuccess, setRecomposeSuccess] = useState(false);
  const [isSavingCopy, setIsSavingCopy] = useState(false);
  const [copySavedSuccess, setCopySavedSuccess] = useState(false);

  // Video Reel Generation State (Wan 2.1 / Wan 2.2)
  const effectiveVideoUrl = poster.video_url || initialVideoUrl || null;
  const isVideoPrompt = Boolean(
    (poster.prompt || '').toLowerCase().includes('video') ||
    (poster.prompt || '').toLowerCase().includes('reel')
  );

  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
  const [generatedVideoUrl, setGeneratedVideoUrl] = useState<string | null>(effectiveVideoUrl);

  useEffect(() => {
    const vUrl = poster.video_url || initialVideoUrl || null;
    if (vUrl) {
      setGeneratedVideoUrl(vUrl);
      setSocialMediaType('video');
    }
  }, [poster.video_url, initialVideoUrl]);

  // Unified Typography State (Headline & Quotes positioned in AI-analyzed safe space)
  const initialY = typeof poster.layout_meta?.y === 'number' ? poster.layout_meta.y : 16;
  const [textPos, setTextPos] = useState<{ x: number; y: number }>({ x: 50, y: initialY });
  const [textWidth, setTextWidth] = useState<number>(82); // Horizontal stretch (40% to 96%)
  const [textScale, setTextScale] = useState<number>(1.0); // Overall proportional scale (0.6 to 1.7)
  const [textRotation, setTextRotation] = useState<number>(0); // Rotation degrees (-180 to 180)
  const [textGap, setTextGap] = useState<number>(14); // Vertical spacing between headline & quote

  // Typography Color State (for contrast & visibility on any image/video background)
  const [headlineColor, setHeadlineColor] = useState<string>('#FFFFFF');
  const [quoteColor, setQuoteColor] = useState<string>('#FFDF0F');
  const [accentColor, setAccentColor] = useState<string>('#DFB876');

  type TransformAction = 'drag' | 'rotate' | 'stretch-e' | 'stretch-w' | 'stretch-n' | 'stretch-s' | 'scale-corner';
  const [activeAction, setActiveAction] = useState<TransformAction | null>(null);

  const posterFrameRef = useRef<HTMLDivElement>(null);
  const videoFrameRef = useRef<HTMLDivElement>(null);
  const [videoEditMode, setVideoEditMode] = useState<boolean>(false);
  const textBoxRef = useRef<HTMLDivElement>(null);
  const activeActionRef = useRef<TransformAction | null>(null);
  const actionStartRef = useRef<{
    startX: number;
    startY: number;
    startWidth: number;
    startScale: number;
    startGap: number;
    startPosX: number;
    startPosY: number;
  }>({
    startX: 0,
    startY: 0,
    startWidth: 82,
    startScale: 1.0,
    startGap: 14,
    startPosX: 50,
    startPosY: 46,
  });

  const handleActionStart = (action: TransformAction, e: React.MouseEvent | React.TouchEvent) => {
    e.stopPropagation();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    activeActionRef.current = action;
    setActiveAction(action);
    actionStartRef.current = {
      startX: clientX,
      startY: clientY,
      startWidth: textWidth,
      startScale: textScale,
      startGap: textGap,
      startPosX: textPos.x,
      startPosY: textPos.y,
    };
  };

  const handleResetCenter = () => {
    const safeY = typeof currentPoster.layout_meta?.y === 'number' ? currentPoster.layout_meta.y : 16;
    setTextPos({ x: 50, y: safeY });
    setTextWidth(82);
    setTextScale(1.0);
    setTextRotation(0);
    setTextGap(14);
    setHeadlineColor(currentPoster.layout_meta?.headline_color || '#FFFFFF');
    setQuoteColor(currentPoster.layout_meta?.quote_color || '#FFDF0F');
    setAccentColor(currentPoster.layout_meta?.accent_color || '#DFB876');
    try {
      localStorage.removeItem(`poster_layout_${currentPoster.id}`);
    } catch {}
  };

  useEffect(() => {
    const handleMove = (e: MouseEvent | TouchEvent) => {
      const activeFrame = previewTab === 'video'
        ? (videoFrameRef.current || posterFrameRef.current)
        : (posterFrameRef.current || videoFrameRef.current);
      if (!activeActionRef.current || !activeFrame) return;
      const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
      const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
      const rect = activeFrame.getBoundingClientRect();
      const action = activeActionRef.current;

      if (action === 'drag') {
        const xPercent = Math.max(15, Math.min(85, ((clientX - rect.left) / rect.width) * 100));
        const yPercent = Math.max(10, Math.min(90, ((clientY - rect.top) / rect.height) * 100));
        setTextPos({ x: Math.round(xPercent), y: Math.round(yPercent) });
      } else if (action === 'rotate' && textBoxRef.current) {
        const boxRect = textBoxRef.current.getBoundingClientRect();
        const centerX = boxRect.left + boxRect.width / 2;
        const centerY = boxRect.top + boxRect.height / 2;
        const radians = Math.atan2(clientY - centerY, clientX - centerX);
        let deg = Math.round((radians * 180) / Math.PI) + 90;
        if (deg > 180) deg -= 360;
        if (deg < -180) deg += 360;
        if (Math.abs(deg) <= 3) deg = 0; // Snap to 0 within 3 degrees
        setTextRotation(deg);
      } else if (action === 'stretch-e' || action === 'stretch-w') {
        const deltaX = clientX - actionStartRef.current.startX;
        const sign = action === 'stretch-e' ? 1 : -1;
        const deltaPercent = ((deltaX * sign * 2) / rect.width) * 100;
        const newWidth = Math.max(40, Math.min(96, Math.round(actionStartRef.current.startWidth + deltaPercent)));
        setTextWidth(newWidth);
      } else if (action === 'stretch-s' || action === 'stretch-n') {
        const deltaY = clientY - actionStartRef.current.startY;
        const sign = action === 'stretch-s' ? 1 : -1;
        const change = (deltaY * sign) / 4;
        const newGap = Math.max(4, Math.min(48, Math.round(actionStartRef.current.startGap + change)));
        setTextGap(newGap);
      } else if (action === 'scale-corner') {
        const deltaX = clientX - actionStartRef.current.startX;
        const deltaY = clientY - actionStartRef.current.startY;
        const delta = (deltaX + deltaY) / 2;
        const scaleChange = delta / 110;
        const newScale = Math.max(0.6, Math.min(1.7, Number((actionStartRef.current.startScale + scaleChange).toFixed(2))));
        setTextScale(newScale);
      }
    };

    const handleEnd = () => {
      activeActionRef.current = null;
      setActiveAction(null);
    };

    window.addEventListener('mousemove', handleMove);
    window.addEventListener('mouseup', handleEnd);
    window.addEventListener('touchmove', handleMove);
    window.addEventListener('touchend', handleEnd);

    return () => {
      window.removeEventListener('mousemove', handleMove);
      window.removeEventListener('mouseup', handleEnd);
      window.removeEventListener('touchmove', handleMove);
      window.removeEventListener('touchend', handleEnd);
    };
  }, []);

  const lastPosterIdRef = useRef<number | null>(null);

  // Sync internal state only when opening modal or selecting a new poster
  useEffect(() => {
    if (!isOpen) {
      lastPosterIdRef.current = null;
      return;
    }

    setCurrentPoster(poster);
    const isNewPoster = lastPosterIdRef.current !== poster.id;
    if (isNewPoster) {
      lastPosterIdRef.current = poster.id;
      setHeadline(poster.headline);
      setQuote(resolveQuote(poster));

      // Restore saved layout (from poster.layout_meta or localStorage)
      let savedLayout = poster.layout_meta;
      if (!savedLayout || typeof savedLayout.y !== 'number') {
        try {
          const raw = localStorage.getItem(`poster_layout_${poster.id}`);
          if (raw) savedLayout = JSON.parse(raw);
        } catch {}
      }

      if (savedLayout && typeof savedLayout.y === 'number') {
        setTextPos({ x: savedLayout.x ?? 50, y: savedLayout.y });
        setTextWidth(savedLayout.width ?? 82);
        setTextScale(savedLayout.scale ?? 1.0);
        setTextRotation(savedLayout.rotation ?? 0);
        setTextGap(savedLayout.gap ?? 14);
        setHeadlineColor(savedLayout.headline_color || '#FFFFFF');
        setQuoteColor(savedLayout.quote_color || '#FFDF0F');
        setAccentColor(savedLayout.accent_color || '#DFB876');
      } else {
        const safeY = typeof poster.layout_meta?.y === 'number' ? poster.layout_meta.y : 16;
        setTextPos({ x: 50, y: safeY });
        setTextWidth(82);
        setTextScale(1.0);
        setTextRotation(0);
        setTextGap(14);
        setHeadlineColor(poster.layout_meta?.headline_color || '#FFFFFF');
        setQuoteColor(poster.layout_meta?.quote_color || '#FFDF0F');
        setAccentColor(poster.layout_meta?.accent_color || '#DFB876');
      }

      setCaption(poster.caption);
      setHashtagsText(parseHashtagsList(poster.hashtags).join(' '));
      setViewArtOnly(false);
      const hasVideo = Boolean(poster.video_url || initialVideoUrl);
      const defaultTab = initialTab || (hasVideo || isVideoPrompt ? 'video' : 'poster');
      setPreviewTab(defaultTab);
      if (hasVideo) {
        setSocialMediaType('video');
      }
      setDispatchError(null);
      setDispatchSuccessMsg(null);
    }
  }, [poster.id, poster.video_url, isOpen]);

  // Approval state
  const [isApproving, setIsApproving] = useState(false);

  // Social dispatch state
  const [dispatchPlatform, setDispatchPlatform] = useState<'linkedin' | 'instagram'>('linkedin');
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [scheduleDateTime, setScheduleDateTime] = useState('');
  const [dispatching, setDispatching] = useState(false);
  const [dispatchSuccessMsg, setDispatchSuccessMsg] = useState<string | null>(null);
  const [dispatchError, setDispatchError] = useState<string | null>(null);
  const [isUnlocking, setIsUnlocking] = useState(false);
  const [editMode, setEditMode] = useState(true);
  const [socialMediaType, setSocialMediaType] = useState<'video' | 'image'>(
    poster.video_url || initialVideoUrl || isVideoPrompt ? 'video' : 'image'
  );

  // Social Preview tab
  const [previewTab, setPreviewTab] = useState<'poster' | 'linkedin' | 'instagram' | 'video'>(
    initialTab || (poster.video_url || initialVideoUrl || isVideoPrompt ? 'video' : 'poster')
  );

  useEffect(() => {
    if (initialTab) {
      setPreviewTab(initialTab);
    }
    if (initialVideoUrl) {
      setSocialMediaType('video');
    }
  }, [initialTab, initialVideoUrl]);

  const hasCleanBackground = Boolean(
    currentPoster.background_image_url &&
    (currentPoster.background_image_url.includes('background') || currentPoster.background_image_url !== currentPoster.final_poster_url)
  );

  const isPublished = String(currentPoster.status).toLowerCase() === 'published';

  const resolveEventTagline = (p: typeof currentPoster) => {
    if (p.layout_meta && typeof p.layout_meta === 'object' && 'sub_tagline' in p.layout_meta && p.layout_meta.sub_tagline) {
      return `—   ${String(p.layout_meta.sub_tagline).split(/\s+/).join('   ')}   —`;
    }
    const combined = ((p.prompt || '') + ' ' + (p.headline || '')).toLowerCase();
    if (combined.includes('karwa') || combined.includes('karva')) return '—   K A R W A   C H A U T H   •   2 0 2 6   —';
    if (combined.includes('chhath') || combined.includes('chhat') || combined.includes('surya')) return '—   C H H A T H   P U J A   •   2 0 2 6   —';
    if (combined.includes('diwali') || combined.includes('deepawali') || combined.includes('dhanteras')) return '—   D E E P A W A L I   •   2 0 2 6   —';
    if (combined.includes('bhai')) return '—   B H A I   D O O J   •   2 0 2 6   —';
    if (combined.includes('christmas')) return '—   C H R I S T M A S   •   2 0 2 6   —';
    if (combined.includes('new year')) return '—   N E W   Y E A R   •   2 0 2 6   —';
    if (combined.includes('halloween')) return '—   H A L L O W E E N   •   2 0 2 6   —';
    return '—   4 2   W O R K S   •   2 0 2 6   —';
  };

  const eventTagline = resolveEventTagline(currentPoster);

  if (!isOpen) return null;

  // Re-composite typography and persist all edits to database
  const handleRecomposite = async () => {
    setIsRecomposing(true);
    setRecomposeSuccess(false);
    try {
      const tags = hashtagsText
        .split(/\s+/)
        .map((t) => t.trim())
        .filter((t) => t.length > 0)
        .map((t) => (t.startsWith('#') ? t : `#${t}`));

      const layoutPayload = {
        x: textPos.x,
        y: textPos.y,
        width: textWidth,
        scale: textScale,
        rotation: textRotation,
        gap: textGap,
        headline_color: headlineColor,
        quote_color: quoteColor,
        accent_color: accentColor,
      };

      try {
        localStorage.setItem(`poster_layout_${currentPoster.id}`, JSON.stringify(layoutPayload));
      } catch {}

      const editPromise = apiClient.post<Poster>(`/reviews/${currentPoster.id}/edit`, {
        headline,
        headline_y_ratio: Math.max(0.12, (textPos.y - 7) / 100),
        headline_scale: textScale,
        quote,
        quote_y_ratio: Math.min(0.88, (textPos.y + 11) / 100),
        quote_scale: textScale,
        caption: caption.trim(),
        hashtags: tags,
        layout_meta: layoutPayload,
        primary_color: accentColor,
        secondary_color: headlineColor,
        quote_color: quoteColor,
      });

      const shouldSyncVideo = Boolean(previewTab === 'video' || socialMediaType === 'video' || generatedVideoUrl || currentPoster.video_url);

      const videoPromise = shouldSyncVideo
        ? apiClient.post<any>('/videos/from-poster', {
            poster_id: currentPoster.id,
            duration_seconds: 14,
            headline,
            quote,
            headline_color: headlineColor,
            quote_color: quoteColor,
            accent_color: accentColor,
            y_percent: textPos.y,
            scale: textScale,
            rotation: textRotation,
            skip_diffusion: true,
          })
        : Promise.resolve(null);

      const [res, vidRes] = await Promise.all([editPromise, videoPromise]);
      const cacheBuster = `?t=${Date.now()}`;
      const freshPosterUrl = res.data.final_poster_url ? `${res.data.final_poster_url.split('?')[0]}${cacheBuster}` : res.data.final_poster_url;
      const freshVideoUrl = vidRes?.data?.video_url ? `${vidRes.data.video_url.split('?')[0]}${cacheBuster}` : (res.data.video_url ? `${res.data.video_url.split('?')[0]}${cacheBuster}` : null);

      const mergedPoster: Poster = {
        ...res.data,
        final_poster_url: freshPosterUrl,
        video_url: freshVideoUrl || (generatedVideoUrl ? `${generatedVideoUrl.split('?')[0]}${cacheBuster}` : null),
      };
      if (freshVideoUrl) {
        setGeneratedVideoUrl(freshVideoUrl);
      }
      setCurrentPoster(mergedPoster);
      onUpdated(mergedPoster);
      setVideoEditMode(false);
      setRecomposeSuccess(true);
      setTimeout(() => setRecomposeSuccess(false), 2500);
    } catch (err: any) {
      alert(getCleanErrorMessage(err, 'Failed to save changes and re-composite typography. Please try again.'));
    } finally {
      setIsRecomposing(false);
    }
  };

  // Save as PNG: re-composites with latest coordinates and scales, then downloads high-res PNG
  const handleDownloadPNG = async (e?: React.MouseEvent) => {
    if (e) e.preventDefault();
    try {
      const tags = hashtagsText
        .split(/\s+/)
        .map((t) => t.trim())
        .filter((t) => t.length > 0)
        .map((t) => (t.startsWith('#') ? t : `#${t}`));

      const layoutPayload = {
        x: textPos.x,
        y: textPos.y,
        width: textWidth,
        scale: textScale,
        rotation: textRotation,
        gap: textGap,
        headline_color: headlineColor,
        quote_color: quoteColor,
        accent_color: accentColor,
      };

      try {
        localStorage.setItem(`poster_layout_${currentPoster.id}`, JSON.stringify(layoutPayload));
      } catch {}

      const res = await apiClient.post<Poster>(`/reviews/${currentPoster.id}/edit`, {
        headline,
        headline_y_ratio: Math.max(0.12, (textPos.y - 7) / 100),
        headline_scale: textScale,
        quote,
        quote_y_ratio: Math.min(0.88, (textPos.y + 11) / 100),
        quote_scale: textScale,
        caption: caption.trim(),
        hashtags: tags,
        layout_meta: layoutPayload,
        primary_color: accentColor,
        secondary_color: headlineColor,
        quote_color: quoteColor,
      });
      const mergedPoster: Poster = {
        ...res.data,
        video_url: res.data.video_url || generatedVideoUrl || currentPoster.video_url,
      };
      setCurrentPoster(mergedPoster);
      onUpdated(mergedPoster);

      const link = document.createElement('a');
      link.href = res.data.final_poster_url;
      link.download = `poster_${currentPoster.id}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch {
      const link = document.createElement('a');
      link.href = currentPoster.final_poster_url;
      link.download = `poster_${currentPoster.id}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  // Save Social Caption & Hashtags changes
  const handleSaveSocialCopy = async () => {
    setIsSavingCopy(true);
    setCopySavedSuccess(false);
    try {
      const tags = hashtagsText
        .split(/\s+/)
        .filter((t) => t.trim().length > 0)
        .map((t) => (t.startsWith('#') ? t : `#${t}`));

      const layoutPayload = {
        x: textPos.x,
        y: textPos.y,
        width: textWidth,
        scale: textScale,
        rotation: textRotation,
        gap: textGap,
        headline_color: headlineColor,
        quote_color: quoteColor,
        accent_color: accentColor,
      };

      try {
        localStorage.setItem(`poster_layout_${currentPoster.id}`, JSON.stringify(layoutPayload));
      } catch {}

      const res = await apiClient.post<Poster>(`/reviews/${currentPoster.id}/edit`, {
        headline,
        headline_y_ratio: Math.max(0.12, (textPos.y - 7) / 100),
        headline_scale: textScale,
        quote,
        quote_y_ratio: Math.min(0.88, (textPos.y + 11) / 100),
        quote_scale: textScale,
        caption: caption.trim(),
        hashtags: tags,
        layout_meta: layoutPayload,
        primary_color: accentColor,
        secondary_color: headlineColor,
        quote_color: quoteColor,
      });
      const mergedPoster: Poster = {
        ...res.data,
        video_url: res.data.video_url || generatedVideoUrl || currentPoster.video_url,
      };
      setCurrentPoster(mergedPoster);
      onUpdated(mergedPoster);
      setCopySavedSuccess(true);
      setTimeout(() => setCopySavedSuccess(false), 2500);
    } catch (err: any) {
      alert(getCleanErrorMessage(err, 'Failed to update caption and hashtags. Please try again.'));
    } finally {
      setIsSavingCopy(false);
    }
  };

  // Approve and lock
  const handleApprove = async () => {
    setIsApproving(true);
    try {
      await apiClient.post(`/reviews/${currentPoster.id}/approve`, {
        reviewer_id: 1,
      });
      const updated: Poster = { ...currentPoster, status: 'approved' };
      setCurrentPoster(updated);
      onUpdated(updated);
    } catch (err: any) {
      alert(getCleanErrorMessage(err, 'Failed to approve poster. Please try again.'));
    } finally {
      setIsApproving(false);
    }
  };

  // Unlock poster for editing
  const handleUnlock = async () => {
    setIsUnlocking(true);
    try {
      await apiClient.post(`/reviews/${currentPoster.id}/unlock`);
      const updated: Poster = { ...currentPoster, status: 'in_review' };
      setCurrentPoster(updated);
      onUpdated(updated);
      setDispatchSuccessMsg('Poster unlocked. You can now make typography and copy revisions.');
      setTimeout(() => setDispatchSuccessMsg(null), 3500);
    } catch (err: any) {
      alert(getCleanErrorMessage(err, 'Failed to unlock poster. Please try again.'));
    } finally {
      setIsUnlocking(false);
    }
  };

  // Delete or Archive poster
  const handleDeletePoster = async () => {
    if (currentPoster.status === 'published') {
      const confirmed = confirm(
        'This poster was already published to social media.\n\nIt will be moved to the Published Vault to keep your active studio clean, while preserving your AI Knowledge Graph and Admin metrics.\n\nMove to Published Vault?'
      );
      if (!confirmed) return;
    } else {
      const confirmed = confirm('Are you sure you want to permanently delete this unpublished draft?');
      if (!confirmed) return;
    }

    try {
      const forceHardDelete = currentPoster.status !== 'published';
      await apiClient.delete(`/posters/${currentPoster.id}?force_hard_delete=${forceHardDelete}`);
      if (onDeleted) {
        onDeleted(currentPoster.id);
      }
      onClose();
    } catch (err: any) {
      if (err.response?.status === 404) {
        if (onDeleted) {
          onDeleted(currentPoster.id);
        }
        onClose();
      } else {
        alert(getCleanErrorMessage(err, 'Failed to process request. Please try again.'));
      }
    }
  };

  // Immediate Publish (LinkedIn or Instagram)
  const handlePublishNow = async (platform: 'linkedin' | 'instagram') => {
    if (currentPoster.status !== 'approved' && currentPoster.status !== 'scheduled' && currentPoster.status !== 'published') {
      alert('Please approve and lock this poster before publishing to social media.');
      return;
    }

    setDispatching(true);
    setDispatchError(null);
    setDispatchSuccessMsg(null);
    try {
      const mediaUrlToDispatch =
        socialMediaType === 'video' && generatedVideoUrl ? generatedVideoUrl : currentPoster.final_poster_url;
      const res = await apiClient.post<any>(`/schedules/${currentPoster.id}`, {
        platform,
        post_now: true,
        media_url: mediaUrlToDispatch,
      });

      if (res.data?.status === 'failed') {
        setDispatchError(res.data.error_message || `Failed to publish to ${platform}.`);
        return;
      }

      const updated: Poster = { ...currentPoster, status: 'published' };
      setCurrentPoster(updated);
      onUpdated(updated);
      setDispatchSuccessMsg(`Successfully published to ${platform === 'linkedin' ? 'LinkedIn' : 'Instagram Feed'}!`);
      setTimeout(() => setDispatchSuccessMsg(null), 4000);
    } catch (err: any) {
      setDispatchError(err.response?.data?.detail || `Failed to publish to ${platform}.`);
    } finally {
      setDispatching(false);
    }
  };

  // Scheduled Dispatch (Like Gmail Schedule Send)
  const handleScheduleSend = async () => {
    if (currentPoster.status !== 'approved' && currentPoster.status !== 'scheduled' && currentPoster.status !== 'published') {
      alert('Please approve and lock this poster before scheduling.');
      return;
    }
    if (!scheduleDateTime) {
      alert('Please choose a valid date and time for scheduled dispatch.');
      return;
    }

    setDispatching(true);
    setDispatchError(null);
    try {
      const mediaUrlToDispatch =
        socialMediaType === 'video' && generatedVideoUrl ? generatedVideoUrl : currentPoster.final_poster_url;
      await apiClient.post(`/schedules/${currentPoster.id}`, {
        platform: dispatchPlatform,
        post_now: false,
        scheduled_for: new Date(scheduleDateTime).toISOString(),
        media_url: mediaUrlToDispatch,
      });
      const updated: Poster = { ...currentPoster, status: 'scheduled' };
      setCurrentPoster(updated);
      onUpdated(updated);
      setScheduleModalOpen(false);
      setDispatchSuccessMsg(`Scheduled to publish on ${dispatchPlatform.toUpperCase()} at ${new Date(scheduleDateTime).toLocaleString()}`);
      setTimeout(() => setDispatchSuccessMsg(null), 5000);
    } catch (err: any) {
      setDispatchError(err.response?.data?.detail || 'Failed to schedule publication.');
    } finally {
      setDispatching(false);
    }
  };

  const copyCaptionToClipboard = () => {
    const fullText = `${caption}\n\n${hashtagsText}`;
    navigator.clipboard.writeText(fullText);
    setCopiedCaption(true);
    setTimeout(() => setCopiedCaption(false), 2000);
  };

  const isApproved = currentPoster.status === 'approved' || currentPoster.status === 'published';

  // Generate Video Reel using Wan 2.1 / Wan 2.2
  const handleGenerateVideoReel = async () => {
    if (isGeneratingVideo) return;
    setIsGeneratingVideo(true);
    setDispatchError(null);
    try {
      const res = await apiClient.post<any>('/videos/from-poster', {
        poster_id: currentPoster.id,
        duration_seconds: 14,
        headline,
        quote,
        headline_color: headlineColor,
        quote_color: quoteColor,
        accent_color: accentColor,
        y_percent: textPos.y,
        scale: textScale,
        rotation: textRotation,
        skip_diffusion: Boolean(generatedVideoUrl),
      });
      const cacheBuster = `?t=${Date.now()}`;
      const freshVid = `${res.data.video_url.split('?')[0]}${cacheBuster}`;
      setGeneratedVideoUrl(freshVid);
      setPreviewTab('video');
      setSocialMediaType('video');
      const updatedPoster = { ...currentPoster, video_url: freshVid };
      setCurrentPoster(updatedPoster);
      onUpdated(updatedPoster);
      setDispatchSuccessMsg('Video reel synchronized with latest typography and colors!');
      setTimeout(() => setDispatchSuccessMsg(null), 4000);
    } catch (err: any) {
      alert(getCleanErrorMessage(err, 'Failed to generate video reel. Please try again in a moment.'));
    } finally {
      setIsGeneratingVideo(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-2 sm:p-4 md:p-6 overflow-y-auto">
      <div
        ref={modalCardRef}
        className="relative w-full max-w-6xl rounded-2xl sm:rounded-3xl border border-slate-200 bg-white shadow-2xl flex flex-col max-h-[96vh] sm:max-h-[92vh] overflow-hidden will-change-transform"
      >
        {/* Top Header - Fully Responsive */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 px-3 sm:px-6 py-3 bg-slate-50/90 gap-2.5">
          <div className="flex items-center justify-between sm:justify-start gap-2 min-w-0">
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] sm:text-xs font-semibold uppercase tracking-wider shrink-0 ${
                isApproved
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-amber-50 text-amber-800 border border-amber-200'
              }`}
            >
              {currentPoster.status.replace('_', ' ')}
            </span>
            <span className="text-xs sm:text-sm font-medium text-slate-600 truncate max-w-[170px] xs:max-w-[220px] sm:max-w-xs md:max-w-md">
              {currentPoster.prompt}
            </span>

            {/* Mobile Actions: Delete & Close in header */}
            <div className="flex sm:hidden items-center gap-1 shrink-0 ml-auto">
              <button
                onClick={handleDeletePoster}
                title="Delete Poster"
                className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition-colors"
              >
                <Trash2 className="h-4 w-4" />
              </button>
              <button
                onClick={onClose}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
              >
                <X className="h-4.5 w-4.5" />
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between sm:justify-end gap-2 overflow-x-auto no-scrollbar w-full sm:w-auto">
            {/* View Mode Switcher */}
            <div className="flex items-center rounded-xl bg-slate-100 p-0.5 sm:p-1 border border-slate-200 shrink-0 w-full sm:w-auto justify-between sm:justify-start">
              <button
                onClick={() => setPreviewTab('poster')}
                className={`rounded-lg px-2 sm:px-3 py-1 text-[11px] sm:text-xs font-semibold transition-all ${
                  previewTab === 'poster'
                    ? 'bg-white text-slate-900 shadow-xs border border-slate-200/80 font-bold'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                Poster Canvas
              </button>
              <button
                onClick={() => setPreviewTab('linkedin')}
                className={`flex items-center gap-1 rounded-lg px-2 sm:px-3 py-1 text-[11px] sm:text-xs font-semibold transition-all ${
                  previewTab === 'linkedin'
                    ? 'bg-[#0077b5] text-white shadow-xs font-bold'
                    : 'text-slate-500 hover:text-[#0077b5]'
                }`}
              >
                <LinkedinIcon className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                <span className="hidden xs:inline">LinkedIn</span>
              </button>
              <button
                onClick={() => setPreviewTab('instagram')}
                className={`flex items-center gap-1 rounded-lg px-2 sm:px-3 py-1 text-[11px] sm:text-xs font-semibold transition-all ${
                  previewTab === 'instagram'
                    ? 'bg-gradient-to-r from-purple-600 via-pink-600 to-amber-500 text-white shadow-xs font-bold'
                    : 'text-slate-500 hover:text-pink-600'
                }`}
              >
                <InstagramIcon className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                <span className="hidden xs:inline">Instagram</span>
              </button>
              <button
                onClick={() => setPreviewTab('video')}
                className={`flex items-center gap-1 rounded-lg px-2 sm:px-3 py-1 text-[11px] sm:text-xs font-semibold transition-all ${
                  previewTab === 'video'
                    ? 'bg-rose-600 text-white shadow-xs font-bold'
                    : 'text-slate-500 hover:text-rose-600'
                }`}
              >
                <Video className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                <span>Video Reel</span>
              </button>
            </div>

            {/* Desktop Actions */}
            <div className="hidden sm:flex items-center gap-1 shrink-0">
              <button
                onClick={handleDeletePoster}
                title="Delete Poster"
                className="rounded-xl p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition-colors cursor-pointer"
              >
                <Trash2 className="h-4 w-4" />
              </button>

              <button
                onClick={onClose}
                className="rounded-xl p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Notifications */}
        {dispatchSuccessMsg && (
          <div className="bg-emerald-50 border-b border-emerald-200 px-6 py-2.5 text-xs font-medium text-emerald-800 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
              <span>{dispatchSuccessMsg}</span>
            </div>
            {dispatchSuccessMsg.includes('LinkedIn') && (
              <a
                href="https://www.linkedin.com/in/anna-vance-09b599447/recent-activity/all/"
                target="_blank"
                rel="noreferrer"
                className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1 bg-[#0077b5] hover:bg-[#006097] text-white rounded-lg text-xs font-bold transition-all shadow-xs"
              >
                View Live on LinkedIn ↗
              </a>
            )}
          </div>
        )}
        {dispatchError && (
          <div className="bg-rose-50 border-b border-rose-200 px-6 py-2.5 text-xs font-medium text-rose-800 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 min-w-0">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
              <span>{dispatchError}</span>
            </div>
            {dispatchError.toLowerCase().includes('linkedin') && (
              <a
                href="http://localhost:8000/auth/linkedin/login"
                target="_blank"
                rel="noreferrer"
                className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1 bg-[#0077b5] hover:bg-[#006097] text-white rounded-lg text-xs font-bold transition-all shadow-xs"
              >
                Connect LinkedIn Account →
              </a>
            )}
          </div>
        )}

        {/* Main Content Body */}
        <div className="grid grid-cols-1 lg:grid-cols-12 flex-1 overflow-y-auto">
          {/* Left Canvas Preview Area: starts cleanly from top, horizontally centered */}
          <div className="lg:col-span-7 p-3 sm:p-5 flex flex-col items-center justify-start bg-slate-50/50 border-b lg:border-b-0 lg:border-r border-slate-200 overflow-y-auto">
            {/* Minimal Canvas Control Header */}
            {previewTab === 'poster' && (
              <div className="w-full max-w-lg mb-3 flex flex-wrap sm:flex-nowrap items-center justify-between gap-2 px-1">
                <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                  <span>Poster Canvas</span>
                </span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setEditMode(!editMode)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border transition-all cursor-pointer shadow-2xs ${
                      editMode
                        ? 'bg-amber-100 border-amber-300 text-amber-900'
                        : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <Move className="h-3.5 w-3.5 text-amber-600" />
                    <span>{editMode ? 'Done Dragging' : 'Interactive Canvas Drag'}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewArtOnly((v) => !v)}
                    className={`text-xs font-semibold px-2.5 py-1.5 rounded-xl border transition-all cursor-pointer shadow-2xs ${
                      viewArtOnly
                        ? 'bg-amber-100 border-amber-300 text-amber-900'
                        : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    {viewArtOnly ? 'Show Text' : 'Clean Art'}
                  </button>
                </div>
              </div>
            )}

            {previewTab === 'poster' ? (
              <div
                ref={posterFrameRef}
                className="relative group flex flex-col items-center select-none max-w-full"
              >
                {/* Poster Canvas Frame (100% uncut, native proportional aspect ratio) */}
                <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-slate-200/80 bg-slate-950 inline-block max-w-full">
                  <img
                    src={
                      viewArtOnly
                        ? currentPoster.background_image_url || currentPoster.final_poster_url
                        : isPublished
                        ? currentPoster.final_poster_url
                        : hasCleanBackground
                        ? currentPoster.background_image_url || currentPoster.final_poster_url
                        : currentPoster.final_poster_url
                    }
                    alt={currentPoster.headline}
                    className="block max-h-[44vh] sm:max-h-[54vh] lg:max-h-[64vh] max-w-full w-auto h-auto object-contain select-none"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = '/samples/c0b9f6cf6ff9_final.png';
                    }}
                  />

                  {/* Clean Canvas Typography Layer: Live editor active ONLY for unapproved/in-review drafts with clean background */}
                  {!viewArtOnly && !isPublished && hasCleanBackground && (
                    <>
                      {/* 1. 42 WORKS Logo (Top-Right: matching the gold-standard reference poster) */}
                      <div className="absolute top-[4%] right-[4.5%] z-10 pointer-events-none drop-shadow-[0_2px_4px_rgba(0,0,0,0.85)]">
                        <img src="/42Works_logo2.png?v=2" alt="42 WORKS" className="h-8 sm:h-10 w-auto object-contain" />
                      </div>

                      {/* 2. Unified MS Paint-Style Typography Transformer: Headline & Quotes Togetherly */}
                      <div
                        ref={textBoxRef}
                        style={{
                          left: `${textPos.x}%`,
                          top: `${textPos.y}%`,
                          width: `${textWidth}%`,
                          transform: `translate(-50%, -50%) rotate(${textRotation}deg) scale(${textScale})`,
                          transformOrigin: 'center center',
                        }}
                        onMouseDown={(e) => handleActionStart('drag', e)}
                        onTouchStart={(e) => handleActionStart('drag', e)}
                        title="Click & drag to move headline and quote together. Drag edges to stretch, corners to resize, top circle to rotate!"
                        className={`absolute z-20 cursor-grab active:cursor-grabbing select-none transition-shadow rounded-2xl flex flex-col items-center text-center group/textcard ${
                          activeAction
                            ? 'ring-2 ring-amber-400 border border-dashed border-amber-300 bg-black/45 backdrop-blur-xs shadow-2xl'
                            : 'hover:ring-1 hover:ring-amber-400/80 hover:bg-black/25'
                        }`}
                      >
                        {/* MS Paint Rotation Stem & Handle on top */}
                        <div className="absolute -top-7 left-1/2 -translate-x-1/2 flex flex-col items-center opacity-0 group-hover/textcard:opacity-100 transition-opacity">
                          {/* Circular Rotate Knob */}
                          <div
                            onMouseDown={(e) => handleActionStart('rotate', e)}
                            onTouchStart={(e) => handleActionStart('rotate', e)}
                            title={`Drag to rotate freely (current: ${textRotation}°)`}
                            className={`h-5 w-5 rounded-full bg-amber-400 border-2 border-slate-900 text-slate-950 flex items-center justify-center cursor-crosshair shadow-md hover:scale-125 transition-transform ${
                              activeAction === 'rotate' ? 'scale-125 ring-2 ring-white' : ''
                            }`}
                          >
                            <RotateCw className="h-2.5 w-2.5" />
                          </div>
                          {/* Stem line */}
                          <div className="h-2.5 w-[1.5px] bg-amber-400" />
                        </div>

                        {/* East / Right Horizontal Stretch Handle */}
                        <div
                          onMouseDown={(e) => handleActionStart('stretch-e', e)}
                          onTouchStart={(e) => handleActionStart('stretch-e', e)}
                          title="Drag to stretch width horizontally"
                          className="opacity-0 group-hover/textcard:opacity-100 transition-opacity absolute -right-2 top-1/2 -translate-y-1/2 h-7 w-2.5 rounded-sm bg-amber-400 border border-slate-900 cursor-ew-resize shadow-md hover:scale-125 transition-transform flex items-center justify-center"
                        >
                          <div className="h-3 w-0.5 bg-slate-900" />
                        </div>

                        {/* West / Left Horizontal Stretch Handle */}
                        <div
                          onMouseDown={(e) => handleActionStart('stretch-w', e)}
                          onTouchStart={(e) => handleActionStart('stretch-w', e)}
                          title="Drag to stretch width horizontally"
                          className="opacity-0 group-hover/textcard:opacity-100 transition-opacity absolute -left-2 top-1/2 -translate-y-1/2 h-7 w-2.5 rounded-sm bg-amber-400 border border-slate-900 cursor-ew-resize shadow-md hover:scale-125 transition-transform flex items-center justify-center"
                        >
                          <div className="h-3 w-0.5 bg-slate-900" />
                        </div>

                        {/* North / Top Vertical Spacing Handle */}
                        <div
                          onMouseDown={(e) => handleActionStart('stretch-n', e)}
                          onTouchStart={(e) => handleActionStart('stretch-n', e)}
                          title="Drag to adjust vertical spacing"
                          className="opacity-0 group-hover/textcard:opacity-100 transition-opacity absolute -top-1.5 left-1/2 -translate-x-1/2 w-7 h-2 rounded-sm bg-amber-400 border border-slate-900 cursor-ns-resize shadow-md hover:scale-125 transition-transform"
                        />

                        {/* South / Bottom Vertical Spacing Handle */}
                        <div
                          onMouseDown={(e) => handleActionStart('stretch-s', e)}
                          onTouchStart={(e) => handleActionStart('stretch-s', e)}
                          title="Drag to adjust vertical spacing"
                          className="opacity-0 group-hover/textcard:opacity-100 transition-opacity absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-7 h-2 rounded-sm bg-amber-400 border border-slate-900 cursor-ns-resize shadow-md hover:scale-125 transition-transform"
                        />

                        {/* Corner Handles (Proportional Scaling) */}
                        {/* Southeast */}
                        <div
                          onMouseDown={(e) => handleActionStart('scale-corner', e)}
                          onTouchStart={(e) => handleActionStart('scale-corner', e)}
                          title="Drag corner to scale size"
                          className="opacity-0 group-hover/textcard:opacity-100 transition-opacity absolute -bottom-2 -right-2 h-4 w-4 rounded-full bg-amber-400 border-2 border-slate-900 cursor-nwse-resize shadow-md hover:scale-125 transition-transform flex items-center justify-center"
                        >
                          <Maximize2 className="h-2 w-2 text-slate-950 rotate-90" />
                        </div>
                        {/* Southwest */}
                        <div
                          onMouseDown={(e) => handleActionStart('scale-corner', e)}
                          onTouchStart={(e) => handleActionStart('scale-corner', e)}
                          title="Drag corner to scale size"
                          className="opacity-0 group-hover/textcard:opacity-100 transition-opacity absolute -bottom-2 -left-2 h-4 w-4 rounded-full bg-amber-400 border-2 border-slate-900 cursor-nesw-resize shadow-md hover:scale-125 transition-transform"
                        />
                        {/* Northeast */}
                        <div
                          onMouseDown={(e) => handleActionStart('scale-corner', e)}
                          onTouchStart={(e) => handleActionStart('scale-corner', e)}
                          title="Drag corner to scale size"
                          className="opacity-0 group-hover/textcard:opacity-100 transition-opacity absolute -top-2 -right-2 h-4 w-4 rounded-full bg-amber-400 border-2 border-slate-900 cursor-nesw-resize shadow-md hover:scale-125 transition-transform"
                        />
                        {/* Northwest */}
                        <div
                          onMouseDown={(e) => handleActionStart('scale-corner', e)}
                          onTouchStart={(e) => handleActionStart('scale-corner', e)}
                          title="Drag corner to scale size"
                          className="opacity-0 group-hover/textcard:opacity-100 transition-opacity absolute -top-2 -left-2 h-4 w-4 rounded-full bg-amber-400 border-2 border-slate-900 cursor-nwse-resize shadow-md hover:scale-125 transition-transform"
                        />

                        {/* Typography Content: Headline + Diamond Divider + Quotes together with Live Color Binding */}
                        <div className="px-5 py-3 w-full flex flex-col items-center">
                          {/* Event Tagline */}
                          <p
                            style={{ color: accentColor }}
                            className="text-[10px] sm:text-xs font-bold tracking-[0.25em] uppercase drop-shadow-[0_1px_3px_rgba(0,0,0,0.9)] mb-1 pointer-events-none transition-colors"
                          >
                            {eventTagline}
                          </p>

                          {/* Hero Headline */}
                          <h2
                            style={{ color: headlineColor }}
                            className="font-serif font-bold text-lg sm:text-2xl drop-shadow-[0_2px_5px_rgba(0,0,0,0.95)] w-full leading-tight pointer-events-none transition-colors"
                          >
                            {headline || currentPoster.headline}
                          </h2>

                          {/* Diamond Divider */}
                          <div className="flex items-center justify-center gap-2 my-2 pointer-events-none">
                            <div style={{ backgroundColor: accentColor }} className="h-[1.5px] w-12 sm:w-16 opacity-80 transition-colors" />
                            <div style={{ backgroundColor: accentColor }} className="h-2 w-2 rotate-45 transition-colors" />
                            <div style={{ backgroundColor: accentColor }} className="h-[1.5px] w-12 sm:w-16 opacity-80 transition-colors" />
                          </div>

                          {/* Reflection Quote */}
                          {quote && (
                            <div style={{ marginTop: `${textGap}px` }} className="w-full">
                              <p
                                style={{ color: quoteColor }}
                                className="font-serif italic text-center text-xs sm:text-sm drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)] leading-relaxed pointer-events-none transition-colors"
                              >
                                "{cleanQuoteText(quote)}"
                              </p>
                            </div>
                          )}
                        </div>

                        {/* Hover Floating Status Badge */}
                        <div className="opacity-0 group-hover/textcard:opacity-100 transition-opacity absolute -bottom-7 left-1/2 -translate-x-1/2 flex items-center gap-2 pointer-events-auto">
                          <span className="rounded-full bg-slate-950/90 px-2.5 py-0.5 text-[9px] font-bold text-amber-300 border border-amber-400/40 shadow-lg flex items-center gap-1.5 whitespace-nowrap">
                            <Move className="h-2.5 w-2.5" />
                            Drag Together ({textPos.y}%) • {textWidth}% W • {textRotation}°
                          </span>
                          {textRotation !== 0 && (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                setTextRotation(0);
                              }}
                              className="rounded-full bg-amber-400 text-slate-950 px-2 py-0.5 text-[9px] font-bold hover:bg-amber-300 shadow cursor-pointer"
                              title="Reset rotation to 0°"
                            >
                              0° Reset
                            </button>
                          )}
                        </div>
                      </div>
                    </>
                  )}
                </div>

                {/* Canvas Bottom Action Bar: Preview Clean Art & Save as PNG (Appearing right after poster ends) */}
                <div className="mt-3.5 flex flex-wrap items-center justify-between gap-3 w-full max-w-lg">
                  <div className="flex items-center gap-2">
                    {currentPoster.background_image_url && (
                      <button
                        type="button"
                        onClick={() => setViewArtOnly(!viewArtOnly)}
                        className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold border transition-all cursor-pointer shadow-xs ${
                          viewArtOnly
                            ? 'bg-amber-500 text-white border-amber-600 shadow-amber-500/20'
                            : 'bg-white text-slate-800 border-slate-300 hover:bg-slate-50 hover:text-amber-600'
                        }`}
                      >
                        <Eye className="h-4 w-4" />
                        <span>{viewArtOnly ? 'Show Final Typography' : 'Preview Clean Art'}</span>
                      </button>
                    )}
                    {(generatedVideoUrl || currentPoster.video_url) && (
                      <a
                        href={generatedVideoUrl || currentPoster.video_url || '#'}
                        download={`video_reel_${currentPoster.id}.mp4`}
                        className="flex items-center gap-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white px-4 py-2 text-xs font-bold shadow-md transition-all hover:scale-105 active:scale-95 cursor-pointer"
                      >
                        <Video className="h-4 w-4" />
                        <span>Download MP4</span>
                      </a>
                    )}
                    <button
                      type="button"
                      onClick={handleDownloadPNG}
                      className="flex items-center gap-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white px-4 py-2 text-xs font-bold shadow-md transition-all hover:scale-105 active:scale-95 cursor-pointer"
                    >
                      <Download className="h-4 w-4" />
                      <span>Save as PNG</span>
                    </button>
                  </div>

                  <button
                    type="button"
                    onClick={handleDeletePoster}
                    className="flex items-center gap-1.5 rounded-xl border border-rose-200 bg-rose-50/80 px-3 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-100 shadow-xs transition-colors cursor-pointer"
                  >
                    <Trash2 className="h-3.5 w-3.5 text-rose-500" />
                    <span>Delete</span>
                  </button>
                </div>
              </div>
            ) : previewTab === 'linkedin' ? (
              /* Realistic LinkedIn Post Preview */
              <div className="w-full max-w-md mx-auto rounded-2xl border border-slate-200 bg-white text-slate-900 p-4 shadow-xl">
                {generatedVideoUrl && (
                  <div className="flex items-center justify-between mb-3 bg-slate-100 p-1 rounded-xl">
                    <button
                      type="button"
                      onClick={() => setSocialMediaType('video')}
                      className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                        socialMediaType === 'video' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-900'
                      }`}
                    >
                      <Video className="h-3.5 w-3.5 text-rose-600" />
                      <span>Video Reel</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setSocialMediaType('image')}
                      className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                        socialMediaType === 'image' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-900'
                      }`}
                    >
                      <Eye className="h-3.5 w-3.5 text-amber-600" />
                      <span>Static Image</span>
                    </button>
                  </div>
                )}
                <div className="flex items-center gap-3 mb-3">
                  <div className="h-10 w-10 rounded-full flex items-center justify-center overflow-hidden p-0.5">
                    <img src="/42works_logo.png" alt="42 WORKS" className="h-full w-full object-contain" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">42 WORKS</h4>
                    <p className="text-[10px] text-slate-500">18,480 followers • Just now</p>
                  </div>
                </div>
                <p className="text-xs text-slate-700 whitespace-pre-line mb-3 max-h-36 overflow-y-auto leading-relaxed">
                  {caption || currentPoster.caption}
                </p>
                <p className="text-xs text-[#0077b5] font-semibold mb-3">
                  {hashtagsText || currentPoster.hashtags.join(' ')}
                </p>
                <div className="rounded-xl overflow-hidden border border-slate-200 bg-black mb-2 shadow-xs">
                  {socialMediaType === 'video' && generatedVideoUrl ? (
                    <video
                      key={generatedVideoUrl}
                      src={generatedVideoUrl}
                      controls
                      autoPlay
                      loop
                      playsInline
                      className="w-full max-h-[380px] object-contain bg-black mx-auto"
                    />
                  ) : (
                    <img
                      key={currentPoster.final_poster_url}
                      src={currentPoster.final_poster_url}
                      alt="LinkedIn Creative"
                      className="w-full h-auto"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = '/42works_logo.png';
                      }}
                    />
                  )}
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-500 border-t border-slate-100 pt-2.5 px-1 font-medium">
                  <span className="flex items-center gap-1.5 text-emerald-600 font-semibold">
                    <span className="h-2 w-2 rounded-full bg-emerald-500" />
                    {socialMediaType === 'video' && generatedVideoUrl ? 'Video Reel Ready' : 'Poster Creative Ready'}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">LinkedIn Feed Preview</span>
                </div>
              </div>
            ) : previewTab === 'video' ? (
              /* Realistic Video Reel Preview */
              <div className="w-full max-w-sm mx-auto rounded-3xl border border-slate-200 bg-white text-slate-900 p-4 shadow-xl text-center space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Video className="h-4 w-4 text-rose-600" />
                    <h4 className="text-xs font-bold text-slate-900">Video Reel</h4>
                  </div>
                  {generatedVideoUrl && (
                    <button
                      type="button"
                      onClick={() => setVideoEditMode(!videoEditMode)}
                      className={`flex items-center gap-1.5 px-3 py-1 rounded-xl text-[11px] font-bold border transition-all cursor-pointer shadow-2xs ${
                        videoEditMode
                          ? 'bg-amber-500 text-white border-amber-600 shadow-amber-500/20'
                          : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      <Move className="h-3 w-3" />
                      <span>{videoEditMode ? 'Done Positioning' : 'Reposition Text'}</span>
                    </button>
                  )}
                </div>

                {generatedVideoUrl ? (
                  <>
                    <div
                      ref={videoFrameRef}
                    className="relative rounded-2xl overflow-hidden border border-slate-200 bg-black aspect-[9/16] max-h-[440px] shadow-lg flex items-center justify-center mx-auto select-none group/videocard"
                  >
                    <video
                      key={generatedVideoUrl}
                      src={generatedVideoUrl}
                      controls
                      autoPlay
                      loop
                      playsInline
                      className="w-full h-full object-contain bg-black"
                    />

                    {/* Interactive Target Frame for Video Typography (Full Live Preview & Exact Placement) */}
                    {videoEditMode && (
                      <div
                        ref={textBoxRef}
                        onMouseDown={(e) => handleActionStart('drag', e)}
                        onTouchStart={(e) => handleActionStart('drag', e)}
                        style={{
                          top: `${textPos.y}%`,
                          left: `${textPos.x}%`,
                          width: `${textWidth}%`,
                          transform: `translate(-50%, -50%) rotate(${textRotation}deg) scale(${textScale})`,
                        }}
                        className={`absolute flex flex-col items-center justify-center select-none text-center cursor-move transition-shadow z-20 group/textcard ${
                          activeAction ? 'cursor-grabbing' : ''
                        }`}
                      >
                        {/* Target Outline & Bounding Box */}
                        <div
                          className={`absolute inset-0 rounded-2xl border-2 pointer-events-none transition-all ${
                            activeAction
                              ? 'border-amber-400 bg-black/60 shadow-xl'
                              : 'border-dashed border-amber-400/90 bg-black/50 hover:border-amber-300 hover:bg-black/60'
                          }`}
                        />

                        {/* Top Rotation Handle */}
                        <div className="opacity-0 group-hover/textcard:opacity-100 transition-opacity absolute -top-8 left-1/2 -translate-x-1/2 flex flex-col items-center cursor-crosshair">
                          <div
                            onMouseDown={(e) => handleActionStart('rotate', e)}
                            onTouchStart={(e) => handleActionStart('rotate', e)}
                            title={`Drag to rotate (current: ${textRotation}°)`}
                            className="h-4.5 w-4.5 rounded-full bg-amber-400 border-2 border-slate-900 text-slate-950 flex items-center justify-center shadow hover:scale-125 transition-transform"
                          >
                            <RotateCw className="h-2 w-2" />
                          </div>
                          <div className="h-2 w-[1.5px] bg-amber-400" />
                        </div>

                        {/* East & West stretch handles */}
                        <div
                          onMouseDown={(e) => handleActionStart('stretch-e', e)}
                          onTouchStart={(e) => handleActionStart('stretch-e', e)}
                          title="Stretch width"
                          className="opacity-0 group-hover/textcard:opacity-100 transition-opacity absolute -right-2 top-1/2 -translate-y-1/2 h-6 w-2 rounded-sm bg-amber-400 border border-slate-900 cursor-ew-resize shadow hover:scale-125 transition-transform flex items-center justify-center"
                        />
                        <div
                          onMouseDown={(e) => handleActionStart('stretch-w', e)}
                          onTouchStart={(e) => handleActionStart('stretch-w', e)}
                          title="Stretch width"
                          className="opacity-0 group-hover/textcard:opacity-100 transition-opacity absolute -left-2 top-1/2 -translate-y-1/2 h-6 w-2 rounded-sm bg-amber-400 border border-slate-900 cursor-ew-resize shadow hover:scale-125 transition-transform flex items-center justify-center"
                        />

                        {/* Corner scale handle */}
                        <div
                          onMouseDown={(e) => handleActionStart('scale-corner', e)}
                          onTouchStart={(e) => handleActionStart('scale-corner', e)}
                          title="Scale size"
                          className="opacity-0 group-hover/textcard:opacity-100 transition-opacity absolute -bottom-2 -right-2 h-3.5 w-3.5 rounded-full bg-amber-400 border-2 border-slate-900 cursor-nwse-resize shadow hover:scale-125 transition-transform flex items-center justify-center"
                        >
                          <Maximize2 className="h-1.5 w-1.5 text-slate-950 rotate-90" />
                        </div>

                        {/* Live Typography Preview matching exact video styling */}
                        <div className="px-4 py-2.5 w-full flex flex-col items-center pointer-events-none">
                          <p
                            style={{ color: accentColor }}
                            className="text-[9px] font-bold tracking-[0.2em] uppercase mb-0.5 drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)]"
                          >
                            {eventTagline}
                          </p>
                          <h3
                            style={{ color: headlineColor }}
                            className="font-serif font-bold text-sm sm:text-base w-full leading-tight drop-shadow-[0_2px_4px_rgba(0,0,0,0.95)]"
                          >
                            {headline || currentPoster.headline}
                          </h3>
                          <div className="flex items-center justify-center gap-1.5 my-1">
                            <div style={{ backgroundColor: accentColor }} className="h-[1px] w-8 opacity-80" />
                            <div style={{ backgroundColor: accentColor }} className="h-1.5 w-1.5 rotate-45" />
                            <div style={{ backgroundColor: accentColor }} className="h-[1px] w-8 opacity-80" />
                          </div>
                          {quote && (
                            <p
                              style={{ color: quoteColor }}
                              className="font-serif italic text-center text-[10px] sm:text-xs leading-snug drop-shadow-[0_1px_3px_rgba(0,0,0,0.9)]"
                            >
                              "{cleanQuoteText(quote)}"
                            </p>
                          )}
                          <span className="mt-1.5 rounded-full bg-amber-400 text-slate-950 px-2 py-0.5 text-[8px] font-bold shadow flex items-center gap-1">
                            <Move className="h-2 w-2" />
                            Position: {textPos.y}% Y
                          </span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Video Typography Reposition Action Bar */}
                  {videoEditMode && (
                    <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 bg-amber-500/10 border border-amber-400/40 rounded-2xl text-left mt-2">
                      <div>
                        <span className="text-xs font-bold text-slate-900 block">
                          Video Text Position: <span className="text-amber-700 font-mono">{textPos.y}% Y</span>
                        </span>
                        <span className="text-[10px] text-slate-600">
                          Drag to fit text anywhere on video, then approve.
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setVideoEditMode(false)}
                          className="px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100 bg-white border border-slate-300 rounded-lg cursor-pointer"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          onClick={handleRecomposite}
                          disabled={isRecomposing}
                          className="px-3.5 py-1 text-xs font-bold text-slate-950 bg-amber-400 hover:bg-amber-300 rounded-lg shadow-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                        >
                          {isRecomposing ? <Loader2 className="h-3 w-3 animate-spin" /> : <Check className="h-3 w-3" />}
                          <span>{isRecomposing ? 'Applying...' : 'Approve & Place Here'}</span>
                        </button>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                  <div className="rounded-2xl border-2 border-dashed border-rose-200 bg-rose-50/40 p-8 text-center space-y-3">
                    <div className="h-12 w-12 rounded-2xl bg-rose-100 text-rose-600 flex items-center justify-center mx-auto border border-rose-200 shadow-xs">
                      <Play className="h-6 w-6 ml-0.5" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">No Reel Generated Yet</h4>
                      <p className="text-[11px] text-slate-500 mt-1 max-w-xs mx-auto leading-relaxed">
                        Convert this poster into an animated short-form video reel.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={handleGenerateVideoReel}
                      disabled={isGeneratingVideo}
                      className="inline-flex items-center gap-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white px-4 py-2 text-xs font-bold shadow-md transition-all cursor-pointer disabled:opacity-50"
                    >
                      {isGeneratingVideo ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>Synthesizing Reel...</span>
                        </>
                      ) : (
                        <>
                          <Video className="h-4 w-4" />
                          <span>Generate Video Reel</span>
                        </>
                      )}
                    </button>
                  </div>
                )}

                {generatedVideoUrl && (
                  <div className="pt-2.5 flex items-center justify-between border-t border-slate-100 gap-2">
                    <a
                      href={generatedVideoUrl}
                      download="wan2_video_reel.mp4"
                      className="flex items-center gap-1.5 text-xs font-bold text-rose-600 hover:underline"
                    >
                      <Download className="h-3.5 w-3.5" />
                      <span>Download MP4</span>
                    </a>
                    <button
                      type="button"
                      onClick={handleGenerateVideoReel}
                      disabled={isGeneratingVideo}
                      title="Re-render the video reel to reflect your latest typography and color revisions"
                      className="inline-flex items-center gap-1.5 text-xs bg-rose-50 hover:bg-rose-100 text-rose-700 px-3 py-1.5 rounded-xl font-bold cursor-pointer transition-all border border-rose-200 disabled:opacity-50"
                    >
                      {isGeneratingVideo ? (
                        <>
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          <span>Updating Reel...</span>
                        </>
                      ) : (
                        <>
                          <RefreshCw className="h-3.5 w-3.5 text-rose-600" />
                          <span>Sync Video with Typography & Colors</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              /* Realistic Instagram Post / Reel Preview - Centered */
              <div className="w-full max-w-sm mx-auto rounded-3xl border border-slate-200 bg-white text-slate-900 p-3.5 shadow-xl flex flex-col items-center">
                {generatedVideoUrl && (
                  <div className="w-full flex items-center justify-between mb-3 bg-slate-100 p-1 rounded-xl">
                    <button
                      type="button"
                      onClick={() => setSocialMediaType('video')}
                      className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                        socialMediaType === 'video' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-900'
                      }`}
                    >
                      <Video className="h-3.5 w-3.5 text-rose-600" />
                      <span>Reels (9:16)</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setSocialMediaType('image')}
                      className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                        socialMediaType === 'image' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-900'
                      }`}
                    >
                      <Eye className="h-3.5 w-3.5 text-amber-600" />
                      <span>Feed Post (1:1)</span>
                    </button>
                  </div>
                )}
                <div className="w-full flex items-center gap-2.5 mb-3 px-1">
                  <div className="h-9 w-9 rounded-full bg-gradient-to-tr from-amber-500 to-pink-500 p-0.5 shadow-xs">
                    <div className="h-full w-full rounded-full flex items-center justify-center p-0.5 overflow-hidden bg-white">
                      <img src="/42works_logo.png" alt="42 WORKS" className="h-full w-full object-contain" />
                    </div>
                  </div>
                  <div className="text-left flex-1">
                    <h4 className="text-xs font-bold text-slate-900 leading-none">42works_official</h4>
                    <p className="text-[10px] text-slate-500 mt-0.5">Global Innovation Studio</p>
                  </div>
                </div>
                {socialMediaType === 'video' && generatedVideoUrl ? (
                  <div className="relative rounded-2xl overflow-hidden border border-slate-800 bg-black mb-3 shadow-2xl aspect-[9/16] w-full max-h-[460px] flex items-center justify-center mx-auto select-none">
                    <video
                      key={generatedVideoUrl}
                      src={generatedVideoUrl}
                      controls
                      autoPlay
                      loop
                      playsInline
                      className="w-full h-full object-contain bg-black"
                    />

                    <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-full text-white text-[9px] font-bold pointer-events-none shadow-md z-30">
                      <span className="h-2 w-2 rounded-full bg-rose-500 animate-pulse" />
                      <span>Instagram Reels</span>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-2xl overflow-hidden border border-slate-200 mb-3 shadow-xs w-full mx-auto">
                    <img
                      key={currentPoster.final_poster_url}
                      src={currentPoster.final_poster_url}
                      alt="Instagram Creative"
                      className="w-full h-auto"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = '/42works_logo.png';
                      }}
                    />
                  </div>
                )}
                <div className="w-full px-1 text-xs">
                  <div className="flex items-center justify-between text-[10px] text-slate-400 mb-2 pt-1 border-t border-slate-100">
                    <span className="font-semibold text-rose-600 flex items-center gap-1">
                      <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
                      {socialMediaType === 'video' && generatedVideoUrl ? 'Reels Ready' : 'Feed Post Ready'}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">Instagram Mobile Mockup</span>
                  </div>
                  <div className="max-h-36 overflow-y-auto pr-1 space-y-1.5 mb-1 border-t border-slate-100 pt-2 leading-relaxed text-left">
                    <p className="text-slate-700 text-[11px] whitespace-pre-line">
                      <span className="font-bold text-slate-900 mr-1.5">42works_official</span>
                      {caption || currentPoster.caption}
                    </p>
                    <p className="text-[#0077b5] text-[10px] font-medium whitespace-pre-line leading-normal">
                      {hashtagsText || currentPoster.hashtags.join(' ')}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Inspector & Controls */}
          <div className="lg:col-span-5 p-4 sm:p-6 flex flex-col justify-between space-y-5 sm:space-y-6 bg-white">
            <div className="space-y-5">
              {/* Approval Lock Banner */}
              <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                <div>
                  <h4 className="text-xs font-bold text-slate-900">Human Approval State</h4>
                  <p className="text-[11px] text-slate-500">
                    {isApproved ? 'Approved and ready for social dispatch.' : 'Requires approval before social dispatch.'}
                  </p>
                </div>
                {!isApproved ? (
                  <button
                    onClick={handleApprove}
                    disabled={isApproving}
                    className="flex items-center gap-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-xs font-semibold text-white shadow-sm disabled:opacity-50 transition-all cursor-pointer"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    {isApproving ? 'Locking...' : 'Approve & Lock'}
                  </button>
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-200">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" /> Approved
                    </span>
                    <button
                      onClick={handleUnlock}
                      disabled={isUnlocking}
                      title="Unlock this creative to make further edits or adjustments"
                      className="flex items-center gap-1 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-300 transition-all cursor-pointer shadow-2xs"
                    >
                      <RotateCcw className="h-3 w-3 text-slate-500" />
                      {isUnlocking ? 'Unlocking...' : 'Unlock to Edit'}
                    </button>
                  </div>
                )}
              </div>

              {/* Fast Copy Revision */}
              <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                    <RefreshCw className="h-3.5 w-3.5 text-amber-600" />
                    Instant Typography Revisions
                  </span>
                </div>

                {/* Headline Text Input */}
                <div>
                  <label className="text-[11px] font-semibold text-slate-700 block mb-1">Headline Text</label>
                  <input
                    type="text"
                    value={headline}
                    onChange={(e) => setHeadline(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-[#FFC20E] focus:ring-1 focus:ring-[#FFC20E] focus:outline-none shadow-xs"
                  />
                </div>

                {/* Reflection Quote Text Input */}
                <div>
                  <label className="text-[11px] font-semibold text-slate-700 block mb-1">Reflection Quote</label>
                  <input
                    type="text"
                    value={quote}
                    onChange={(e) => setQuote(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-[#FFC20E] focus:ring-1 focus:ring-[#FFC20E] focus:outline-none shadow-xs"
                  />
                </div>

                {/* Text Color & Visibility Controls (Ensure crisp contrast on any light or dark image/video) */}
                <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-slate-800 flex items-center gap-1.5">
                      <Palette className="h-3.5 w-3.5 text-amber-600" />
                      Text Color & Contrast
                    </span>
                    {/* Theme-aligned Segmented Preset Switcher (Styled exactly like Video Reel / Poster buttons) */}
                    <div className="inline-flex rounded-xl bg-slate-200/80 p-0.5 border border-slate-200">
                      <button
                        type="button"
                        onClick={() => {
                          setHeadlineColor('#FFFFFF');
                          setQuoteColor('#FFDF0F');
                          setAccentColor('#DFB876');
                        }}
                        title="White & Gold: Best for dark, rich, or night scenes"
                        className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-bold transition-all cursor-pointer ${
                          headlineColor.toLowerCase() === '#ffffff'
                            ? 'bg-white text-slate-900 shadow-xs border border-slate-200/80'
                            : 'text-slate-500 hover:text-slate-900'
                        }`}
                      >
                        <Sun className={`h-3.5 w-3.5 ${headlineColor.toLowerCase() === '#ffffff' ? 'text-amber-500' : 'text-slate-400'}`} />
                        <span>Light on Dark</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setHeadlineColor('#0F172A');
                          setQuoteColor('#78350F');
                          setAccentColor('#92400E');
                        }}
                        title="Dark Slate & Bronze: Best for bright, sunny, or daylight scenes"
                        className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-bold transition-all cursor-pointer ${
                          headlineColor.toLowerCase() === '#0f172a'
                            ? 'bg-white text-slate-900 shadow-xs border border-slate-200/80'
                            : 'text-slate-500 hover:text-slate-900'
                        }`}
                      >
                        <Moon className={`h-3.5 w-3.5 ${headlineColor.toLowerCase() === '#0f172a' ? 'text-indigo-600' : 'text-slate-400'}`} />
                        <span>Dark on Light</span>
                      </button>
                    </div>
                  </div>

                  {/* Headline Color Row */}
                  <div className="flex items-center justify-between gap-2 text-[10px]">
                    <span className="font-semibold text-slate-700 shrink-0">Headline Color:</span>
                    <div className="flex items-center gap-1.5 flex-wrap justify-end">
                      {[
                        { label: 'White', color: '#FFFFFF', border: 'border-slate-300' },
                        { label: 'Dark Slate', color: '#0F172A', border: 'border-slate-800' },
                        { label: 'Brand Gold', color: '#FFDF0F', border: 'border-amber-400' },
                        { label: 'Sunset Amber', color: '#F59E0B', border: 'border-amber-500' },
                        { label: 'Ruby Red', color: '#DC2626', border: 'border-rose-500' },
                      ].map((c) => (
                        <button
                          key={c.color}
                          type="button"
                          onClick={() => setHeadlineColor(c.color)}
                          title={`${c.label} (${c.color})`}
                          style={{ backgroundColor: c.color }}
                          className={`h-4.5 w-4.5 rounded-full border-2 transition-transform cursor-pointer shadow-2xs hover:scale-125 ${
                            headlineColor.toLowerCase() === c.color.toLowerCase()
                              ? 'ring-2 ring-amber-500 ring-offset-1 scale-110 border-white'
                              : c.border
                          }`}
                        />
                      ))}
                      {/* Color Picker input */}
                      <label
                        title="Custom Color Picker"
                        className="relative flex items-center justify-center h-4.5 w-4.5 rounded-full border border-slate-300 bg-gradient-to-tr from-pink-500 via-amber-400 to-indigo-500 cursor-pointer shadow-2xs hover:scale-110"
                      >
                        <input
                          type="color"
                          value={headlineColor}
                          onChange={(e) => setHeadlineColor(e.target.value)}
                          className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                        />
                      </label>
                      <span className="text-[10px] font-mono text-slate-600 font-bold uppercase">{headlineColor}</span>
                    </div>
                  </div>

                  {/* Quote Color Row */}
                  <div className="flex items-center justify-between gap-2 text-[10px]">
                    <span className="font-semibold text-slate-700 shrink-0">Quote Color:</span>
                    <div className="flex items-center gap-1.5 flex-wrap justify-end">
                      {[
                        { label: 'Brand Gold', color: '#FFDF0F', border: 'border-amber-400' },
                        { label: 'White', color: '#FFFFFF', border: 'border-slate-300' },
                        { label: 'Dark Slate', color: '#0F172A', border: 'border-slate-800' },
                        { label: 'Bronze', color: '#78350F', border: 'border-amber-700' },
                        { label: 'Soft Amber', color: '#F59E0B', border: 'border-amber-500' },
                      ].map((c) => (
                        <button
                          key={c.color}
                          type="button"
                          onClick={() => setQuoteColor(c.color)}
                          title={`${c.label} (${c.color})`}
                          style={{ backgroundColor: c.color }}
                          className={`h-4.5 w-4.5 rounded-full border-2 transition-transform cursor-pointer shadow-2xs hover:scale-125 ${
                            quoteColor.toLowerCase() === c.color.toLowerCase()
                              ? 'ring-2 ring-amber-500 ring-offset-1 scale-110 border-white'
                              : c.border
                          }`}
                        />
                      ))}
                      {/* Color Picker input */}
                      <label
                        title="Custom Quote Color Picker"
                        className="relative flex items-center justify-center h-4.5 w-4.5 rounded-full border border-slate-300 bg-gradient-to-tr from-pink-500 via-amber-400 to-indigo-500 cursor-pointer shadow-2xs hover:scale-110"
                      >
                        <input
                          type="color"
                          value={quoteColor}
                          onChange={(e) => setQuoteColor(e.target.value)}
                          className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                        />
                      </label>
                      <span className="text-[10px] font-mono text-slate-600 font-bold uppercase">{quoteColor}</span>
                    </div>
                  </div>

                  {/* Accent / Tagline Color Row */}
                  <div className="flex items-center justify-between gap-2 text-[10px]">
                    <span className="font-semibold text-slate-700 shrink-0">Tagline & Divider:</span>
                    <div className="flex items-center gap-1.5 flex-wrap justify-end">
                      {[
                        { label: 'Warm Gold', color: '#DFB876', border: 'border-amber-300' },
                        { label: 'Bright Gold', color: '#FFDF0F', border: 'border-amber-400' },
                        { label: 'White', color: '#FFFFFF', border: 'border-slate-300' },
                        { label: 'Dark Slate', color: '#0F172A', border: 'border-slate-800' },
                      ].map((c) => (
                        <button
                          key={c.color}
                          type="button"
                          onClick={() => setAccentColor(c.color)}
                          title={`${c.label} (${c.color})`}
                          style={{ backgroundColor: c.color }}
                          className={`h-4.5 w-4.5 rounded-full border-2 transition-transform cursor-pointer shadow-2xs hover:scale-125 ${
                            accentColor.toLowerCase() === c.color.toLowerCase()
                              ? 'ring-2 ring-amber-500 ring-offset-1 scale-110 border-white'
                              : c.border
                          }`}
                        />
                      ))}
                      {/* Color Picker input */}
                      <label
                        title="Custom Accent Color Picker"
                        className="relative flex items-center justify-center h-4.5 w-4.5 rounded-full border border-slate-300 bg-gradient-to-tr from-pink-500 via-amber-400 to-indigo-500 cursor-pointer shadow-2xs hover:scale-110"
                      >
                        <input
                          type="color"
                          value={accentColor}
                          onChange={(e) => setAccentColor(e.target.value)}
                          className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                        />
                      </label>
                      <span className="text-[10px] font-mono text-slate-600 font-bold uppercase">{accentColor}</span>
                    </div>
                  </div>
                </div>

                {/* Unified Typography MS Paint Controls (Transform Headline & Quote Together) */}
                <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3 space-y-2.5">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-bold text-slate-800 flex items-center gap-1.5">
                      <Move className="h-3 w-3 text-amber-600" />
                      Unified Typography (Move & Stretch Together)
                    </span>
                    <button
                      type="button"
                      onClick={handleResetCenter}
                      className="text-[10px] font-bold text-amber-700 hover:text-amber-800 underline cursor-pointer"
                    >
                      Reset 0°
                    </button>
                  </div>

                  {/* Horizontal Width Stretch */}
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-slate-600 font-medium">Horizontal Stretch (Width):</span>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => setTextWidth((w) => Math.max(40, w - 5))}
                        className="px-2 py-0.5 rounded border border-slate-200 bg-white hover:bg-slate-100 font-bold text-slate-700"
                      >
                        -
                      </button>
                      <span className="w-10 text-center font-bold text-slate-800">{textWidth}%</span>
                      <button
                        type="button"
                        onClick={() => setTextWidth((w) => Math.min(96, w + 5))}
                        className="px-2 py-0.5 rounded border border-slate-200 bg-white hover:bg-slate-100 font-bold text-slate-700"
                      >
                        +
                      </button>
                    </div>
                  </div>

                  {/* Proportional Scale */}
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-slate-600 font-medium">Overall Scale:</span>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => setTextScale((s) => Math.max(0.6, Number((s - 0.1).toFixed(2))))}
                        className="px-2 py-0.5 rounded border border-slate-200 bg-white hover:bg-slate-100 font-bold text-slate-700"
                      >
                        -
                      </button>
                      <span className="w-10 text-center font-bold text-slate-800">{Math.round(textScale * 100)}%</span>
                      <button
                        type="button"
                        onClick={() => setTextScale((s) => Math.min(1.7, Number((s + 0.1).toFixed(2))))}
                        className="px-2 py-0.5 rounded border border-slate-200 bg-white hover:bg-slate-100 font-bold text-slate-700"
                      >
                        +
                      </button>
                    </div>
                  </div>

                  {/* Rotation Degrees */}
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-slate-600 font-medium">Rotation Angle:</span>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => setTextRotation((r) => r - 5)}
                        className="px-2 py-0.5 rounded border border-slate-200 bg-white hover:bg-slate-100 font-bold text-slate-700"
                      >
                        ↺ 5°
                      </button>
                      <span className="w-10 text-center font-bold text-amber-700">{textRotation}°</span>
                      <button
                        type="button"
                        onClick={() => setTextRotation((r) => r + 5)}
                        className="px-2 py-0.5 rounded border border-slate-200 bg-white hover:bg-slate-100 font-bold text-slate-700"
                      >
                        ↻ 5°
                      </button>
                    </div>
                  </div>

                  {/* Vertical Position */}
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-slate-600 font-medium">Vertical Placement:</span>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => setTextPos({ x: 50, y: 16 })}
                        className={`px-2 py-0.5 rounded border ${textPos.y === 16 ? 'bg-amber-100 border-amber-300 text-amber-900 font-bold' : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-600'}`}
                      >
                        Top (16%)
                      </button>
                      <button
                        type="button"
                        onClick={() => setTextPos({ x: 50, y: 26 })}
                        className={`px-2 py-0.5 rounded border ${textPos.y === 26 ? 'bg-amber-100 border-amber-300 text-amber-900 font-bold' : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-600'}`}
                      >
                        Upper (26%)
                      </button>
                      <button
                        type="button"
                        onClick={() => setTextPos({ x: 50, y: 80 })}
                        className={`px-2 py-0.5 rounded border ${textPos.y === 80 ? 'bg-amber-100 border-amber-300 text-amber-900 font-bold' : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-600'}`}
                      >
                        Bottom (80%)
                      </button>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end pt-1">
                  <button
                    onClick={handleRecomposite}
                    disabled={isRecomposing}
                    className={`inline-flex items-center gap-1.5 rounded-xl px-5 py-2 text-xs font-bold transition-all hover:scale-105 disabled:opacity-50 ${
                      recomposeSuccess
                        ? 'bg-emerald-500 text-white shadow-md'
                        : 'bg-[#FFC20E] hover:bg-[#e5ae0d] text-slate-950 shadow-sm'
                    }`}
                  >
                    {recomposeSuccess ? <Check className="h-3.5 w-3.5" /> : <Sparkles className="h-3.5 w-3.5" />}
                    <span>{isRecomposing ? 'Saving...' : recomposeSuccess ? 'Changes Saved!' : 'Apply Instant Revision'}</span>
                  </button>
                </div>
              </div>

              {/* Editable Social Caption & Hashtags */}
              <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-[#FFC20E]" />
                    Social Caption & Hashtags
                  </span>
                  <button
                    onClick={copyCaptionToClipboard}
                    className="flex items-center gap-1 text-[11px] text-amber-700 hover:text-amber-800 font-semibold"
                  >
                    {copiedCaption ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
                    {copiedCaption ? 'Copied!' : 'Copy Caption'}
                  </button>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 mb-1">Social Caption</label>
                  <textarea
                    rows={6}
                    value={caption}
                    onChange={(e) => setCaption(e.target.value)}
                    placeholder="Enter social caption..."
                    className="w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-[#FFC20E] focus:ring-1 focus:ring-[#FFC20E] focus:outline-none shadow-xs resize-y min-h-[120px] leading-relaxed font-normal whitespace-pre-wrap"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 mb-1">Hashtags (space-separated)</label>
                  <input
                    type="text"
                    value={hashtagsText}
                    onChange={(e) => setHashtagsText(e.target.value)}
                    placeholder="#Brand #Campaign #Festival"
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-[#0077b5] font-semibold placeholder-slate-400 focus:border-[#FFC20E] focus:ring-1 focus:ring-[#FFC20E] focus:outline-none shadow-xs"
                  />
                </div>

                <div className="flex justify-end pt-1">
                  <button
                    onClick={handleSaveSocialCopy}
                    disabled={isSavingCopy}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 px-5 py-2 text-xs font-bold text-slate-800 shadow-2xs transition-all hover:border-slate-400 disabled:opacity-50"
                  >
                    <Check className="h-3.5 w-3.5 text-emerald-600" />
                    <span>{isSavingCopy ? 'Saving...' : copySavedSuccess ? 'Changes Saved!' : 'Apply Caption Changes'}</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Social Dispatch Buttons ("Like in Gmail") */}
            <div className="pt-2 border-t border-slate-200 space-y-3">
              <div className="text-[11px] font-semibold text-slate-600 flex items-center justify-between">
                <span>Multi-Channel Dispatch</span>
                <span className="text-[10px] text-slate-500 font-normal">Post Now or Schedule Send</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {/* LinkedIn Publish / Schedule */}
                <div className="flex rounded-xl overflow-hidden shadow-sm border border-[#0077b5]">
                  <button
                    onClick={() => handlePublishNow('linkedin')}
                    disabled={dispatching || !isApproved}
                    className="flex-1 flex items-center justify-center gap-1.5 bg-[#0077b5] hover:bg-[#006097] py-2.5 px-3 text-xs font-bold text-white disabled:opacity-50 transition-colors"
                  >
                    <LinkedinIcon className="h-3.5 w-3.5 shrink-0" />
                    <span>Post on LinkedIn</span>
                  </button>
                  <button
                    onClick={() => {
                      setDispatchPlatform('linkedin');
                      setScheduleModalOpen(true);
                    }}
                    disabled={dispatching || !isApproved}
                    title="Schedule LinkedIn Post"
                    className="bg-[#006097] hover:bg-[#004e7c] px-2.5 flex items-center justify-center text-white border-l border-white/20 disabled:opacity-50"
                  >
                    <Clock className="h-3.5 w-3.5" />
                  </button>
                </div>

                {/* Instagram Publish / Schedule */}
                <div className="flex rounded-xl overflow-hidden shadow-sm border border-pink-500">
                  <button
                    onClick={() => handlePublishNow('instagram')}
                    disabled={dispatching || !isApproved}
                    className="flex-1 flex items-center justify-center gap-1.5 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 py-2.5 px-3 text-xs font-bold text-white disabled:opacity-50 transition-all"
                  >
                    <InstagramIcon className="h-3.5 w-3.5 shrink-0" />
                    <span>Post on Instagram</span>
                  </button>
                  <button
                    onClick={() => {
                      setDispatchPlatform('instagram');
                      setScheduleModalOpen(true);
                    }}
                    disabled={dispatching || !isApproved}
                    title="Schedule Instagram Post"
                    className="bg-pink-700 hover:bg-pink-800 px-2.5 flex items-center justify-center text-white border-l border-white/20 disabled:opacity-50"
                  >
                    <Clock className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Schedule Dispatch Dialog (Like in Gmail Schedule Send) */}
      {scheduleModalOpen && (
        <div className="fixed inset-0 z-60 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-amber-600" />
                <h4 className="text-sm font-bold text-slate-900">Schedule Dispatch</h4>
              </div>
              <button
                onClick={() => setScheduleModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <p className="text-xs text-slate-600 mb-4">
              Schedule your post to be automatically published to{' '}
              <span className="font-bold text-slate-900 capitalize">{dispatchPlatform}</span>.
            </p>

            <div className="space-y-3 mb-5">
              <label className="block text-xs font-semibold text-slate-700">Choose Date & Time</label>
              <input
                type="datetime-local"
                value={scheduleDateTime}
                onChange={(e) => setScheduleDateTime(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 focus:border-[#FFC20E] focus:outline-none"
              />
            </div>

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setScheduleModalOpen(false)}
                className="rounded-xl px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleScheduleSend}
                disabled={dispatching || !scheduleDateTime}
                className="flex items-center gap-1.5 rounded-xl bg-[#FFC20E] hover:bg-[#e5ae0d] px-4 py-1.5 text-xs font-bold text-slate-950 disabled:opacity-50 shadow-sm"
              >
                <Send className="h-3.5 w-3.5" />
                {dispatching ? 'Scheduling...' : 'Confirm Schedule'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
