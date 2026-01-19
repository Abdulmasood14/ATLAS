"""
Deep Dive API - Generate Intelligent Questions for Company Reports

Provides endpoints to generate and serve questions in 3 categories:
- General Questions
- Sector-Specific Questions
- Business-Specific Questions
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.question_generator import QuestionGenerator
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/deep-dive", tags=["deep-dive"])


class QuestionRequest(BaseModel):
    company_id: str
    company_name: str


@router.post("/generate-questions")
async def generate_questions(request: QuestionRequest):
    """
    Generate 3 categories of intelligent questions based on uploaded annual report

    **Request Body**:
    - `company_id`: Company identifier (e.g., "KEMP_111")
    - `company_name`: Company name (e.g., "KEMP & Company LTD")

    **Response**:
    - `company_id`: Echo back company ID
    - `company_name`: Echo back company name
    - `detected_sector`: Auto-detected sector (e.g., "Pharmaceuticals", "Technology")
    - `questions`: Object with 3 arrays:
        - `general`: Universal questions for all companies (10 questions)
        - `sector_specific`: Questions tailored to the detected sector (8 questions)
        - `business_specific`: Business strategy and competitive questions (10 questions)
    - `generated_at`: ISO timestamp of generation

    **Example**:
    ```json
    {
      "company_id": "KEMP_111",
      "company_name": "KEMP & Company LTD",
      "detected_sector": "Manufacturing",
      "questions": {
        "general": [
          "What is the company's total revenue for the fiscal year?",
          ...
        ],
        "sector_specific": [
          "What is the production capacity utilization rate?",
          ...
        ],
        "business_specific": [
          "What are the key competitive advantages?",
          ...
        ]
      },
      "generated_at": "2025-12-26T12:00:00"
    }
    ```
    """
    try:
        logger.info(f"Generating questions for {request.company_name} ({request.company_id})")

        # Initialize question generator
        generator = QuestionGenerator()

        # Generate all questions
        result = await generator.generate_all_questions(
            company_id=request.company_id,
            company_name=request.company_name
        )

        logger.info(f"Successfully generated questions for {request.company_name}")
        return result

    except Exception as e:
        logger.error(f"Failed to generate questions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate questions: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "deep-dive-question-generator"
    }
