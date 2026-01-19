"""
Hybrid Retrieval Engine

3-tier retrieval system that combines vector search, keyword fallback, and classification re-ranking.
Guarantees retrieval of Fair Value paragraphs even when vector search fails.
"""
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from typing import List, Dict, Optional, Tuple
import numpy as np
from embedding_pipeline import BGE_M3_EmbeddingPipeline
from retrieval_types import RetrievalResult
from deduplication_utils import smart_deduplicate


class HybridRetrievalEngine:
    """
    3-tier hybrid retrieval system

    Tier 1: Vector Search (HNSW + BGE-M3)
    - Fast semantic similarity search
    - Filtered by classification

    Tier 2: Keyword Fallback (GIN full-text)
    - Exact match guarantee
    - Triggers when vector search returns < threshold results

    Tier 3: Re-ranking (Classification match)
    - Boosts chunks matching query intent
    - Uses section types to improve relevance
    """

    def __init__(
        self,
        db_config: Dict[str, str],
        embedding_pipeline: Optional[BGE_M3_EmbeddingPipeline] = None
    ):
        """
        Initialize retrieval engine

        Args:
            db_config: PostgreSQL connection config
            embedding_pipeline: Optional BGE-M3 pipeline (creates new if None)
        """
        self.db_config = db_config
        self.conn = None
        self.cursor = None

        # Initialize embedding pipeline
        if embedding_pipeline:
            self.embedder = embedding_pipeline
        else:
            self.embedder = BGE_M3_EmbeddingPipeline()

        # Connect to database
        self._connect()

    def _connect(self):
        """Connect to PostgreSQL database"""
        self.conn = psycopg2.connect(**self.db_config)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

    def _ensure_connection(self):
        """Ensure database connection is alive, reconnect if needed"""
        try:
            # Check if connection is alive
            if self.conn is None or self.conn.closed:
                self._connect()
            else:
                # Test connection with a simple query
                self.cursor.execute("SELECT 1")
                self.cursor.fetchone()
        except (psycopg2.OperationalError, psycopg2.InterfaceError, AttributeError):
            # Connection is dead, reconnect
            self._connect()

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.embedder.close()

    def retrieve(
        self,
        query: str,
        company_id: str,
        top_k: int = 10,
        section_filters: Optional[List[str]] = None,
        statement_type: Optional[str] = None,  # NEW: 'consolidated', 'standalone', or None
        note_number: Optional[str] = None,  # NEW: 'Note 10', etc.
        min_vector_results: int = 3,
        enable_deduplication: bool = True,
        similarity_threshold: float = 0.75
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks using hybrid approach

        Args:
            query: User query
            company_id: Company identifier
            top_k: Number of results to return
            section_filters: Optional list of section types to filter by
            statement_type: Optional statement type ('consolidated', 'standalone', or None)
            note_number: Optional note number to filter by ('Note 10', etc.)
            min_vector_results: Minimum results from vector search before triggering keyword fallback
            enable_deduplication: Whether to deduplicate similar chunks (default: True)
            similarity_threshold: Threshold for deduplication similarity (default: 0.75)

        Returns:
            List of RetrievalResult objects, sorted by score
        """
        # Ensure connection is alive before querying
        self._ensure_connection()

        # Tier 1: Vector search
        vector_results = self._vector_search(
            query, company_id, top_k * 3, section_filters, statement_type, note_number  # Get more candidates for deduplication
        )

        # Tier 2: ALWAYS run keyword search to guarantee exact matches
        keyword_results = self._keyword_search(
            query, company_id, top_k * 2, section_filters, statement_type, note_number
        )

        # Combine results (remove duplicates, keep best scores)
        combined = self._merge_results(vector_results, keyword_results)

        # Tier 3: Re-rank by classification
        reranked = self._rerank_by_classification(combined, query, section_filters)

        # Tier 4: Deduplicate to remove similar chunks (NEW)
        if enable_deduplication:
            deduplicated = smart_deduplicate(
                reranked,
                similarity_threshold=similarity_threshold,
                max_chunks=top_k,
                max_per_page=2  # Max 2 chunks from same page
            )
            return deduplicated
        else:
            return reranked[:top_k]

    def _vector_search(
        self,
        query: str,
        company_id: str,
        top_k: int,
        section_filters: Optional[List[str]] = None,
        statement_type: Optional[str] = None,
        note_number: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Tier 1: Vector similarity search using HNSW index

        Args:
            query: User query
            company_id: Company identifier
            top_k: Number of results
            section_filters: Optional section type filters
            statement_type: Optional statement type filter
            note_number: Optional note number filter

        Returns:
            List of RetrievalResult objects
        """
        # Generate query embedding
        embedding_result = self.embedder.embed_single(query)

        if not embedding_result.success:
            print(f"Warning: Failed to generate query embedding: {embedding_result.error}")
            return []

        query_embedding = embedding_result.embedding

        # Build SQL query
        sql = """
            SELECT
                chunk_id,
                chunk_text,
                chunk_type,
                section_types,
                note_number,
                page_numbers,
                statement_type,
                1 - (embedding <=> %s::vector) AS similarity
            FROM document_chunks_v2
            WHERE company_id = %s
        """

        params = [query_embedding, company_id]

        # Add section filters
        if section_filters:
            sql += " AND section_types && %s"
            params.append(section_filters)

        # NEW: Add statement_type filter
        if statement_type:
            sql += " AND statement_type = %s"
            params.append(statement_type)

        # NEW: Add note_number filter
        if note_number:
            sql += " AND note_number = %s"
            params.append(note_number)

        sql += """
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        params.extend([query_embedding, top_k])

        # Execute query
        self.cursor.execute(sql, params)
        rows = self.cursor.fetchall()

        # Convert to RetrievalResult objects
        results = []
        for row in rows:
            results.append(RetrievalResult(
                chunk_id=row.get('chunk_id', 'unknown'),
                chunk_text=row.get('chunk_text', 'No text available'),
                chunk_type=row.get('chunk_type', 'paragraph'),
                section_types=row.get('section_types') or [],
                note_number=row.get('note_number'),
                page_numbers=row.get('page_numbers') or [],
                score=float(row.get('similarity', 0.0)),
                retrieval_tier='vector'
            ))

        return results

    def _keyword_search(
        self,
        query: str,
        company_id: str,
        top_k: int,
        section_filters: Optional[List[str]] = None,
        statement_type: Optional[str] = None,
        note_number: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Tier 2: Keyword search using GIN full-text index

        This guarantees retrieval when vector search fails (e.g., Fair Value paragraphs)

        Args:
            query: User query
            company_id: Company identifier
            top_k: Number of results
            section_filters: Optional section type filters
            statement_type: Optional statement type filter
            note_number: Optional note number filter

        Returns:
            List of RetrievalResult objects
        """
        # Use plainto_tsquery for better handling of plain text queries
        # This automatically handles special characters and doesn't require tsquery syntax

        # Build SQL query
        sql = """
            SELECT
                chunk_id,
                chunk_text,
                chunk_type,
                section_types,
                note_number,
                page_numbers,
                statement_type,
                ts_rank(search_vector, plainto_tsquery('english', %s)) AS rank
            FROM document_chunks_v2
            WHERE company_id = %s
              AND search_vector @@ plainto_tsquery('english', %s)
        """

        params = [query, company_id, query]

        # Add section filters
        if section_filters:
            sql += " AND section_types && %s"
            params.append(section_filters)

        # NEW: Add statement_type filter
        if statement_type:
            sql += " AND statement_type = %s"
            params.append(statement_type)

        # NEW: Add note_number filter
        if note_number:
            sql += " AND note_number = %s"
            params.append(note_number)

        sql += """
            ORDER BY rank DESC
            LIMIT %s
        """
        params.append(top_k)

        try:
            # Execute query
            self.cursor.execute(sql, params)
            rows = self.cursor.fetchall()

            # Convert to RetrievalResult objects
            results = []
            for row in rows:
                # Use .get() or safer access to avoid KeyErrors reported in logs
                results.append(RetrievalResult(
                    chunk_id=row.get('chunk_id', 'unknown'),
                    chunk_text=row.get('chunk_text', 'No text available'),
                    chunk_type=row.get('chunk_type', 'paragraph'),
                    section_types=row.get('section_types') or [],
                    note_number=row.get('note_number'),
                    page_numbers=row.get('page_numbers') or [],
                    score=float(row.get('rank', 0.0)),
                    retrieval_tier='keyword'
                ))

            return results

        except Exception as e:
            # More descriptive error
            print(f"Warning: Keyword search failed for query '{query[:30]}...': {str(e)}")
            return []

    def _merge_results(
        self,
        vector_results: List[RetrievalResult],
        keyword_results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        Merge vector and keyword results, removing duplicates

        Args:
            vector_results: Results from vector search
            keyword_results: Results from keyword search

        Returns:
            Merged list of unique results
        """
        seen_chunk_ids = set()
        merged = []

        # Add vector results first (higher priority)
        for result in vector_results:
            if result.chunk_id not in seen_chunk_ids:
                merged.append(result)
                seen_chunk_ids.add(result.chunk_id)

        # Add keyword results (avoiding duplicates)
        for result in keyword_results:
            if result.chunk_id not in seen_chunk_ids:
                merged.append(result)
                seen_chunk_ids.add(result.chunk_id)

        return merged

    def _rerank_by_classification(
        self,
        results: List[RetrievalResult],
        query: str,
        section_filters: Optional[List[str]] = None
    ) -> List[RetrievalResult]:
        """
        Tier 3: Re-rank results by classification match

        Boosts chunks whose section types match query intent

        Args:
            results: Results to re-rank
            query: User query
            section_filters: Optional section type filters

        Returns:
            Re-ranked results
        """
        query_lower = query.lower()

        # Detect query intent from keywords
        query_section_hints = []

        if 'fair value' in query_lower:
            query_section_hints.append('fair_value')
        if 'investment propert' in query_lower:
            query_section_hints.append('investment_property')
        if 'balance sheet' in query_lower:
            query_section_hints.append('balance_sheet')
        if 'income statement' in query_lower or 'profit' in query_lower:
            query_section_hints.append('income_statement')
        if 'cash flow' in query_lower:
            query_section_hints.append('cash_flow')
        if 'note' in query_lower:
            query_section_hints.append('notes')
        if 'borrowing' in query_lower or 'debt' in query_lower:
            query_section_hints.append('borrowings')
        if 'equity' in query_lower:
            query_section_hints.append('equity')

        # Use section filters if provided
        if section_filters:
            query_section_hints.extend(section_filters)

        # Re-rank results
        for result in results:
            # Boost score if section types match query hints
            section_match_count = 0
            for section_type in result.section_types:
                if section_type in query_section_hints:
                    section_match_count += 1

            if section_match_count > 0:
                # Boost score by 20% per matching section
                boost = 1.0 + (section_match_count * 0.2)
                result.score *= boost
                result.retrieval_tier = 're-ranked'

        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)

        return results


# ============================================================================
# TEST/DEMO
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("HYBRID RETRIEVAL ENGINE - TEST")
    print("="*80)

    # Database config
    db_config = {
        'host': 'localhost',
        'database': 'financial_rag',
        'user': 'postgres',
        'password': 'Abdul@786'
    }

    print("\nInitializing retrieval engine...")

    try:
        # Initialize engine
        engine = HybridRetrievalEngine(db_config)

        print("Retrieval engine initialized successfully!")

        # Note: Can't test actual retrieval yet since we haven't ingested any data
        print("\nRetrieval engine is ready.")
        print("Next step: Build ingestion pipeline to load Phoenix Mills PDF")

        # Close engine
        engine.close()

        print("\n" + "="*80)
        print("TEST COMPLETE - Retrieval engine ready for use")
        print("="*80)

    except Exception as e:
        print(f"\nError: {e}")
        print("\nNote: This is expected if database schema hasn't been created yet.")
        print("Run: psql -U postgres -d financial_rag -f schema.sql")
