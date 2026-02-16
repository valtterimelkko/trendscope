// Database types will be generated from Supabase
// For now, we'll define the core types manually

export type UserTier = 'free' | 'solo' | 'agency' | 'enterprise';
export type UserStatus = 'active' | 'paused' | 'cancelled';

export interface Profile {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  tier: UserTier;
  status: UserStatus;
  stripe_customer_id?: string;
  stripe_subscription_id?: string;
  email_notifications: boolean;
  created_at: string;
  updated_at: string;
}

export interface Niche {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  hashtag_count: number;
  is_active: boolean;
  created_at: string;
}

export interface UserNiche {
  id: string;
  user_id: string;
  niche_id: string;
  alert_enabled: boolean;
  velocity_threshold: number;
  created_at: string;
}

export interface Trend {
  id: string;
  type: 'sound' | 'hashtag' | 'format';
  identifier: string;
  display_name: string;
  niche_id: string;
  velocity_score: number;
  saturation_percentage: number;
  video_count: number;
  growth_rate: number;
  detection_timestamp: string;
  peak_timestamp?: string;
  status: 'emerging' | 'peaking' | 'declining' | 'expired';
  example_videos: string[];
  related_tags: string[];
  created_at: string;
  updated_at: string;
}

export interface Alert {
  id: string;
  user_id: string;
  trend_id: string;
  delivered_at: string;
  channel: 'slack' | 'email' | 'webhook';
  status: 'sent' | 'failed' | 'dismissed';
  created_at: string;
}

export interface AlertIntegration {
  id: string;
  user_id: string;
  type: 'slack' | 'webhook' | 'discord';
  name: string;
  config: {
    webhook_url?: string;
    channel?: string;
    format?: string;
  };
  is_active: boolean;
  last_tested_at?: string;
  created_at: string;
  updated_at: string;
}
