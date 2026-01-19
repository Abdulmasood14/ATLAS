"""
Shared data types for Financial RAG V2

This module contains common dataclasses used across multiple modules
to avoid circular imports.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RetrievalResult:
    """A single retrieved chunk with score"""
    chunk_id: str
    chunk_text: str
    chunk_type: str
    section_types: List[str]
    note_number: Optional[str]
    page_numbers: List[int]
    score: float
    retrieval_tier: str  # 'vector', 'keyword', 're-ranked'
