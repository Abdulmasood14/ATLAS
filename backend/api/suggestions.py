"""
Suggestions API Routes

Generates dynamic, document-specific suggested questions using Phi-4 LLM.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import requests
import json

from services.rag_service import get_rag_service, RAGService
from database.connection import get_db, DatabaseManager

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])


class SuggestionRequest(BaseModel):
    """Request for generating suggested questions"""
    company_id: str
    company_name: str
    num_questions: int = 4


class SuggestionResponse(BaseModel):
    """Response with suggested questions"""
    questions: List[str]
    company_id: str
    company_name: str


# ============================================================================
# GENERATE DYNAMIC QUESTIONS
# ============================================================================

@router.post("/generate", response_model=SuggestionResponse)
async def generate_suggestions(
    request: SuggestionRequest,
    rag: RAGService = Depends(get_rag_service),
    db: DatabaseManager = Depends(get_db)
):
    """
    Generate dynamic suggested questions based on the company's document

    Uses Phi-4 LLM to analyze a sample of the company's chunks and generate
    relevant, document-specific questions.

    Args:
        request: Company details and number of questions
        rag: RAG service instance
        db: Database manager

    Returns:
        List of suggested questions tailored to the document
    """
    try:
        # 1. Get sample chunks from the company's document
        async with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT chunk_text, section_types, note_number, page_numbers
                FROM document_chunks_v2
                WHERE company_id = %s
                ORDER BY chunk_id ASC
                LIMIT 20
            """, (request.company_id,))

            chunks = cursor.fetchall()

            if not chunks:
                raise HTTPException(
                    status_code=404,
                    detail=f"No chunks found for company {request.company_id}"
                )

        # 2. Build context from sample chunks
        context_parts = []
        seen_sections = set()

        for chunk in chunks:
            # section_types is an array, take first element or 'General'
            section_type = chunk['section_types'][0] if chunk['section_types'] and len(chunk['section_types']) > 0 else 'General'
            if section_type not in seen_sections:
                context_parts.append(f"[{section_type}] {chunk['chunk_text'][:500]}")
                seen_sections.add(section_type)
                if len(context_parts) >= 8:  # Max 8 different sections
                    break

        context = "\n\n".join(context_parts)

        # 3. Create prompt for Phi-4
        prompt = f"""You are analyzing a financial annual report for {request.company_name}.

Based on the following excerpts from the document, generate {request.num_questions} highly relevant, specific questions that a financial analyst would ask about this company.

Document Excerpts:
{context}

Requirements:
- Questions must be specific to THIS company and THIS document
- Focus on financial metrics, risks, strategic initiatives, and operational details
- Questions should be answerable from the document
- Vary question types (metrics, explanations, comparisons, strategic)
- Keep questions concise (under 15 words each)

Output ONLY the questions, one per line, without numbering or bullet points:"""

        # 4. Call Phi-4 LLM
        llm_response = requests.post(
            rag.text_llm_endpoint,
            json={
                "model": rag.text_llm_model,
                "messages": [
                    {"role": "system", "content": "You are a financial document analyst who generates insightful questions."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 300,
                "stream": False
            },
            timeout=180
        )

        if llm_response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"LLM request failed: {llm_response.text}"
            )

        # 5. Parse response
        llm_data = llm_response.json()
        generated_text = llm_data['choices'][0]['message']['content'].strip()

        # Split into questions and clean up
        questions = []
        for line in generated_text.split('\n'):
            line = line.strip()
            # Remove numbering, bullets, or extra whitespace
            line = line.lstrip('0123456789.-•* ').strip()
            if line and len(line) > 10 and '?' in line:
                questions.append(line)

        # Ensure we have the requested number
        if len(questions) < request.num_questions:
            # Add fallback questions if LLM didn't generate enough
            fallback_questions = [
                f"What are the key financial highlights for {request.company_name}?",
                f"What are the main strategic risks mentioned in the report?",
                f"How has the company's revenue evolved?",
                f"What are the major operational initiatives discussed?"
            ]
            questions.extend(fallback_questions[:request.num_questions - len(questions)])

        # Return only requested number
        questions = questions[:request.num_questions]

        return SuggestionResponse(
            questions=questions,
            company_id=request.company_id,
            company_name=request.company_name
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating suggestions: {str(e)}")
        import traceback
        traceback.print_exc()

        # Return fallback questions on error
        fallback_questions = [
            f"What are the key financial metrics for {request.company_name}?",
            f"What strategic risks does the company face?",
            f"What are the company's growth initiatives?",
            f"How does the company generate revenue?"
        ]

        return SuggestionResponse(
            questions=fallback_questions[:request.num_questions],
            company_id=request.company_id,
            company_name=request.company_name
        )


# ============================================================================
# GET CACHED SUGGESTIONS (Optional)
# ============================================================================

@router.get("/{company_id}", response_model=SuggestionResponse)
async def get_cached_suggestions(
    company_id: str,
    num_questions: int = 4,
    rag: RAGService = Depends(get_rag_service),
    db: DatabaseManager = Depends(get_db)
):
    """
    Get cached suggestions or generate new ones

    This endpoint could be extended to cache suggestions in the database
    to avoid regenerating them every time.
    """
    # Get company name first
    async with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT company_name
            FROM document_chunks_v2
            WHERE company_id = %s
            LIMIT 1
        """, (company_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Company not found")

        company_name = row['company_name']

    # Generate fresh suggestions
    return await generate_suggestions(
        SuggestionRequest(
            company_id=company_id,
            company_name=company_name,
            num_questions=num_questions
        ),
        rag=rag,
        db=db
    )
