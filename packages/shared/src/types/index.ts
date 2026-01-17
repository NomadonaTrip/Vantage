/**
 * Database-aligned TypeScript types for Vantage.
 *
 * These types mirror the database schema and Pydantic models.
 */

// Enums matching database ENUM types
export type UserRole = 'admin' | 'agency_owner' | 'agency_member';
export type LeadStatus = 'new' | 'contacted' | 'qualified' | 'converted' | 'rejected';
export type LeadSource = 'upwork' | 'reddit' | 'apollo' | 'clutch' | 'bing' | 'google' | 'manual';
export type SearchStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

// Core entity types
export interface User {
  id: string;
  email: string;
  role: UserRole;
  created_at: string;
  updated_at: string;
}

export interface ClientProfile {
  id: string;
  user_id: string;
  company_name: string;
  industry: string;
  ideal_client_description: string | null;
  keywords: string[];
  negative_keywords: string[];
  quality_threshold: number;
  created_at: string;
  updated_at: string;
}

export interface Search {
  id: string;
  client_profile_id: string;
  status: SearchStatus;
  sources: LeadSource[];
  quality_min: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface Lead {
  id: string;
  search_id: string;
  source: LeadSource;
  source_url: string | null;
  company_name: string | null;
  contact_name: string | null;
  contact_email_encrypted: string | null;
  contact_phone_encrypted: string | null;
  title: string | null;
  content_snippet: string | null;
  quality_score: number;
  intent_signals: Record<string, unknown>;
  status: LeadStatus;
  status_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  client_profile_id: string;
  messages: ConversationMessage[];
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

// Database type for Supabase
export interface Database {
  public: {
    Tables: {
      users: {
        Row: User;
        Insert: Omit<User, 'id' | 'created_at' | 'updated_at'>;
        Update: Partial<Omit<User, 'id' | 'created_at'>>;
      };
      client_profiles: {
        Row: ClientProfile;
        Insert: Omit<ClientProfile, 'id' | 'created_at' | 'updated_at'>;
        Update: Partial<Omit<ClientProfile, 'id' | 'created_at'>>;
      };
      searches: {
        Row: Search;
        Insert: Omit<Search, 'id' | 'created_at'>;
        Update: Partial<Omit<Search, 'id' | 'created_at'>>;
      };
      leads: {
        Row: Lead;
        Insert: Omit<Lead, 'id' | 'created_at' | 'updated_at'>;
        Update: Partial<Omit<Lead, 'id' | 'created_at'>>;
      };
      conversations: {
        Row: Conversation;
        Insert: Omit<Conversation, 'id' | 'created_at' | 'updated_at'>;
        Update: Partial<Omit<Conversation, 'id' | 'created_at'>>;
      };
    };
    Enums: {
      user_role: UserRole;
      lead_status: LeadStatus;
      lead_source: LeadSource;
      search_status: SearchStatus;
    };
  };
}
