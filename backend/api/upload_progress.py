"""
Real-time Upload Progress Tracking with Server-Sent Events (SSE)

Provides real progress updates from the ingestion pipeline.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Dict
import asyncio
import json
from datetime import datetime

router = APIRouter(prefix="/api/upload", tags=["upload-progress"])

# Global progress tracker
_progress_trackers: Dict[str, Dict] = {}


class ProgressTracker:
    """Track progress for an upload session"""

    def __init__(self, upload_id: str):
        self.upload_id = upload_id
        self.stages = [
            "Uploading file",
            "Orientation correction",
            "Text extraction & OCR",
            "Section boundary detection",
            "Adaptive chunking",
            "AI chunk classification",
            "Neural embeddings",
            "PostgreSQL vector storage"
        ]
        self.current_stage = 0
        self.progress = 0
        self.status = "uploading"
        self.message = "Starting upload..."
        self.chunks_created = 0

    def update(self, stage: int = None, progress: int = None, message: str = None, chunks: int = None):
        """Update progress"""
        if stage is not None:
            self.current_stage = stage
        if progress is not None:
            self.progress = progress
        if message is not None:
            self.message = message
        if chunks is not None:
            self.chunks_created = chunks

        # Update status based on progress
        if self.progress >= 100:
            self.status = "completed"
        elif self.progress > 0:
            self.status = "processing"

    def get_state(self) -> Dict:
        """Get current state"""
        return {
            "upload_id": self.upload_id,
            "status": self.status,
            "progress": self.progress,
            "current_stage": self.stages[min(self.current_stage, len(self.stages) - 1)],
            "message": self.message,
            "chunks_created": self.chunks_created,
            "timestamp": datetime.now().isoformat()
        }


def get_progress_tracker(upload_id: str) -> ProgressTracker:
    """Get or create progress tracker"""
    if upload_id not in _progress_trackers:
        _progress_trackers[upload_id] = ProgressTracker(upload_id)
    return _progress_trackers[upload_id]


def update_progress(upload_id: str, stage: int = None, progress: int = None, message: str = None, chunks: int = None):
    """Update progress for an upload"""
    tracker = get_progress_tracker(upload_id)
    tracker.update(stage=stage, progress=progress, message=message, chunks=chunks)


async def progress_stream(upload_id: str) -> AsyncGenerator[str, None]:
    """
    Stream progress updates using Server-Sent Events

    Client should listen to this endpoint for real-time progress.
    """
    tracker = get_progress_tracker(upload_id)

    while tracker.status != "completed" and tracker.status != "failed":
        # Send current state
        state = tracker.get_state()
        yield f"data: {json.dumps(state)}\n\n"

        # Wait before next update
        await asyncio.sleep(0.5)  # Update every 500ms

    # Send final state
    state = tracker.get_state()
    yield f"data: {json.dumps(state)}\n\n"


@router.get("/progress/{upload_id}")
async def stream_progress(upload_id: str):
    """
    Stream progress updates via Server-Sent Events

    Usage from frontend:
    ```javascript
    const eventSource = new EventSource(`/api/upload/progress/${uploadId}`);
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data.progress, data.message);
    };
    ```
    """
    return StreamingResponse(
        progress_stream(upload_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/progress-status/{upload_id}")
async def get_progress_status(upload_id: str):
    """Get current progress status (non-streaming)"""
    tracker = get_progress_tracker(upload_id)
    return tracker.get_state()
