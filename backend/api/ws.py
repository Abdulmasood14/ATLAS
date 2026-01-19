"""
WebSocket API Routes for Ingestion Logs
=======================================
Provides a real-time stream of ingestion logs to the frontend.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json

from services.ingestion_manager import broadcaster

router = APIRouter(prefix="/api/upload/ws", tags=["upload_ws"])

@router.websocket("/{upload_id}")
async def websocket_ingestion_logs(websocket: WebSocket, upload_id: int):
    """
    WebSocket endpoint for real-time ingestion logs.
    """
    await websocket.accept()
    
    try:
        # Subscribe to ingestion logs for this upload
        async for log_entry in broadcaster.subscribe(upload_id):
            # Send the log entry to the client
            await websocket.send_json({
                "type": "log",
                "data": log_entry
            })
            
            # If the process is finished, we could signal it here
            # But we'll let the client decide when to close or use the status API
            if "Status: SUCCESS" in log_entry["message"] or "Pipeline failed" in log_entry["message"]:
                # Wait a bit before closing to ensure the final message is sent
                await asyncio.sleep(1)
                await websocket.send_json({
                    "type": "status",
                    "data": {"status": "completed" if "SUCCESS" in log_entry["message"] else "failed"}
                })
                break

    except WebSocketDisconnect:
        print(f"Ingestion WebSocket disconnected: {upload_id}")
    except Exception as e:
        print(f"Ingestion WebSocket error for {upload_id}: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        # Note: Broadcaster cleanup happens if no more subscribers
        pass
