"""
Ingestion Manager - Event Broadcasting System
==============================================
Manages real-time log broadcasting from the ingestion pipeline to WebSocket clients.
"""
import asyncio
from typing import Dict, Set
from collections import deque
import contextvars

# Context variable to track the current upload_id in the execution context
current_upload_id = contextvars.ContextVar("current_upload_id", default=None)

class IngestionBroadcaster:
    """
    Singleton broadcaster that manages per-upload message queues.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IngestionBroadcaster, cls).__new__(cls)
            cls._instance.queues: Dict[int, asyncio.Queue] = {}
            cls._instance.history: Dict[int, deque] = {}
            cls._instance.subscribers: Dict[int, int] = {}
        return cls._instance

    def broadcast(self, upload_id: int, message: str, level: str = "info"):
        """
        Broadcast a message to all subscribers of a specific upload.
        """
        if upload_id is None:
            return

        payload = {
            "upload_id": upload_id,
            "message": message,
            "level": level,
            "timestamp": asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
        }

        # Store in history (last 50 messages)
        if upload_id not in self.history:
            self.history[upload_id] = deque(maxlen=50)
        self.history[upload_id].append(payload)

        # Put into queue for live streaming
        if upload_id in self.queues:
            # We can't use await here because Logger might be called from sync code
            # We use call_soon_threadsafe if we're in a thread
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.call_soon_threadsafe(self.queues[upload_id].put_nowait, payload)
            except RuntimeError:
                # Loop not running (e.g. during shutdown or from a CLI)
                pass

    async def subscribe(self, upload_id: int):
        """
        Create a queue for a new subscriber and yield existing history.
        """
        if upload_id not in self.queues:
            self.queues[upload_id] = asyncio.Queue()
            self.subscribers[upload_id] = 0
        
        self.subscribers[upload_id] += 1
        
        # Initial yield: History
        if upload_id in self.history:
            for msg in self.history[upload_id]:
                yield msg

        # Loop: Listen for new messages
        try:
            while True:
                msg = await self.queues[upload_id].get()
                yield msg
        finally:
            self.subscribers[upload_id] -= 1
            if self.subscribers[upload_id] <= 0:
                # Cleanup if no more subscribers
                # Note: We might want to keep history for a bit, but for now we clean up
                pass

    def cleanup(self, upload_id: int):
        """Force cleanup for an upload"""
        if upload_id in self.queues:
            del self.queues[upload_id]
        if upload_id in self.history:
            del self.history[upload_id]
        if upload_id in self.subscribers:
            del self.subscribers[upload_id]

# Global instance
broadcaster = IngestionBroadcaster()
