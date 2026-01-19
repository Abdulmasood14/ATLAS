"""
Feedback API Routes (RLHF)

Handles user feedback submission and review for Reinforcement Learning from Human Feedback.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from uuid import UUID
from typing import List, Optional
import json

from models.schemas import (
    FeedbackSubmit,
    FeedbackResponse,
    FeedbackDetail,
    FeedbackReview,
    FeedbackSummary
)
from database.connection import get_db, DatabaseManager

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


# ============================================================================
# FEEDBACK SUBMISSION
# ============================================================================

@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackSubmit,
    db: DatabaseManager = Depends(get_db)
):
    """
    Submit feedback on an assistant response

    Args:
        feedback: Feedback data (message_id, score)
        db: Database manager

    Returns:
        Feedback submission confirmation
    """
    try:
        async with db.get_cursor() as cursor:
            # 1. Get the assistant message and previous user message
            cursor.execute(
                """
                SELECT
                    m.message_id,
                    m.session_id,
                    m.content as assistant_response,
                    m.query_metadata,
                    prev_m.content as user_query,
                    cs.company_id
                FROM chat_messages m
                JOIN chat_messages prev_m ON prev_m.session_id = m.session_id
                    AND prev_m.message_id < m.message_id
                    AND prev_m.role = 'user'
                JOIN chat_sessions cs ON cs.session_id = m.session_id
                WHERE m.message_id = %s AND m.role = 'assistant'
                ORDER BY prev_m.message_id DESC
                LIMIT 1
                """,
                (feedback.message_id,)
            )

            message_row = cursor.fetchone()

            if not message_row:
                raise HTTPException(status_code=404, detail="Message not found")

            # 2. Extract metadata
            metadata = message_row['query_metadata'] or {}
            retrieved_chunks = metadata.get('sources', [])
            model_used = metadata.get('model_used', 'unknown')
            retrieval_tier = metadata.get('retrieval_tier_used', 'unknown')

            # 3. Check if feedback already exists for this message
            cursor.execute(
                "SELECT feedback_id FROM feedback_responses WHERE message_id = %s",
                (feedback.message_id,)
            )
            existing_feedback = cursor.fetchone()

            if existing_feedback:
                # Update existing feedback
                cursor.execute(
                    """
                    UPDATE feedback_responses
                    SET feedback_score = %s, feedback_timestamp = NOW()
                    WHERE message_id = %s
                    RETURNING feedback_id, feedback_timestamp
                    """,
                    (feedback.feedback_score, feedback.message_id)
                )
                result = cursor.fetchone()
                message = "Feedback updated successfully"

            else:
                # Insert new feedback
                cursor.execute(
                    """
                    INSERT INTO feedback_responses (
                        message_id, session_id, user_query, assistant_response,
                        feedback_score, retrieved_chunks, model_used, retrieval_tier,
                        company_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING feedback_id, feedback_timestamp
                    """,
                    (
                        feedback.message_id,
                        str(message_row['session_id']),
                        message_row['user_query'],
                        message_row['assistant_response'],
                        feedback.feedback_score,
                        json.dumps(retrieved_chunks),
                        model_used,
                        retrieval_tier,
                        message_row['company_id']
                    )
                )
                result = cursor.fetchone()
                message = "Feedback recorded successfully"

            return FeedbackResponse(
                feedback_id=result['feedback_id'],
                message_id=feedback.message_id,
                feedback_score=feedback.feedback_score,
                feedback_timestamp=result['feedback_timestamp'],
                success=True,
                message=message
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")


# ============================================================================
# FEEDBACK RETRIEVAL (for review/analysis)
# ============================================================================

@router.get("/bad", response_model=List[FeedbackDetail])
async def get_bad_feedback(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: DatabaseManager = Depends(get_db)
):
    """
    Get all bad feedback responses (score = 0.0) for review

    Args:
        limit: Maximum results to return
        offset: Offset for pagination
        db: Database manager

    Returns:
        List of bad feedback entries
    """
    return await _get_feedback_by_score(0.0, limit, offset, db)


@router.get("/medium", response_model=List[FeedbackDetail])
async def get_medium_feedback(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: DatabaseManager = Depends(get_db)
):
    """
    Get all medium feedback responses (score = 0.5) for review

    Args:
        limit: Maximum results to return
        offset: Offset for pagination
        db: Database manager

    Returns:
        List of medium feedback entries
    """
    return await _get_feedback_by_score(0.5, limit, offset, db)


@router.get("/good", response_model=List[FeedbackDetail])
async def get_good_feedback(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: DatabaseManager = Depends(get_db)
):
    """
    Get all good feedback responses (score = 1.0)

    Args:
        limit: Maximum results to return
        offset: Offset for pagination
        db: Database manager

    Returns:
        List of good feedback entries
    """
    return await _get_feedback_by_score(1.0, limit, offset, db)


@router.get("/needs-review", response_model=List[FeedbackDetail])
async def get_feedback_needs_review(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: DatabaseManager = Depends(get_db)
):
    """
    Get feedback that needs review (bad or medium, not yet reviewed)

    Args:
        limit: Maximum results
        offset: Offset for pagination
        db: Database manager

    Returns:
        List of feedback needing review
    """
    try:
        async with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    feedback_id, message_id, session_id, user_query, assistant_response,
                    feedback_score, retrieved_chunks, model_used, retrieval_tier,
                    company_id, query_type, statement_type, feedback_timestamp,
                    review_status, reviewer_notes
                FROM feedback_responses
                WHERE feedback_score < 1.0 AND review_status = 'pending'
                ORDER BY feedback_timestamp DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset)
            )
            rows = cursor.fetchall()

            return [
                FeedbackDetail(
                    feedback_id=row['feedback_id'],
                    message_id=row['message_id'],
                    session_id=row['session_id'],
                    user_query=row['user_query'],
                    assistant_response=row['assistant_response'],
                    feedback_score=float(row['feedback_score']),
                    retrieved_chunks=row['retrieved_chunks'] or [],
                    model_used=row['model_used'],
                    retrieval_tier=row['retrieval_tier'],
                    company_id=row['company_id'],
                    query_type=row['query_type'],
                    statement_type=row['statement_type'],
                    feedback_timestamp=row['feedback_timestamp'],
                    review_status=row['review_status'],
                    reviewer_notes=row['reviewer_notes']
                )
                for row in rows
            ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")


async def _get_feedback_by_score(
    score: float,
    limit: int,
    offset: int,
    db: DatabaseManager
) -> List[FeedbackDetail]:
    """
    Helper function to get feedback by score

    Args:
        score: Feedback score (0.0, 0.5, or 1.0)
        limit: Maximum results
        offset: Offset for pagination
        db: Database manager

    Returns:
        List of feedback entries
    """
    try:
        async with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    feedback_id, message_id, session_id, user_query, assistant_response,
                    feedback_score, retrieved_chunks, model_used, retrieval_tier,
                    company_id, query_type, statement_type, feedback_timestamp,
                    review_status, reviewer_notes
                FROM feedback_responses
                WHERE feedback_score = %s
                ORDER BY feedback_timestamp DESC
                LIMIT %s OFFSET %s
                """,
                (score, limit, offset)
            )
            rows = cursor.fetchall()

            return [
                FeedbackDetail(
                    feedback_id=row['feedback_id'],
                    message_id=row['message_id'],
                    session_id=row['session_id'],
                    user_query=row['user_query'],
                    assistant_response=row['assistant_response'],
                    feedback_score=float(row['feedback_score']),
                    retrieved_chunks=row['retrieved_chunks'] or [],
                    model_used=row['model_used'],
                    retrieval_tier=row['retrieval_tier'],
                    company_id=row['company_id'],
                    query_type=row['query_type'],
                    statement_type=row['statement_type'],
                    feedback_timestamp=row['feedback_timestamp'],
                    review_status=row['review_status'],
                    reviewer_notes=row['reviewer_notes']
                )
                for row in rows
            ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")


# ============================================================================
# FEEDBACK REVIEW
# ============================================================================

@router.patch("/{feedback_id}/review")
async def update_feedback_review(
    feedback_id: int,
    review: FeedbackReview,
    reviewer_name: Optional[str] = None,
    db: DatabaseManager = Depends(get_db)
):
    """
    Update feedback review status

    Args:
        feedback_id: Feedback ID
        review: Review update data
        reviewer_name: Name of reviewer (optional)
        db: Database manager

    Returns:
        Success message
    """
    try:
        async with db.get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE feedback_responses
                SET review_status = %s,
                    reviewer_notes = %s,
                    reviewed_at = NOW(),
                    reviewed_by = %s
                WHERE feedback_id = %s
                """,
                (review.review_status, review.reviewer_notes, reviewer_name, feedback_id)
            )

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Feedback not found")

            return {
                "success": True,
                "message": f"Feedback review updated to '{review.review_status}'"
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update review: {str(e)}")


# ============================================================================
# FEEDBACK ANALYTICS
# ============================================================================

@router.get("/summary/company/{company_id}", response_model=FeedbackSummary)
async def get_feedback_summary_by_company(
    company_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """
    Get feedback summary for a specific company

    Args:
        company_id: Company identifier
        db: Database manager

    Returns:
        Feedback summary statistics
    """
    try:
        async with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_responses,
                    SUM(CASE WHEN feedback_score = 1.0 THEN 1 ELSE 0 END) as good_count,
                    SUM(CASE WHEN feedback_score = 0.5 THEN 1 ELSE 0 END) as medium_count,
                    SUM(CASE WHEN feedback_score = 0.0 THEN 1 ELSE 0 END) as bad_count,
                    COALESCE(AVG(feedback_score), 0) as avg_score,
                    COUNT(DISTINCT session_id) as unique_sessions
                FROM feedback_responses
                WHERE company_id = %s
                """,
                (company_id,)
            )
            row = cursor.fetchone()

            return FeedbackSummary(
                total_responses=row['total_responses'],
                good_count=row['good_count'],
                medium_count=row['medium_count'],
                bad_count=row['bad_count'],
                avg_score=round(float(row['avg_score']), 2),
                unique_sessions=row['unique_sessions']
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/summary/model/{model_name}", response_model=FeedbackSummary)
async def get_feedback_summary_by_model(
    model_name: str,
    db: DatabaseManager = Depends(get_db)
):
    """
    Get feedback summary for a specific model

    Args:
        model_name: Model name (e.g., 'phi4:14b')
        db: Database manager

    Returns:
        Feedback summary statistics
    """
    try:
        async with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_responses,
                    SUM(CASE WHEN feedback_score = 1.0 THEN 1 ELSE 0 END) as good_count,
                    SUM(CASE WHEN feedback_score = 0.5 THEN 1 ELSE 0 END) as medium_count,
                    SUM(CASE WHEN feedback_score = 0.0 THEN 1 ELSE 0 END) as bad_count,
                    COALESCE(AVG(feedback_score), 0) as avg_score
                FROM feedback_responses
                WHERE model_used = %s
                """,
                (model_name,)
            )
            row = cursor.fetchone()

            return FeedbackSummary(
                total_responses=row['total_responses'],
                good_count=row['good_count'],
                medium_count=row['medium_count'],
                bad_count=row['bad_count'],
                avg_score=round(float(row['avg_score']), 2)
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")
