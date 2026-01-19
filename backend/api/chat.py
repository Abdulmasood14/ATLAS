"""
Chat API Routes

Handles chat sessions, queries, and message history.
"""
from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID, uuid4
from datetime import datetime
from typing import List
import json
import time

from models.schemas import (
    ChatQueryRequest,
    ChatQueryResponse,
    SessionCreate,
    SessionResponse,
    ChatHistoryResponse,
    ChatMessage
)
from database.connection import get_db, DatabaseManager
from services.rag_service import get_rag_service, RAGService

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ============================================================================
# SESSION ENDPOINTS
# ============================================================================

@router.post("/session", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: DatabaseManager = Depends(get_db)
):
    """
    Create a new chat session

    Args:
        session_data: Session creation data
        db: Database manager

    Returns:
        Created session details
    """
    try:
        async with db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO chat_sessions (user_id, company_id, company_name, session_metadata)
                VALUES (%s, %s, %s, %s)
                RETURNING session_id, user_id, company_id, company_name, created_at, last_activity, is_active
                """,
                (
                    session_data.user_id,
                    session_data.company_id,
                    session_data.company_name,
                    json.dumps(session_data.session_metadata)
                )
            )
            row = cursor.fetchone()

            return SessionResponse(
                session_id=row['session_id'],
                user_id=row['user_id'],
                company_id=row['company_id'],
                company_name=row['company_name'],
                created_at=row['created_at'],
                last_activity=row['last_activity'],
                message_count=0,
                is_active=row['is_active']
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: DatabaseManager = Depends(get_db)
):
    """
    Get session details

    Args:
        session_id: Session UUID
        db: Database manager

    Returns:
        Session details
    """
    try:
        async with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT session_id, user_id, company_id, company_name, created_at, last_activity, is_active
                FROM chat_sessions
                WHERE session_id = %s
                """,
                (str(session_id),)
            )
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Session not found")

            # Get message count
            cursor.execute(
                "SELECT COUNT(*) as count FROM chat_messages WHERE session_id = %s",
                (str(session_id),)
            )
            count_row = cursor.fetchone()

            return SessionResponse(
                session_id=row['session_id'],
                user_id=row['user_id'],
                company_id=row['company_id'],
                company_name=row['company_name'],
                created_at=row['created_at'],
                last_activity=row['last_activity'],
                message_count=count_row['count'],
                is_active=row['is_active']
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: UUID,
    db: DatabaseManager = Depends(get_db)
):
    """
    Delete a chat session and all associated messages

    Args:
        session_id: Session UUID
        db: Database manager

    Returns:
        Success message
    """
    try:
        async with db.get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM chat_sessions WHERE session_id = %s",
                (str(session_id),)
            )

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Session not found")

            return {"success": True, "message": "Session deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


# ============================================================================
# QUERY ENDPOINTS
# ============================================================================

@router.post("/query", response_model=ChatQueryResponse)
async def send_query(
    request: ChatQueryRequest,
    db: DatabaseManager = Depends(get_db),
    rag: RAGService = Depends(get_rag_service)
):
    """
    Send a query to the RAG system

    Args:
        request: Query request
        db: Database manager
        rag: RAG service

    Returns:
        Query response with answer and sources
    """
    try:
        # Track response time
        start_time = time.time()

        # 1. Store user message
        async with db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO chat_messages (session_id, role, content)
                VALUES (%s, %s, %s)
                RETURNING message_id
                """,
                (str(request.session_id), 'user', request.query)
            )
            user_message_id = cursor.fetchone()['message_id']

        # 2. Check for conversational queries (greetings, help, etc.)
        query_lower = request.query.lower().strip()

        # Only trigger for very simple greetings/help, not document questions
        conversational_keywords = ['hi', 'hello', 'hey', 'help']
        document_keywords = ['revenue', 'profit', 'report', 'financial', 'company', 'what', 'how', 'why', 'when', 'where', 'analysis', 'data', 'growth', 'ratio', 'margin']

        # Check if it's a pure conversational query (short and matches keywords exactly)
        is_short = len(query_lower.split()) <= 3
        has_greeting = any(query_lower == keyword or query_lower.startswith(keyword + ' ') or query_lower.startswith(keyword + '!') or query_lower == keyword + '?' for keyword in conversational_keywords)
        has_document_intent = any(kw in query_lower for kw in document_keywords)

        is_conversational = is_short and has_greeting and not has_document_intent

        if is_conversational:
            # Provide a friendly introduction
            response_time_ms = int((time.time() - start_time) * 1000)

            conversational_response = """Hello! I'm **XIRR.ai Atlas**, your AI-powered financial analysis assistant.

I'm designed to help you analyze annual reports and financial documents. Here's what I can do:

**📊 Financial Analysis**
- Answer questions about revenue, profits, expenses, and key financial metrics
- Explain financial ratios and performance indicators
- Compare year-over-year trends

**📈 Strategic Insights**
- Identify risks and opportunities mentioned in reports
- Analyze business strategies and market positioning
- Review operational highlights and challenges

**🔍 Deep Document Search**
- Extract information from specific sections (P&L, Balance Sheet, Notes, etc.)
- Find and cite exact page references
- Provide relevance scores for each answer

**💡 How to Use Me**
- Ask specific questions about the company's financials
- Request analysis of particular sections or metrics
- Explore suggested questions for guided insights

Try asking: "What was the company's revenue growth?" or "What are the key risks mentioned?"

I'm here to help you make sense of complex financial documents quickly and accurately!"""

            query_metadata = {
                'sources': [],
                'retrieval_tier_used': 'conversational',
                'model_used': 'system',
                'success': True,
                'error': None,
                'response_time_ms': response_time_ms
            }

            async with db.get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO chat_messages (session_id, role, content, query_metadata)
                    VALUES (%s, %s, %s, %s)
                    RETURNING message_id, created_at
                    """,
                    (
                        str(request.session_id),
                        'assistant',
                        conversational_response,
                        json.dumps(query_metadata)
                    )
                )
                assistant_message = cursor.fetchone()

            return ChatQueryResponse(
                message_id=assistant_message['message_id'],
                query=request.query,
                answer=conversational_response,
                sources=[],
                retrieval_tier_used='conversational',
                model_used='system',
                success=True,
                error=None,
                created_at=assistant_message['created_at'],
                response_time_ms=response_time_ms
            )

        # 3. Query the RAG system for document-based questions
        rag_response = await rag.query(
            query=request.query,
            company_id=request.company_id,
            top_k=request.top_k,
            section_filters=request.section_filters,
            verbose=False
        )

        # Calculate response time in milliseconds
        response_time_ms = int((time.time() - start_time) * 1000)

        # 3. Store assistant response
        query_metadata = {
            'sources': rag_response.sources,
            'retrieval_tier_used': rag_response.retrieval_tier_used,
            'model_used': rag_response.model_used,
            'success': rag_response.success,
            'error': rag_response.error,
            'response_time_ms': response_time_ms
        }

        async with db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO chat_messages (session_id, role, content, query_metadata)
                VALUES (%s, %s, %s, %s)
                RETURNING message_id, created_at
                """,
                (
                    str(request.session_id),
                    'assistant',
                    rag_response.answer,
                    json.dumps(query_metadata)
                )
            )
            assistant_message = cursor.fetchone()

        # 4. Return response
        return ChatQueryResponse(
            message_id=assistant_message['message_id'],
            query=request.query,
            answer=rag_response.answer,
            sources=rag_response.sources,
            retrieval_tier_used=rag_response.retrieval_tier_used,
            model_used=rag_response.model_used,
            success=rag_response.success,
            error=rag_response.error,
            created_at=assistant_message['created_at'],
            response_time_ms=response_time_ms
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


# ============================================================================
# HISTORY ENDPOINTS
# ============================================================================

@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: UUID,
    limit: int = 100,
    offset: int = 0,
    db: DatabaseManager = Depends(get_db)
):
    """
    Get chat history for a session

    Args:
        session_id: Session UUID
        limit: Maximum messages to return
        offset: Offset for pagination
        db: Database manager

    Returns:
        Chat history with messages
    """
    try:
        # Get session info
        async with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT session_id, user_id, company_id, company_name, created_at, last_activity, is_active
                FROM chat_sessions
                WHERE session_id = %s
                """,
                (str(session_id),)
            )
            session_row = cursor.fetchone()

            if not session_row:
                raise HTTPException(status_code=404, detail="Session not found")

            # Get messages
            cursor.execute(
                """
                SELECT message_id, session_id, role, content, query_metadata, created_at
                FROM chat_messages
                WHERE session_id = %s
                ORDER BY created_at ASC
                LIMIT %s OFFSET %s
                """,
                (str(session_id), limit, offset)
            )
            message_rows = cursor.fetchall()

            # Get total message count
            cursor.execute(
                "SELECT COUNT(*) as count FROM chat_messages WHERE session_id = %s",
                (str(session_id),)
            )
            total_messages = cursor.fetchone()['count']

        # Build response
        messages = [
            ChatMessage(
                message_id=row['message_id'],
                session_id=row['session_id'],
                role=row['role'],
                content=row['content'],
                query_metadata=row['query_metadata'] or {},
                created_at=row['created_at']
            )
            for row in message_rows
        ]

        session = SessionResponse(
            session_id=session_row['session_id'],
            user_id=session_row['user_id'],
            company_id=session_row['company_id'],
            company_name=session_row['company_name'],
            created_at=session_row['created_at'],
            last_activity=session_row['last_activity'],
            message_count=total_messages,
            is_active=session_row['is_active']
        )

        return ChatHistoryResponse(
            session=session,
            messages=messages,
            total_messages=total_messages
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")
