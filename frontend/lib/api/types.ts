/**
 * Shared API types matching backend schemas.
 */

// Auth
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  created_at: string;
}

// Profile
export interface UserProfile {
  id: string;
  user_id: string;
  persona: string | null;
  experience_level: string | null;
  biggest_barrier: string | null;
  primary_goal: string | null;
  risk_tolerance: string | null;
  learning_preference: string | null;
  onboarding_completed: boolean;
  created_at: string;
  updated_at: string;
}

// Onboarding
export interface OnboardingQuestion {
  id: string;
  text: string;
  options: OnboardingOption[];
}

export interface OnboardingOption {
  value: string;
  label: string;
  description?: string;
}

export interface OnboardingSection {
  id: string;
  title: string;
  description: string;
  questions: OnboardingQuestion[];
}

export interface OnboardingProgress {
  section: string;
  progress: number;
  is_complete: boolean;
  next_section: string | null;
}

// Chat
export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  last_message_preview?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

// API Error
export interface ApiError {
  detail: string;
}
