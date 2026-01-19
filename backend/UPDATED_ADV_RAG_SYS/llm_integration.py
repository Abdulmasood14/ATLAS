"""
LLM Integration Module

Dual LLM system for answer extraction:
1. GPT-OSS 20B: Text extraction from paragraphs and notes
2. Wen 2.5 VL: Table and image understanding
"""
import requests
import json
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from LLM"""
    answer: str
    success: bool
    model_used: str
    error: Optional[str] = None


class DualLLMSystem:
    """
    Dual LLM system for financial document analysis

    GPT-OSS 20B: Text-based queries
    - Fair Value paragraphs
    - Note disclosures
    - Accounting policies
    - Text-based metrics

    Wen 2.5 VL: Visual queries (future enhancement)
    - Financial tables
    - Charts and graphs
    - Complex financial statements
    """

    def __init__(
        self,
        text_llm_endpoint: str = "http://10.100.20.76:11434/v1/chat/completions",
        text_llm_model: str = "gpt-oss:20b",
        vision_llm_endpoint: Optional[str] = None,
        vision_llm_model: str = "qwen2.5vl:latest",
        timeout: int = 60
    ):
        """
        Initialize dual LLM system

        Args:
            text_llm_endpoint: GPT-OSS endpoint
            text_llm_model: GPT-OSS model name
            vision_llm_endpoint: Wen 2.5 VL endpoint (optional)
            vision_llm_model: Wen 2.5 VL model name
            timeout: Request timeout in seconds
        """
        self.text_llm_endpoint = text_llm_endpoint
        self.text_llm_model = text_llm_model
        self.vision_llm_endpoint = vision_llm_endpoint
        self.vision_llm_model = vision_llm_model
        self.timeout = timeout

        # Session for connection pooling
        self.session = requests.Session()

    def extract_answer(
        self,
        query: str,
        context_chunks: List[Dict],
        use_vision: bool = False,
        statement_type: Optional[str] = None,  # NEW: 'consolidated', 'standalone', or None
        query_type: str = 'mixed'  # NEW: 'objective', 'subjective', or 'mixed'
    ) -> LLMResponse:
        """
        Extract answer from context chunks using appropriate LLM

        Args:
            query: User query
            context_chunks: Retrieved chunks with text and metadata
            use_vision: Whether to use vision LLM (for tables/images)
            statement_type: Optional statement type for section-aware prompting
            query_type: Type of query ('objective', 'subjective', or 'mixed')

        Returns:
            LLMResponse with extracted answer
        """
        if use_vision and self.vision_llm_endpoint:
            return self._extract_with_vision_llm(query, context_chunks, statement_type, query_type)
        else:
            return self._extract_with_text_llm(query, context_chunks, statement_type, query_type)

    def _extract_with_text_llm(
        self,
        query: str,
        context_chunks: List[Dict],
        statement_type: Optional[str] = None,
        query_type: str = 'mixed'
    ) -> LLMResponse:
        """
        Extract answer using GPT-OSS (text LLM)

        Args:
            query: User query
            context_chunks: Retrieved chunks
            statement_type: Optional statement type for section-aware prompting
            query_type: Type of query ('objective', 'subjective', or 'mixed')

        Returns:
            LLMResponse with answer
        """
        # Build context from chunks with smart windowing
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            chunk_text = chunk.get('chunk_text', chunk.get('text', ''))
            page_nums = chunk.get('page_numbers', [])
            page_info = f"[Page(s) {page_nums}]" if page_nums else ""

            # Smart windowing disabled - using clean chunks from database instead
            # if len(chunk_text) > 2500:
            #     chunk_text = self._smart_window_chunk(chunk_text, query, window_size=2000)

            # Don't use "Context X" labels - just separate with clear boundaries
            context_parts.append(f"{page_info}\n{chunk_text}\n")

        context = "\n---\n".join(context_parts)

        # Build prompt with section awareness
        prompt = self._build_extraction_prompt(query, context, statement_type, query_type)

        # Call LLM
        try:
            response = self.session.post(
                self.text_llm_endpoint,
                json={
                    "model": self.text_llm_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a financial document analysis assistant. Extract accurate information from the provided context to answer user queries. Provide comprehensive answers based on the available context without adding disclaimers about missing information at the end."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,  # Low temperature for factual extraction
                    "max_tokens": 1000  # Increased to avoid cutoffs
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                message = data['choices'][0]['message']

                # Prefer 'content' field, fallback to 'reasoning'
                content = message.get('content', '').strip()
                reasoning = message.get('reasoning', '').strip()

                if content:
                    # Use content if available (direct answer)
                    answer = content
                elif reasoning:
                    # If only reasoning exists, try to extract the final answer
                    # Look for common answer patterns at the end
                    lines = reasoning.split('\n')
                    # Try last non-empty line, or last sentence
                    for line in reversed(lines):
                        line = line.strip()
                        if line and not line.startswith('We need') and not line.startswith('Search') and not line.startswith('Context'):
                            answer = line
                            break
                    else:
                        answer = reasoning  # Fallback to full reasoning
                else:
                    answer = ''

                return LLMResponse(
                    answer=answer,
                    success=True,
                    model_used=self.text_llm_model
                )
            else:
                return LLMResponse(
                    answer="",
                    success=False,
                    model_used=self.text_llm_model,
                    error=f"HTTP {response.status_code}: {response.text}"
                )

        except requests.exceptions.Timeout:
            return LLMResponse(
                answer="",
                success=False,
                model_used=self.text_llm_model,
                error="Request timeout"
            )

        except Exception as e:
            return LLMResponse(
                answer="",
                success=False,
                model_used=self.text_llm_model,
                error=str(e)
            )

    def _extract_with_vision_llm(
        self,
        query: str,
        context_chunks: List[Dict]
    ) -> LLMResponse:
        """
        Extract answer using Wen 2.5 VL (vision LLM)

        Note: This is a placeholder for future implementation
        Requires image data in context_chunks

        Args:
            query: User query
            context_chunks: Retrieved chunks (with images)

        Returns:
            LLMResponse with answer
        """
        # TODO: Implement vision LLM integration
        # For now, fall back to text LLM
        return self._extract_with_text_llm(query, context_chunks)

    def _smart_window_chunk(self, chunk_text: str, query: str, window_size: int = 1500) -> str:
        """
        Smart windowing for long chunks - find most relevant section

        Strategy:
        1. Look for key phrases (e.g., "fair value", "as at march")
        2. Look for numbers (INR, lakhs, crores)
        3. Prioritize sections with complete sentences
        4. Fallback: use last portion (summaries often at end)

        Args:
            chunk_text: Full chunk text
            query: User query
            window_size: Target window size in characters

        Returns:
            Most relevant section of the chunk
        """
        chunk_lower = chunk_text.lower()
        query_lower = query.lower()

        # Extract key phrases from query (2+ word combinations)
        query_words = [w for w in query_lower.split() if len(w) > 3]
        key_phrases = []

        # Build 2-word phrases
        for i in range(len(query_words) - 1):
            key_phrases.append(query_words[i] + ' ' + query_words[i+1])

        # Add single important words
        key_phrases.extend(query_words)

        # Search for key phrases and indicators of important content
        best_position = -1
        best_score = 0

        # Scan through chunk
        for i in range(0, len(chunk_text), 100):
            window = chunk_lower[i:i+window_size]
            score = 0

            # Score based on key phrases
            for phrase in key_phrases:
                if phrase in window:
                    score += 2  # Higher weight for phrases

            # Bonus for numeric content (financial data)
            if 'inr' in window or 'lakhs' in window or 'crores' in window:
                score += 1

            # Bonus for "as at" or similar date references (often near key data)
            if 'as at' in window or 'as of' in window:
                score += 1

            # Bonus for complete sentences (look for periods and proper capitalization)
            if '. ' in window:
                score += 0.5

            if score > best_score:
                best_score = score
                best_position = i

        # If no good section found OR score is low, use last 1500 chars
        # (summaries/conclusions often at end, especially in financial documents)
        if best_position == -1 or best_score < 5:
            # Try to start from a sentence boundary
            fallback = chunk_text[-window_size:]
            first_period = fallback.find('. ')
            if first_period != -1 and first_period < 300:
                fallback = fallback[first_period+2:]
            return fallback

        # Extract window around best position
        start = max(0, best_position)
        end = min(len(chunk_text), best_position + window_size)

        # Try to break at sentence boundaries
        window = chunk_text[start:end]

        # If we're not at the start, find first sentence start
        if start > 0:
            first_period = window.find('. ')
            if first_period != -1 and first_period < 200:
                window = window[first_period+2:]

        # If we're not at the end, find last sentence end
        if end < len(chunk_text):
            last_period = window.rfind('. ')
            if last_period != -1 and last_period > len(window) - 200:
                window = window[:last_period+1]

        return window

    def _build_extraction_prompt(
        self,
        query: str,
        context: str,
        statement_type: Optional[str] = None,
        query_type: str = 'mixed'
    ) -> str:
        """
        Build section-aware prompt for answer extraction

        Args:
            query: User query
            context: Context from retrieved chunks
            statement_type: Statement type ('consolidated', 'standalone', or None)
            query_type: Query type ('objective', 'subjective', or 'mixed')

        Returns:
            Formatted prompt with section awareness
        """
        # Build context header with section information
        context_header = "Context from financial statements"
        if statement_type:
            context_header += f" ({statement_type.upper()})"

        # Build query-type specific instructions
        if query_type == 'objective':
            specific_instructions = """
- Extract EXACT numbers with their units (Rs., lakhs, crores, million, billion)
- Include year-over-year comparisons when available (e.g., "2025: X vs 2024: Y")
- Cite specific note numbers (e.g., "Note 10", "Note 12.1")
- Format numbers clearly with proper separators (1,234.56)
- If asking about calculations (like depreciation rate), show the formula/breakdown
- Present data in structured format (tables, bullet points)"""
        elif query_type == 'subjective':
            specific_instructions = """
- Explain the methodology, policy, or approach mentioned in the context
- Include relevant assumptions and judgments
- Quote key phrases from the document when appropriate
- Explain any accounting standards or frameworks referenced
- Provide context for why certain methods/policies are used
- If multiple approaches are mentioned, explain all of them"""
        else:  # mixed
            specific_instructions = """
- Provide a comprehensive answer with both quantitative data and qualitative explanations
- Include all relevant numbers, facts, and detailed context
- Cite note numbers and page references
- DO NOT use markdown headings (###, ####, etc.)
- DO NOT create section headers like "Key Findings:", "Explanatory Context:", "Quantitative Data:", "Qualitative Explanations:", "Conclusion:"
- Write in flowing paragraphs without structural divisions
- Present all information in a natural narrative format"""

        # Build section-specific warning if statement_type is provided
        section_warning = ""
        if statement_type:
            section_warning = f"""
IMPORTANT SECTION CONTEXT:
- The context below is from {statement_type.upper()} financial statements
- Ensure your answer is specific to this section only
- Do NOT mix information from different sections (Consolidated vs Standalone)
- If the note number or data doesn't match the question's section, mention the discrepancy
"""

        prompt = f"""You are a financial document analyst. Answer the question using ONLY the provided context below.
{section_warning}
{context_header}:
{context}

Question: {query}

Instructions:
- Read and synthesize information from ALL the context sections above
{specific_instructions}
- DO NOT reference "Context 1", "Context 2", "[Page(s) X]" etc. in your answer
- Provide a direct, clear answer that synthesizes all relevant information
- Write a complete answer based on the available information without adding disclaimers about what's missing
- DO NOT end with statements like "Information not found in the provided context" - only include what you can answer
- Focus on providing useful insights from the available data

Answer:"""

        return prompt

    def close(self):
        """Close the session"""
        self.session.close()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_chunks_for_llm(retrieval_results) -> List[Dict]:
    """
    Convert RetrievalResult objects to dict format for LLM

    Args:
        retrieval_results: List of RetrievalResult objects

    Returns:
        List of dicts with chunk data
    """
    chunks = []
    for result in retrieval_results:
        chunks.append({
            'chunk_text': result.chunk_text,
            'page_numbers': result.page_numbers,
            'chunk_type': result.chunk_type,
            'section_types': result.section_types,
            'note_number': result.note_number
        })
    return chunks


# ============================================================================
# TEST/DEMO
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("LLM INTEGRATION - TEST")
    print("="*80)

    # Initialize LLM system
    llm = DualLLMSystem(
        text_llm_endpoint="http://10.100.20.76:11434/v1/chat/completions",
        text_llm_model="gpt-oss:20b"
    )

    print("\nInitialized dual LLM system")
    print(f"  Text LLM: {llm.text_llm_model}")
    print(f"  Endpoint: {llm.text_llm_endpoint}")

    # Test context
    test_query = "What is the Fair Value of Investment Properties?"

    test_chunks = [
        {
            'chunk_text': "The Group's investment properties consists of Retail Malls and Commercial Buildings which has been determined based on the nature, characteristics and risks of each property. As at March 31, 2025 and March 31, 2024, the fair values of the properties are INR 31,34,063.00 lakhs and INR 28,96,370.00 lakhs respectively.",
            'page_numbers': [196],
            'chunk_type': 'paragraph',
            'section_types': ['fair_value', 'investment_property']
        }
    ]

    print("\n" + "-"*80)
    print("Test Query:", test_query)
    print("-"*80)

    print("\nCalling GPT-OSS to extract answer...")

    # Extract answer
    response = llm.extract_answer(test_query, test_chunks)

    if response.success:
        print("\n" + "="*80)
        print("ANSWER EXTRACTED")
        print("="*80)
        print(f"\nModel: {response.model_used}")
        print(f"\nAnswer:\n{response.answer}")
        print("\n" + "="*80)
    else:
        print("\n" + "="*80)
        print("EXTRACTION FAILED")
        print("="*80)
        print(f"Error: {response.error}")
        print("\nNote: This is expected if GPT-OSS server is not running.")
        print("="*80)

    # Close LLM system
    llm.close()

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
