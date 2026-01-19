"""
Financial RAG Chatbot - FastAPI Backend

Main application entry point with all routes and middleware.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import json
from uuid import UUID
from typing import Dict
import asyncio

# Import API routers
from api import chat, feedback, upload, export, suggestions, analytics, ws, deep_dive, story

# Import services
from services.rag_service import get_rag_service, close_rag_service
from database.connection import close_db_manager


# ============================================================================
# APPLICATION LIFECYCLE
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager

    Handles startup and shutdown events.
    """
    # Startup
    print("="*80)
    print("FINANCIAL RAG CHATBOT - STARTING UP")
    print("="*80)

    # Initialize RAG service (lazy initialization)
    print("✓ RAG service ready (will initialize on first use)")
    print("✓ Database connection pool ready")

    yield

    # Shutdown
    print("\n" + "="*80)
    print("FINANCIAL RAG CHATBOT - SHUTTING DOWN")
    print("="*80)

    # Close services
    close_rag_service()
    close_db_manager()

    print("✓ All connections closed")
    print("="*80)


# ============================================================================
# CREATE APPLICATION
# ============================================================================

app = FastAPI(
    title="Financial RAG Chatbot API",
    description="Backend API for Financial Document Analysis Chatbot with RLHF",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS middleware - allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

app.include_router(chat.router)
app.include_router(feedback.router)
app.include_router(upload.router)
app.include_router(export.router)
app.include_router(suggestions.router)
app.include_router(analytics.router)
app.include_router(ws.router)
app.include_router(deep_dive.router)
app.include_router(story.router)


# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Financial RAG Chatbot API",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "chat": "/api/chat",
            "feedback": "/api/feedback",
            "upload": "/api/upload",
            "export": "/api/export",
            "suggestions": "/api/suggestions",
            "analytics": "/api/analytics",
            "websocket": "/ws/chat/{session_id}",
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2025-12-18T00:00:00Z"
    }


# ============================================================================
# WEBSOCKET CONNECTION MANAGER
# ============================================================================

class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: dict):
        """Send message to specific session"""
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

    async def send_typing_indicator(self, session_id: str, is_typing: bool):
        """Send typing indicator"""
        await self.send_message(session_id, {
            "type": "typing",
            "is_typing": is_typing
        })


manager = ConnectionManager()


# ============================================================================
# WEBSOCKET ENDPOINT (Real-time chat)
# ============================================================================

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time chat

    Args:
        websocket: WebSocket connection
        session_id: Session UUID

    Protocol:
        Client sends: {"query": "...", "company_id": "...", "top_k": 5}
        Server sends: {"type": "typing", "is_typing": true/false}
                     {"type": "response", "data": {...}}
                     {"type": "error", "error": "..."}
    """
    await manager.connect(session_id, websocket)

    try:
        while True:
            # Receive query from client
            data = await websocket.receive_json()

            query = data.get("query")
            company_id = data.get("company_id")
            top_k = data.get("top_k", 5)

            if not query or not company_id:
                await websocket.send_json({
                    "type": "error",
                    "error": "Missing query or company_id"
                })
                continue

            # Show typing indicator
            await manager.send_typing_indicator(session_id, True)

            try:
                # Get RAG service
                rag = get_rag_service()

                # Query RAG system
                response = await rag.query(
                    query=query,
                    company_id=company_id,
                    top_k=top_k,
                    verbose=False
                )

                # Hide typing indicator
                await manager.send_typing_indicator(session_id, False)

                # Send response
                await websocket.send_json({
                    "type": "response",
                    "data": {
                        "query": query,
                        "answer": response.answer,
                        "sources": response.sources,
                        "model_used": response.model_used,
                        "retrieval_tier_used": response.retrieval_tier_used,
                        "success": response.success,
                        "error": response.error
                    }
                })

            except Exception as e:
                # Hide typing indicator
                await manager.send_typing_indicator(session_id, False)

                # Send error
                await websocket.send_json({
                    "type": "error",
                    "error": str(e)
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        print(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(session_id)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": str(exc)}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    """
    Run the FastAPI application

    Usage:
        python main.py

    Server will start on http://localhost:8000
    API docs available at http://localhost:8000/docs
    """
    print("\n" + "="*80)
    print("FINANCIAL RAG CHATBOT - BACKEND SERVER")
    print("="*80)
    print("\nStarting server...")
    print("API Docs: http://localhost:8000/docs")
    print("API Root: http://localhost:8000")
    print("\nPress Ctrl+C to stop")
    print("="*80 + "\n")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (development only)
        log_level="info"
    )
