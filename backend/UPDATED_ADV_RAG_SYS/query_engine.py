"""
Query Engine - Financial RAG V2

Complete query interface that ties all components together.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import json

from hybrid_retrieval import HybridRetrievalEngine
from retrieval_types import RetrievalResult
from llm_integration import DualLLMSystem, format_chunks_for_llm
from section_context_detector import extract_statement_type_from_query, extract_note_number_from_query


@dataclass
class QueryResponse:
    """Response to a user query"""
    query: str
    answer: str
    sources: List[Dict]  # Source chunks with metadata
    retrieval_tier_used: str  # 'vector', 'keyword', 'hybrid'
    model_used: str
    success: bool
    error: Optional[str] = None


class FinancialRAGV2:
    """
    Financial RAG V2 - Complete Query System

    Usage:
        rag = FinancialRAGV2()
        answer = rag.query("What is the Fair Value of Investment Properties?", "PHX_FXD")
        print(answer)
    """

    def __init__(
        self,
        db_config: Optional[Dict[str, str]] = None,
        text_llm_endpoint: str = "http://10.100.20.76:11434/v1/chat/completions",
        text_llm_model: str = "phi4:14b"
    ):
        """
        Initialize Financial RAG V2 system

        Args:
            db_config: PostgreSQL connection config (uses defaults if None)
            text_llm_endpoint: LLM endpoint
            text_llm_model: LLM model name (default: phi4:14b)
        """
        # Default database config
        if db_config is None:
            db_config = {
                'host': 'localhost',
                'database': 'financial_rag',
                'user': 'postgres',
                'password': 'Prasanna!@#2002'
            }

        # Initialize components
        self.retrieval_engine = HybridRetrievalEngine(db_config)
        self.llm_system = DualLLMSystem(
            text_llm_endpoint=text_llm_endpoint,
            text_llm_model=text_llm_model
        )

    def query(
        self,
        query: str,
        company_id: str,
        top_k: int = 5,
        section_filters: Optional[List[str]] = None,
        verbose: bool = False
    ) -> QueryResponse:
        """
        Query the financial RAG system

        Args:
            query: User query
            company_id: Company identifier (e.g., 'PHX_FXD')
            top_k: Number of chunks to retrieve
            section_filters: Optional section type filters
            verbose: Whether to print detailed info

        Returns:
            QueryResponse with answer and sources
        """
        if verbose:
            print("="*80)
            print("FINANCIAL RAG V2 - QUERY")
            print("="*80)
            print(f"\nQuery: {query}")
            print(f"Company: {company_id}")
            print(f"Top-K: {top_k}")
            if section_filters:
                print(f"Section filters: {section_filters}")
            print()

        try:
            # NEW: Parse query for section context
            statement_type = extract_statement_type_from_query(query)
            note_number = extract_note_number_from_query(query)

            if verbose:
                print("Step 0: Parsing query for context...")
                if statement_type:
                    print(f"  -> Detected statement type: {statement_type.upper()}")
                if note_number:
                    print(f"  -> Detected note number: {note_number}")
                if not statement_type and not note_number:
                    print(f"  -> No specific section context detected")
                print()

            # Step 1: Retrieve relevant chunks with section context
            if verbose:
                print("Step 1: Retrieving relevant chunks...")

            retrieval_results = self.retrieval_engine.retrieve(
                query=query,
                company_id=company_id,
                top_k=top_k,
                section_filters=section_filters,
                statement_type=statement_type,  # NEW
                note_number=note_number  # NEW
            )

            if not retrieval_results:
                return QueryResponse(
                    query=query,
                    answer="No relevant information found in the database. Please check if the PDF has been ingested for this company.",
                    sources=[],
                    retrieval_tier_used='none',
                    model_used='none',
                    success=False,
                    error="No retrieval results"
                )

            if verbose:
                print(f"  -> Retrieved {len(retrieval_results)} chunks")
                print(f"  -> Retrieval tiers: {set(r.retrieval_tier for r in retrieval_results)}")
                print()

            # Determine which retrieval tier was used
            retrieval_tier = 'hybrid' if len(set(r.retrieval_tier for r in retrieval_results)) > 1 else retrieval_results[0].retrieval_tier

            # Step 2: Extract answer using LLM
            if verbose:
                print("Step 2: Extracting answer with LLM...")

            chunks_for_llm = format_chunks_for_llm(retrieval_results)

            llm_response = self.llm_system.extract_answer(
                query=query,
                context_chunks=chunks_for_llm,
                statement_type=statement_type,  # NEW: Pass section context to LLM
                query_type=self._detect_query_type(query)  # NEW: Detect objective vs subjective
            )

            if not llm_response.success:
                return QueryResponse(
                    query=query,
                    answer="Failed to extract answer from retrieved context.",
                    sources=self._format_sources(retrieval_results),
                    retrieval_tier_used=retrieval_tier,
                    model_used=llm_response.model_used,
                    success=False,
                    error=llm_response.error
                )

            if verbose:
                print(f"  -> Answer extracted using {llm_response.model_used}")
                print()
                print("="*80)
                print("ANSWER")
                print("="*80)
                print(llm_response.answer)
                print()
                print("="*80)
                print(f"SOURCES ({len(retrieval_results)} chunks)")
                print("="*80)
                for i, result in enumerate(retrieval_results[:5], 1):
                    print(f"\n[{i}] Page(s) {result.page_numbers}, Score: {result.score:.3f}")
                    print(f"    Sections: {result.section_types}")
                    print(f"    Tier: {result.retrieval_tier}")
                    print(f"    Preview: {result.chunk_text[:150]}...")
                print()

            # Return successful response
            return QueryResponse(
                query=query,
                answer=llm_response.answer,
                sources=self._format_sources(retrieval_results),
                retrieval_tier_used=retrieval_tier,
                model_used=llm_response.model_used,
                success=True
            )

        except Exception as e:
            return QueryResponse(
                query=query,
                answer=f"Error processing query: {str(e)}",
                sources=[],
                retrieval_tier_used='error',
                model_used='none',
                success=False,
                error=str(e)
            )

    def _detect_query_type(self, query: str) -> str:
        """
        Detect if query is objective (numbers/facts) or subjective (explanation/policy)

        Args:
            query: User query

        Returns:
            'objective', 'subjective', or 'mixed'
        """
        query_lower = query.lower()

        # Objective indicators (asking for numbers, values, amounts)
        objective_keywords = [
            'what is', 'how much', 'fair value', 'amount', 'value', 'number',
            'total', 'revenue', 'profit', 'depreciation rate', 'percentage',
            'figure', 'balance', 'worth', 'cost', 'price', 'rate'
        ]

        # Subjective indicators (asking for explanations, policies, methods)
        subjective_keywords = [
            'why', 'how', 'explain', 'describe', 'policy', 'method',
            'basis', 'determined', 'assumptions', 'approach', 'methodology',
            'reason', 'rationale', 'criteria', 'process'
        ]

        obj_score = sum(1 for kw in objective_keywords if kw in query_lower)
        subj_score = sum(1 for kw in subjective_keywords if kw in query_lower)

        if obj_score > subj_score:
            return 'objective'
        elif subj_score > obj_score:
            return 'subjective'
        else:
            return 'mixed'

    def _format_sources(self, retrieval_results: List[RetrievalResult]) -> List[Dict]:
        """Format retrieval results as source dictionaries"""
        sources = []
        for result in retrieval_results:
            sources.append({
                'chunk_id': result.chunk_id,
                'text': result.chunk_text,
                'pages': result.page_numbers,
                'sections': result.section_types,
                'note': result.note_number,
                'score': result.score,
                'tier': result.retrieval_tier
            })
        return sources

    def close(self):
        """Close all connections"""
        self.retrieval_engine.close()
        self.llm_system.close()


# ============================================================================
# TEST/DEMO
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("FINANCIAL RAG V2 - QUERY ENGINE TEST")
    print("="*80)

    # Initialize system
    print("\nInitializing Financial RAG V2...")
    rag = FinancialRAGV2()
    print("System initialized!")

    # Note: Can't test actual queries until Phoenix Mills PDF is ingested
    print("\nQuery engine is ready.")
    print("\nNext steps:")
    print("1. Ingest Phoenix Mills PDF:")
    print('   python ingest_pdf.py "D:\\ARCH - OBJ DATA\\Financial_RAG_Production\\pdfs\\PHOENIX.pdf" PHX_FXD --company_name "Phoenix Mills" --fiscal_year "2024-25"')
    print()
    print("2. Test Fair Value query:")
    print('   python query_engine.py "What is the Fair Value of Investment Properties?" PHX_FXD')

    # Close system
    rag.close()

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
