export type UserRole = 'admin' | 'reviewer' | 'member';

export interface User {
  id: number;
  email: string;
  role: UserRole;
  is_active: boolean;
  brand_id?: number;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type PostStatus = 'draft' | 'in_review' | 'approved' | 'scheduled' | 'published' | 'rejected';

export interface Poster {
  id: number;
  brand_id: number;
  prompt: string;
  headline: string;
  caption: string;
  hashtags: string[];
  quote?: string | null;
  background_image_url?: string | null;
  final_poster_url: string;
  video_url?: string | null;
  template_name: string;
  aspect_ratio: string;
  status: PostStatus;
  created_at: string;
  approval_locked_at?: string | null;
  is_archived?: boolean;
  published_at?: string | null;
  created_by_id?: number;
  layout_meta?: {
    x?: number;
    y?: number;
    width?: number;
    scale?: number;
    rotation?: number;
    gap?: number;
    headline_color?: string;
    quote_color?: string;
    accent_color?: string;
    [key: string]: any;
  } | null;
}

export interface CreatorTimelinePoint {
  label: string;
  published_count: number;
  linkedin_count: number;
  instagram_count: number;
}

export interface CreatorSummary {
  creator_id: number;
  email: string;
  role: string;
  total_generated: number;
  total_published: number;
  published_this_week: number;
  published_this_month: number;
  published_this_year: number;
  scheduled_count: number;
  draft_count: number;
  archived_count: number;
  linkedin_count: number;
  instagram_count: number;
  timeline: CreatorTimelinePoint[];
}

export interface GlobalAnalyticsSummary {
  total_creators: number;
  total_posters_generated: number;
  total_published: number;
  published_this_week: number;
  published_this_month: number;
  published_this_year: number;
  total_scheduled: number;
  total_archived: number;
  creators: CreatorSummary[];
}

export interface PosterRevision {
  id: number;
  poster_id: number;
  revision_number: number;
  diff_summary: Record<string, { old: string; new: string }>;
  created_at: string;
}

export interface ScheduledJob {
  id: number;
  poster_id: number;
  platform: 'linkedin' | 'instagram';
  scheduled_for?: string;
  scheduled_time?: string;
  status: 'pending' | 'processing' | 'success' | 'failed';
  error_message?: string | null;
  error_log?: string | null;
  platform_post_id?: string | null;
  created_at: string;
}

export interface Brand {
  id: number;
  team_name: string;
  logo_url?: string | null;
  primary_color: string;
  secondary_color: string;
  font_family: string;
  tone_of_voice: string;
  banned_words: string[];
  default_hashtags: string[];
}

export interface KnowledgeSummary {
  brand_id: number;
  occasions: Array<{ id: number; name: string }>;
  top_templates: Array<{ id: number; template_name: string; approval_count: number }>;
  confirmed_rules: Array<{ id: number; rule_text: string; is_confirmed: boolean }>;
  active_style_rules?: Array<{ id: number; rule_text: string; is_confirmed: boolean }>;
}
