/**
 * API Client for Financial RAG Chatbot Backend
 */
import axios, { AxiosInstance } from 'axios';
import type {
  ChatSession,
  ChatMessage,
  Company,
  FeedbackSubmit,
  UploadStatus,
  ExportRequest,
} from '../types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 600000, // 600 seconds (10 minutes) for deep analytics extraction
    });
  }

  // ============================================================================
  // SESSION ENDPOINTS
  // ============================================================================

  async createSession(companyId: string, companyName: string): Promise<ChatSession> {
    const response = await this.client.post('/api/chat/session', {
      company_id: companyId,
      company_name: companyName,
      session_metadata: {},
    });
    return response.data;
  }

  async getSession(sessionId: string): Promise<ChatSession> {
    const response = await this.client.get(`/api/chat/session/${sessionId}`);
    return response.data;
  }

  async deleteSession(sessionId: string): Promise<void> {
    await this.client.delete(`/api/chat/session/${sessionId}`);
  }

  // ============================================================================
  // CHAT ENDPOINTS
  // ============================================================================

  async sendQuery(
    query: string,
    sessionId: string,
    companyId: string,
    topK: number = 5
  ): Promise<any> {
    const response = await this.client.post('/api/chat/query', {
      query,
      session_id: sessionId,
      company_id: companyId,
      top_k: topK,
    });
    return response.data;
  }

  async getChatHistory(sessionId: string, limit: number = 100, offset: number = 0): Promise<{
    session: ChatSession;
    messages: ChatMessage[];
    total_messages: number;
  }> {
    const response = await this.client.get(`/api/chat/history/${sessionId}`, {
      params: { limit, offset },
    });
    return response.data;
  }

  // ============================================================================
  // FEEDBACK ENDPOINTS (RLHF)
  // ============================================================================

  async submitFeedback(messageId: number, sessionId: string, feedbackScore: 0 | 0.5 | 1): Promise<any> {
    const response = await this.client.post('/api/feedback/submit', {
      message_id: messageId,
      session_id: sessionId,
      feedback_score: feedbackScore,
    });
    return response.data;
  }

  async getBadFeedback(limit: number = 50, offset: number = 0): Promise<any[]> {
    const response = await this.client.get('/api/feedback/bad', {
      params: { limit, offset },
    });
    return response.data;
  }

  async getMediumFeedback(limit: number = 50, offset: number = 0): Promise<any[]> {
    const response = await this.client.get('/api/feedback/medium', {
      params: { limit, offset },
    });
    return response.data;
  }

  async getFeedbackNeedsReview(limit: number = 50, offset: number = 0): Promise<any[]> {
    const response = await this.client.get('/api/feedback/needs-review', {
      params: { limit, offset },
    });
    return response.data;
  }

  async getFeedbackSummaryByCompany(companyId: string): Promise<any> {
    const response = await this.client.get(`/api/feedback/summary/company/${companyId}`);
    return response.data;
  }

  // ============================================================================
  // UPLOAD ENDPOINTS
  // ============================================================================

  async uploadPDF(
    file: File,
    companyId: string,
    companyName: string,
    fiscalYear?: string,
    sessionId?: string,
    onProgress?: (progress: number) => void
  ): Promise<{ upload_id: number; message: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('company_id', companyId);
    formData.append('company_name', companyName);
    if (fiscalYear) formData.append('fiscal_year', fiscalYear);
    if (sessionId) formData.append('session_id', sessionId);

    const response = await this.client.post('/api/upload/pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  }

  async getUploadStatus(uploadId: number): Promise<UploadStatus> {
    const response = await this.client.get(`/api/upload/status/${uploadId}`);
    return response.data;
  }

  getIngestionWebSocketUrl(uploadId: number): string {
    const wsUrl = API_URL.replace('http', 'ws');
    return `${wsUrl}/api/upload/ws/${uploadId}`;
  }

  async getCompanies(): Promise<{ companies: Company[]; total_count: number }> {
    const response = await this.client.get('/api/upload/companies');
    return response.data;
  }

  // ============================================================================
  // EXPORT ENDPOINTS
  // ============================================================================

  async exportSession(request: ExportRequest): Promise<any> {
    const response = await this.client.post('/api/export/session', request);
    return response.data;
  }

  async downloadExport(exportId: number): Promise<Blob> {
    const response = await this.client.get(`/api/export/download/${exportId}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // ============================================================================
  // SUGGESTIONS API
  // ============================================================================

  async generateSuggestions(companyId: string, companyName: string, numQuestions: number = 4): Promise<{
    questions: string[];
    company_id: string;
    company_name: string;
  }> {
    const response = await this.client.post('/api/suggestions/generate', {
      company_id: companyId,
      company_name: companyName,
      num_questions: numQuestions
    });
    return response.data;
  }

  async getCachedSuggestions(companyId: string, numQuestions: number = 4): Promise<{
    questions: string[];
    company_id: string;
    company_name: string;
  }> {
    const response = await this.client.get(`/api/suggestions/${companyId}`, {
      params: { num_questions: numQuestions }
    });
    return response.data;
  }

  // ============================================================================
  // ANALYTICS API
  // ============================================================================

  async generateAnalytics(
    companyId: string,
    companyName: string,
    tickerSymbol?: string,
    forceRefresh: boolean = false
  ): Promise<any> {
    const response = await this.client.post('/api/analytics/generate', {
      company_id: companyId,
      company_name: companyName,
      ticker_symbol: tickerSymbol,
      force_refresh: forceRefresh
    });
    return response.data;
  }

  async getAnalytics(companyId: string, tickerSymbol?: string): Promise<any> {
    const response = await this.client.get(`/api/analytics/${companyId}`, {
      params: tickerSymbol ? { ticker_symbol: tickerSymbol } : {}
    });
    return response.data;
  }

  // ============================================================================
  // HEALTH CHECK
  // ============================================================================

  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;
