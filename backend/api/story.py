"""
Story API - Comprehensive Company Narrative for Investors

Generates a detailed investment story covering:
- Business overview and model
- Financial performance and trends
- Competitive position and advantages
- Risk factors and challenges
- Growth prospects and roadmap
- Investment recommendation (BUY/SELL/HOLD)
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
import asyncio

from services.rag_service import get_rag_service, RAGService

router = APIRouter(prefix="/api/story", tags=["story"])


# ============================================================================
# STORY GENERATION
# ============================================================================

@router.get("/{company_id}")
async def generate_company_story(
    company_id: str,
    rag: RAGService = Depends(get_rag_service)
):
    """
    Generate comprehensive investment story for a company

    Args:
        company_id: Company identifier
        rag: RAG service

    Returns:
        Dict with story narrative, milestones, and recommendation
    """
    try:
        print(f"\n{'='*80}")
        print(f"GENERATING STORY FOR: {company_id}")
        print(f"{'='*80}\n")

        # Define story sections to query in parallel with balanced prompts
        story_queries = [
            {
                'key': 'business_overview',
                'query': """What does this company do? Describe the company's core business activities, products, services, target markets, and revenue model. Include information about their operations, facilities, and industry positioning. Provide a comprehensive overview in 2-3 paragraphs."""
            },
            {
                'key': 'financial_performance',
                'query': """Analyze the company's financial performance. What were the revenue and profit figures for the current year compared to the previous year? What are the key financial metrics like EBITDA, profit margins, ROE, ROCE, and debt ratios? Describe the financial health and trends. Include specific numbers with growth percentages."""
            },
            {
                'key': 'competitive_position',
                'query': """What are the company's competitive advantages and market position? What makes this company unique or better than competitors? Include information about market share, patents, brands, technology, strategic assets, certifications, awards, or any competitive strengths mentioned."""
            },
            {
                'key': 'risk_factors',
                'query': """What are the key risks and challenges facing this company? Look for information about operational risks, market risks, regulatory risks, competitive threats, financial risks, or any concerns mentioned in risk sections. Explain the main risk factors investors should be aware of."""
            },
            {
                'key': 'growth_strategy',
                'query': """What is the company's growth strategy and future plans? Include information about expansion plans, new products, R&D initiatives, capital expenditure, market entry, partnerships, acquisitions, capacity additions, or any strategic initiatives for future growth. Include timelines and targets if mentioned."""
            },
            {
                'key': 'governance_quality',
                'query': """Describe the company's management and governance structure. Who are the key leaders and board members? What is the board composition? What governance practices, committees, or frameworks are in place? Include information about management quality, experience, and any governance awards or recognition."""
            }
        ]

        # Execute all queries in parallel
        print(f"Executing {len(story_queries)} parallel RAG queries for story generation...")

        async def _query_single(query_def):
            try:
                print(f"  [START] {query_def['key']}")
                response = await rag.query(
                    query=query_def['query'],
                    company_id=company_id,
                    top_k=20,  # Increase from 15 to 20 for even better context
                    verbose=False
                )
                print(f"  [DONE] {query_def['key']}: success={response.success}, chunks_retrieved={len(response.sources) if response.sources else 0}")

                # Check if answer is meaningful (not just "Information not available")
                if response.success and response.answer:
                    answer = response.answer.strip()
                    # Filter out non-answers
                    if len(answer) > 50 and not answer.lower().startswith("information not"):
                        print(f"  [SUCCESS] {query_def['key']}: Got {len(answer)} chars")
                        return {
                            'key': query_def['key'],
                            'content': answer,
                            'success': True
                        }

                # FALLBACK: Try with ultra-simple query if first attempt failed
                print(f"  [FALLBACK] {query_def['key']}: Trying simpler query...")
                fallback_queries = {
                    'business_overview': "What does this company do? What are its main products and services?",
                    'financial_performance': "What is the company's revenue and profit? How did it perform financially this year?",
                    'competitive_position': "What are the company's strengths and competitive advantages?",
                    'risk_factors': "What are the main risks and challenges for this company?",
                    'growth_strategy': "What are the company's plans for growth and expansion?",
                    'governance_quality': "Who are the key leaders and board members of this company?"
                }

                if query_def['key'] in fallback_queries:
                    fallback_response = await rag.query(
                        query=fallback_queries[query_def['key']],
                        company_id=company_id,
                        top_k=20,
                        verbose=False
                    )

                    if fallback_response.success and fallback_response.answer:
                        fallback_answer = fallback_response.answer.strip()
                        if len(fallback_answer) > 50 and not fallback_answer.lower().startswith("information not"):
                            print(f"  [FALLBACK SUCCESS] {query_def['key']}: Got {len(fallback_answer)} chars")
                            return {
                                'key': query_def['key'],
                                'content': fallback_answer,
                                'success': True
                            }

                print(f"  [WARNING] {query_def['key']}: No meaningful answer found even after fallback")
                return {
                    'key': query_def['key'],
                    'content': "Information not available in the annual report.",
                    'success': False
                }
            except Exception as e:
                print(f"  [ERROR] {query_def['key']}: {str(e)}")
                return {
                    'key': query_def['key'],
                    'content': "Information not available.",
                    'success': False
                }

        # Run all queries concurrently
        story_sections = await asyncio.gather(*[_query_single(q) for q in story_queries])

        # Convert to dict for easy access
        sections_dict = {s['key']: s['content'] for s in story_sections}

        # Check how many sections succeeded
        successful_sections = [s for s in story_sections if s['success']]
        failed_sections = [s for s in story_sections if not s['success']]

        print(f"\n{'='*80}")
        print(f"SECTION EXTRACTION SUMMARY:")
        print(f"  Total sections: {len(story_sections)}")
        print(f"  Successful: {len(successful_sections)}")
        print(f"  Failed: {len(failed_sections)}")
        if failed_sections:
            print(f"  Failed section keys: {[s['key'] for s in failed_sections]}")
        print(f"{'='*80}\n")

        # Generate final investment recommendation
        print("\n[GENERATING] Investment recommendation...")
        recommendation_query = f"""Based on all available information about this company, provide a clear investment
        recommendation (BUY, SELL, or HOLD) with detailed justification. Consider:

        Business Overview: {sections_dict.get('business_overview', 'N/A')[:500]}...
        Financial Performance: {sections_dict.get('financial_performance', 'N/A')[:500]}...
        Competitive Position: {sections_dict.get('competitive_position', 'N/A')[:500]}...

        Provide a 2-3 paragraph investment thesis with a clear BUY/SELL/HOLD verdict at the end."""

        recommendation_response = await rag.query(
            query=recommendation_query,
            company_id=company_id,
            top_k=15,
            verbose=False
        )

        recommendation = recommendation_response.answer if recommendation_response.success else \
            "Investment recommendation not available. Please consult with a financial advisor."

        print("[DONE] Investment recommendation\n")

        # Extract milestones/roadmap from growth strategy
        milestones = _extract_milestones(sections_dict.get('growth_strategy', ''))

        print(f"{'='*80}")
        print("STORY GENERATION COMPLETE")
        print(f"{'='*80}\n")

        return {
            'company_id': company_id,
            'story': {
                'business_overview': sections_dict.get('business_overview', ''),
                'financial_performance': sections_dict.get('financial_performance', ''),
                'competitive_position': sections_dict.get('competitive_position', ''),
                'risk_factors': sections_dict.get('risk_factors', ''),
                'growth_strategy': sections_dict.get('growth_strategy', ''),
                'governance_quality': sections_dict.get('governance_quality', ''),
                'recommendation': recommendation
            },
            'milestones': milestones,
            'success': True
        }

    except Exception as e:
        print(f"[ERROR] Story generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate story: {str(e)}")


def _extract_milestones(growth_strategy_text: str) -> List[Dict[str, str]]:
    """
    Extract key milestones/roadmap items from growth strategy text

    Args:
        growth_strategy_text: Growth strategy narrative

    Returns:
        List of milestone dicts with title and description
    """
    import re

    if not growth_strategy_text or len(growth_strategy_text) < 100:
        return [
            {
                'title': 'Strategic Milestones',
                'description': 'Detailed roadmap information not available in the annual report. Please refer to investor presentations or management guidance.'
            }
        ]

    # Clean markdown and special characters
    cleaned_text = growth_strategy_text

    # Remove markdown formatting
    cleaned_text = re.sub(r'\*\*\*+', '', cleaned_text)  # Remove *** or more
    cleaned_text = re.sub(r'\*\*', '', cleaned_text)      # Remove **
    cleaned_text = re.sub(r'\*', '', cleaned_text)        # Remove single *
    cleaned_text = re.sub(r'#{1,6}\s*', '', cleaned_text) # Remove ### headers
    cleaned_text = re.sub(r'_{2,}', '', cleaned_text)     # Remove __
    cleaned_text = re.sub(r'`{1,3}', '', cleaned_text)    # Remove ` or ```

    # Try to identify key initiatives/milestones from the text
    milestones = []

    # Common milestone indicators
    milestone_keywords = [
        'expansion', 'launch', 'new', 'plan', 'initiative', 'project',
        'investment', 'capex', 'r&d', 'innovation', 'partnership',
        'acquisition', 'market entry', 'capacity', 'facility', 'development',
        'focus', 'strategy', 'target', 'goal'
    ]

    # Split into sentences (handle both . and newlines)
    sentences = re.split(r'[.!?]\s+|\n+', cleaned_text)

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 25:  # Increased minimum length
            continue

        # Check if sentence contains milestone keywords
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in milestone_keywords):
            # Extract as milestone
            if len(milestones) < 6:  # Limit to 6 key milestones
                # Clean the sentence further
                clean_sentence = sentence.strip()
                clean_sentence = re.sub(r'\s+', ' ', clean_sentence)  # Normalize whitespace

                milestones.append({
                    'title': _extract_milestone_title(clean_sentence),
                    'description': clean_sentence
                })

    # If no milestones found, create a generic one from cleaned text
    if not milestones:
        clean_desc = cleaned_text[:300].strip()
        clean_desc = re.sub(r'\s+', ' ', clean_desc)  # Normalize whitespace
        milestones.append({
            'title': 'Growth Initiatives',
            'description': clean_desc + ('...' if len(cleaned_text) > 300 else '')
        })

    return milestones


def _extract_milestone_title(sentence: str) -> str:
    """Extract a short title from a milestone sentence, removing special characters"""
    import re

    # Remove any remaining special characters
    clean_sentence = re.sub(r'[#*_`]', '', sentence)
    clean_sentence = re.sub(r'\s+', ' ', clean_sentence).strip()

    # Take first few words as title
    words = clean_sentence.split()
    if len(words) <= 5:
        return clean_sentence

    # Try to find a meaningful phrase (up to 6 words)
    title_words = []
    for i, word in enumerate(words[:8]):
        title_words.append(word)
        # Stop at natural break points
        if word.endswith(',') or word.endswith(':') or i >= 5:
            break

    title = ' '.join(title_words).strip(',').strip(':').strip()
    # Clean the title one more time
    title = re.sub(r'[#*_`]', '', title)
    return title if len(title) > 10 else clean_sentence[:60] + ('...' if len(clean_sentence) > 60 else '')
