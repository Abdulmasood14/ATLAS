"""
Upload API Routes

Handles PDF file uploads and ingestion status tracking.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from typing import Optional
from uuid import UUID
import os
import shutil
from pathlib import Path
from datetime import datetime
import json

from models.schemas import (
    UploadMetadata,
    UploadStatusResponse,
    UploadInitResponse,
    CompanyInfo,
    CompanyListResponse
)
from database.connection import get_db, DatabaseManager
from services.rag_service import get_rag_service, RAGService
from services.ingestion_manager import current_upload_id, broadcaster

router = APIRouter(prefix="/api/upload", tags=["upload"])

# Upload directory
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# ============================================================================
# PDF UPLOAD
# ============================================================================

@router.post("/pdf", response_model=UploadInitResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company_id: str = Form(...),
    company_name: str = Form(...),
    fiscal_year: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    db: DatabaseManager = Depends(get_db),
    rag: RAGService = Depends(get_rag_service)
):
    """
    Upload PDF and start ingestion process

    Args:
        background_tasks: FastAPI background tasks
        file: PDF file
        company_id: Company identifier
        company_name: Company name
        fiscal_year: Fiscal year (optional)
        session_id: Session ID (optional)
        db: Database manager
        rag: RAG service

    Returns:
        Upload initialization response
    """
    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    if file.size and file.size > 50 * 1024 * 1024:  # 50 MB limit
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")

    try:
        # Save file to upload directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{company_id}_{timestamp}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(file_path)

        # Create upload record in database
        async with db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO company_uploads (
                    session_id, company_id, company_name, fiscal_year,
                    original_filename, file_path, file_size_bytes, upload_status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING upload_id
                """,
                (
                    session_id,
                    company_id,
                    company_name,
                    fiscal_year,
                    file.filename,
                    str(file_path),
                    file_size,
                    'pending'
                )
            )
            upload_id = cursor.fetchone()['upload_id']

        # Start ingestion in background
        background_tasks.add_task(
            _process_pdf_ingestion,
            upload_id=upload_id,
            file_path=str(file_path),
            company_id=company_id,
            company_name=company_name,
            fiscal_year=fiscal_year,
            db=db,
            rag=rag
        )

        return UploadInitResponse(
            upload_id=upload_id,
            message="PDF upload started. Ingestion processing in background.",
            upload_status="processing"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def _process_pdf_ingestion(
    upload_id: int,
    file_path: str,
    company_id: str,
    company_name: str,
    fiscal_year: Optional[str],
    db: DatabaseManager,
    rag: RAGService
):
    """
    Background task to process PDF ingestion
    """
    # Set the current upload_id in the context for log broadcasting
    token = current_upload_id.set(upload_id)
    
    try:
        # Initial broadcast
        broadcaster.broadcast(upload_id, f"Initializing ingestion for company: {company_id}", "info")
        # Update status to processing
        async with db.get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE company_uploads
                SET upload_status = 'processing', ingestion_started_at = NOW()
                WHERE upload_id = %s
                """,
                (upload_id,)
            )

        # Run ingestion
        result = await rag.ingest_pdf(
            pdf_path=file_path,
            company_id=company_id,
            company_name=company_name,
            fiscal_year=fiscal_year
        )

        # Update status based on result
        if result['status'] == 'success':
            async with db.get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE company_uploads
                    SET upload_status = 'completed',
                        ingestion_completed_at = NOW(),
                        chunks_created = %s,
                        chunks_stored = %s
                    WHERE upload_id = %s
                    """,
                    (result['chunks_created'], result['chunks_stored'], upload_id)
                )
        else:
            async with db.get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE company_uploads
                    SET upload_status = 'failed',
                        error_message = %s
                    WHERE upload_id = %s
                    """,
                    (result.get('error', 'Unknown error'), upload_id)
                )

    except Exception as e:
        # Update status to failed
        async with db.get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE company_uploads
                SET upload_status = 'failed',
                    error_message = %s
                WHERE upload_id = %s
                """,
                (str(e), upload_id)
            )

    finally:
        # Reset the context
        current_upload_id.reset(token)
        # Notify completion (optional: we handle cleanup in the WS service usually)
        broadcaster.broadcast(upload_id, "Pipeline background task finished.", "info")


@router.get("/status/{upload_id}", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: int,
    db: DatabaseManager = Depends(get_db)
):
    """
    Get upload and ingestion status

    Args:
        upload_id: Upload ID
        db: Database manager

    Returns:
        Upload status details
    """
    try:
        async with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    upload_id, company_id, company_name, upload_status,
                    chunks_created, chunks_stored, error_message,
                    uploaded_at, ingestion_completed_at
                FROM company_uploads
                WHERE upload_id = %s
                """,
                (upload_id,)
            )
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Upload not found")

            return UploadStatusResponse(
                upload_id=row['upload_id'],
                company_id=row['company_id'],
                company_name=row['company_name'],
                upload_status=row['upload_status'],
                chunks_created=row['chunks_created'],
                chunks_stored=row['chunks_stored'],
                error_message=row['error_message'],
                uploaded_at=row['uploaded_at'],
                ingestion_completed_at=row['ingestion_completed_at']
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


# ============================================================================
# COMPANY MANAGEMENT
# ============================================================================

@router.get("/companies", response_model=CompanyListResponse)
async def get_companies(
    rag: RAGService = Depends(get_rag_service)
):
    """
    Get list of available companies in the database

    Args:
        rag: RAG service

    Returns:
        List of companies with chunk counts
    """
    try:
        companies_data = await rag.get_available_companies()

        companies = [
            CompanyInfo(
                company_id=c['company_id'],
                company_name=c['company_name'] or "Unknown Company",
                chunk_count=c['chunk_count']
            )
            for c in companies_data
        ]

        return CompanyListResponse(
            companies=companies,
            total_count=len(companies)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get companies: {str(e)}")
