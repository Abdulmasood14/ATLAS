"""
Pydantic Models and Schemas for Chatbot API

This module defines all request/response models for the FastAPI application.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from uuid import UUID


# ============================================================================
# CHAT MODELS
# ============================================================================

class ChatMessage(BaseModel):
    """Individual chat message"""
    message_id: Optional[int] = None
    session_id: UUID
    role: Literal["user", "assistant", "system"]
    content: str
    query_metadata: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatQueryRequest(BaseModel):
    """Request to send a query to the RAG system"""
    query: str = Field(..., min_length=1, max_length=5000, description="User query")
    session_id: UUID = Field(..., description="Session ID")
    company_id: str = Field(..., min_length=1, description="Company identifier")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of chunks to retrieve")
    section_filters: Optional[List[str]] = None

    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty or whitespace')
        return v.strip()


class ChatQueryResponse(BaseModel):
    """Response from the RAG system"""
    message_id: int
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    retrieval_tier_used: str
    model_used: str
    success: bool
    error: Optional[str] = None
    created_at: datetime
    response_time_ms: Optional[int] = None


class SessionCreate(BaseModel):
    """Create a new chat session"""
    user_id: Optional[str] = None
    company_id: str
    company_name: str
    session_metadata: Optional[Dict[str, Any]] = {}


class SessionResponse(BaseModel):
    """Chat session response"""
    session_id: UUID
    user_id: Optional[str]
    company_id: str
    company_name: str
    created_at: datetime
    last_activity: datetime
    message_count: Optional[int] = 0
    is_active: bool

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Complete chat history for a session"""
    session: SessionResponse
    messages: List[ChatMessage]
    total_messages: int


# ============================================================================
# FEEDBACK MODELS (RLHF)
# ============================================================================

class FeedbackSubmit(BaseModel):
    """Submit feedback on an assistant response"""
    message_id: int = Field(..., description="Message ID of the assistant response")
    session_id: UUID
    feedback_score: Literal[0.0, 0.5, 1.0] = Field(..., description="0.0=Bad, 0.5=Medium, 1.0=Good")

    @validator('feedback_score')
    def validate_score(cls, v):
        if v not in [0.0, 0.5, 1.0]:
            raise ValueError('Feedback score must be 0.0, 0.5, or 1.0')
        return v


class FeedbackResponse(BaseModel):
    """Feedback submission response"""
    feedback_id: int
    message_id: int
    feedback_score: float
    feedback_timestamp: datetime
    success: bool
    message: str = "Feedback recorded successfully"

    class Config:
        from_attributes = True


class FeedbackDetail(BaseModel):
    """Detailed feedback information (for review)"""
    feedback_id: int
    message_id: int
    session_id: UUID
    user_query: str
    assistant_response: str
    feedback_score: float
    retrieved_chunks: List[Dict[str, Any]]
    model_used: str
    retrieval_tier: str
    company_id: str
    query_type: Optional[str]
    statement_type: Optional[str]
    feedback_timestamp: datetime
    review_status: str
    reviewer_notes: Optional[str]

    class Config:
        from_attributes = True


class FeedbackReview(BaseModel):
    """Update feedback review status"""
    review_status: Literal["pending", "reviewed", "resolved", "ignored"]
    reviewer_notes: Optional[str] = None


class FeedbackSummary(BaseModel):
    """Summary of feedback statistics"""
    total_responses: int
    good_count: int
    medium_count: int
    bad_count: int
    avg_score: float
    unique_sessions: Optional[int] = None


# ============================================================================
# UPLOAD MODELS
# ============================================================================

class UploadMetadata(BaseModel):
    """Metadata for PDF upload"""
    company_id: str = Field(..., min_length=1, max_length=100)
    company_name: str = Field(..., min_length=1, max_length=255)
    fiscal_year: Optional[str] = Field(None, max_length=20)
    session_id: Optional[UUID] = None


class UploadStatusResponse(BaseModel):
    """PDF upload and ingestion status"""
    upload_id: int
    company_id: str
    company_name: str
    upload_status: Literal["pending", "processing", "completed", "failed"]
    chunks_created: Optional[int] = None
    chunks_stored: Optional[int] = None
    error_message: Optional[str] = None
    uploaded_at: datetime
    ingestion_completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UploadInitResponse(BaseModel):
    """Response when upload is initiated"""
    upload_id: int
    message: str
    upload_status: str


# ============================================================================
# EXPORT MODELS
# ============================================================================

class ExportRequest(BaseModel):
    """Request to export session data"""
    session_id: UUID
    export_format: Literal["json", "csv", "xlsx"] = "json"
    include_feedback: bool = True
    include_sources: bool = True


class ExportResponse(BaseModel):
    """Export creation response"""
    export_id: int
    session_id: UUID
    export_format: str
    file_path: str
    file_size_bytes: Optional[int]
    message_count: int
    created_at: datetime
    download_url: str

    class Config:
        from_attributes = True


# ============================================================================
# COMPANY MODELS
# ============================================================================

class CompanyInfo(BaseModel):
    """Company information"""
    company_id: str
    company_name: str
    chunk_count: int
    fiscal_year: Optional[str] = None


class CompanyListResponse(BaseModel):
    """List of available companies"""
    companies: List[CompanyInfo]
    total_count: int


# ============================================================================
# WEBSOCKET MODELS
# ============================================================================

class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: Literal["query", "response", "error", "status", "typing"]
    session_id: UUID
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None


class WebSocketQueryMessage(BaseModel):
    """WebSocket query message"""
    query: str
    company_id: str
    top_k: Optional[int] = 5


class WebSocketResponseMessage(BaseModel):
    """WebSocket response message"""
    message_id: int
    answer: str
    sources: List[Dict[str, Any]]
    model_used: str
    retrieval_tier_used: str


# ============================================================================
# ERROR MODELS
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


# ============================================================================
# ANALYTICS MODELS (for future admin dashboard)
# ============================================================================

class SessionAnalytics(BaseModel):
    """Session analytics summary"""
    total_sessions: int
    active_sessions: int
    total_messages: int
    total_queries: int
    avg_messages_per_session: float
    most_active_company: Optional[str]


class FeedbackAnalyticsByCompany(BaseModel):
    """Feedback analytics by company"""
    company_id: str
    total_responses: int
    good_count: int
    medium_count: int
    bad_count: int
    avg_score: float
    unique_sessions: int


class FeedbackAnalyticsByModel(BaseModel):
    """Feedback analytics by model"""
    model_used: str
    total_responses: int
    good_count: int
    medium_count: int
    bad_count: int
    avg_score: float


# ============================================================================
# UTILITY MODELS
# ============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
