"""
RAG Service - Integration with UPDATED_ADV_RAG_SYS

This service wraps the existing Financial RAG system and provides
async methods for the FastAPI application.
"""
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add UPDATED_ADV_RAG_SYS to Python path
CURRENT_DIR = Path(__file__).parent  # services/
BACKEND_DIR = CURRENT_DIR.parent  # backend/
RAG_SYSTEM_PATH = BACKEND_DIR / "UPDATED_ADV_RAG_SYS"  # backend/UPDATED_ADV_RAG_SYS/
sys.path.insert(0, str(RAG_SYSTEM_PATH))

# Import from existing RAG system
from query_engine import FinancialRAGV2, QueryResponse
from master_ingest_annual_report import MasterAnnualReportPipeline
from ingest_pdf import PDFIngestionPipeline


class RAGService:
    """
    Wrapper service for the Financial RAG system

    Provides async methods for FastAPI integration without modifying
    the original RAG system code.
    """

    def __init__(
        self,
        db_config: Optional[Dict[str, str]] = None,
        text_llm_endpoint: str = "http://10.100.20.76:11434/v1/chat/completions",
        text_llm_model: str = "phi4:14b"
    ):
        """
        Initialize RAG service

        Args:
            db_config: PostgreSQL connection config
            text_llm_endpoint: LLM endpoint URL
            text_llm_model: LLM model name
        """
        # Default database config
        if db_config is None:
            db_config = {
                'host': 'localhost',
                'database': 'financial_rag',
                'user': 'postgres',
                'password': 'Prasanna!@#2002'
            }

        self.db_config = db_config
        self.text_llm_endpoint = text_llm_endpoint
        self.text_llm_model = text_llm_model

        # Initialize RAG system
        self.rag = FinancialRAGV2(
            db_config=db_config,
            text_llm_endpoint=text_llm_endpoint,
            text_llm_model=text_llm_model
        )

        # Thread pool for running sync code in async context
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def query(
        self,
        query: str,
        company_id: str,
        top_k: int = 5,
        section_filters: Optional[List[str]] = None,
        verbose: bool = False
    ) -> QueryResponse:
        """
        Query the RAG system (async wrapper)

        Args:
            query: User query
            company_id: Company identifier
            top_k: Number of chunks to retrieve
            section_filters: Optional section filters
            verbose: Print debug info

        Returns:
            QueryResponse from RAG system
        """
        # Run sync query in thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            lambda: self.rag.query(
                query=query,
                company_id=company_id,
                top_k=top_k,
                section_filters=section_filters,
                verbose=verbose
            )
        )
        return response

    async def ingest_pdf(
        self,
        pdf_path: str,
        company_id: str,
        company_name: str,
        fiscal_year: Optional[str] = None
    ) -> Dict:
        """
        Ingest PDF into the system (async wrapper)

        Args:
            pdf_path: Path to PDF file
            company_id: Company identifier
            company_name: Company name
            fiscal_year: Fiscal year (optional)

        Returns:
            Dict with ingestion status
        """
        loop = asyncio.get_event_loop()

        # Use master_ingest_annual_report for full pipeline
        result = await loop.run_in_executor(
            self.executor,
            lambda: self._run_ingestion(pdf_path, company_id, company_name, fiscal_year)
        )

        return result

    def _run_ingestion(
        self,
        pdf_path: str,
        company_id: str,
        company_name: str,
        fiscal_year: Optional[str] = None
    ) -> Dict:
        """
        Run the ingestion pipeline (sync method)

        Returns:
            Dict with status, chunks_created, chunks_stored, error
        """
        try:
            # Use the master ingestion pipeline
            pipeline = MasterAnnualReportPipeline(db_config=self.db_config)

            result = pipeline.ingest_annual_report(
                pdf_path=pdf_path,
                company_id=company_id,
                company_name=company_name,
                fiscal_year=fiscal_year
            )

            pipeline.close()

            # Extract chunks from nested stats
            rag_stats = result.get('stages', {}).get('rag_ingestion', {})

            return {
                'status': result.get('status', 'failed'),  # Check 'status' not 'success'
                'chunks_created': rag_stats.get('chunks_created', 0),
                'chunks_stored': rag_stats.get('chunks_stored', 0),
                'error': result.get('error')
            }

        except Exception as e:
            return {
                'status': 'failed',
                'chunks_created': 0,
                'chunks_stored': 0,
                'error': str(e)
            }

    async def get_available_companies(self) -> List[Dict]:
        """
        Get list of companies in the database

        Returns:
            List of dicts with company_id, company_name, chunk_count
        """
        loop = asyncio.get_event_loop()
        companies = await loop.run_in_executor(
            self.executor,
            self._get_companies_from_db
        )
        return companies

    def _get_companies_from_db(self) -> List[Dict]:
        """
        Query database for available companies (sync method)

        Returns:
            List of companies
        """
        import psycopg2

        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT company_id, company_name, COUNT(*) as chunk_count
                FROM document_chunks_v2
                GROUP BY company_id, company_name
                ORDER BY company_id
            """)

            companies = []
            for row in cursor.fetchall():
                companies.append({
                    'company_id': row[0],
                    'company_name': row[1],
                    'chunk_count': row[2]
                })

            cursor.close()
            conn.close()

            return companies

        except Exception as e:
            print(f"Error fetching companies: {e}")
            return []

    def close(self):
        """Close RAG system and thread pool"""
        self.rag.close()
        self.executor.shutdown(wait=True)


# ============================================================================
# Singleton instance for the application
# ============================================================================

_rag_service_instance = None


def get_rag_service() -> RAGService:
    """
    Get or create singleton RAG service instance

    This ensures only one RAG system is initialized for the entire application.
    """
    global _rag_service_instance

    if _rag_service_instance is None:
        _rag_service_instance = RAGService()

    return _rag_service_instance


def close_rag_service():
    """Close the RAG service singleton"""
    global _rag_service_instance

    if _rag_service_instance is not None:
        _rag_service_instance.close()
        _rag_service_instance = None
