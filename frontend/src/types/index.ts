/**
 * TypeScript Type Definitions for Financial RAG Chatbot
 */

export interface ChatMessage {
  message_id?: number;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  query_metadata?: QueryMetadata;
  created_at?: string;
  feedback_score?: number; // 0, 0.5, or 1
}

export interface QueryMetadata {
  sources?: Source[];
  retrieval_tier_used?: string;
  model_used?: string;
  chunk_count?: number;
  success?: boolean;
  error?: string | null;
  response_time_ms?: number;
}

export interface Source {
  chunk_id: number;
  text: string;
  pages: number[];
  sections: string[];
  note: string | null;
  score: number;
  tier: string;
}

export interface ChatSession {
  session_id: string;
  user_id?: string;
  company_id: string;
  company_name: string;
  created_at: string;
  last_activity: string;
  message_count: number;
  is_active: boolean;
}

export interface Company {
  company_id: string;
  company_name: string;
  chunk_count: number;
  fiscal_year?: string;
}

export interface FeedbackSubmit {
  message_id: number;
  session_id: string;
  feedback_score: 0 | 0.5 | 1;
}

export interface UploadStatus {
  upload_id: number;
  company_id: string;
  company_name: string;
  upload_status: 'pending' | 'processing' | 'completed' | 'failed';
  chunks_created?: number;
  chunks_stored?: number;
  error_message?: string;
  uploaded_at: string;
  ingestion_completed_at?: string;
}

export interface ExportRequest {
  session_id: string;
  export_format: 'json' | 'csv' | 'xlsx';
  include_feedback: boolean;
  include_sources: boolean;
}

// WebSocket message types
export interface WSMessage {
  type: 'query' | 'response' | 'error' | 'status' | 'typing';
  session_id?: string;
  data?: any;
  timestamp?: string;
}

// UI State types
export interface AppState {
  currentSession: ChatSession | null;
  currentCompany: Company | null;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
}
