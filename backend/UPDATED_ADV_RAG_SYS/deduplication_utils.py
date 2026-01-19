"""
Deduplication utilities for RAG retrieval results

Removes duplicate or highly similar chunks to improve answer quality.
"""
from typing import List
from retrieval_types import RetrievalResult
import difflib


def deduplicate_by_similarity(
    results: List[RetrievalResult],
    similarity_threshold: float = 0.75,
    max_chunks: int = 5
) -> List[RetrievalResult]:
    """
    Remove duplicate or highly similar chunks from retrieval results

    This prevents the LLM from seeing the same information multiple times
    from different pages (e.g., same note appearing in both standalone and consolidated statements)

    Args:
        results: List of retrieval results sorted by score
        similarity_threshold: Text similarity threshold (0-1) for considering chunks duplicates
                            0.75 means 75% similar text will be considered duplicate
        max_chunks: Maximum number of unique chunks to return

    Returns:
        Deduplicated list of retrieval results with highest scores
    """
    if not results:
        return []

    deduplicated = []
    seen_texts = []

    # Results should already be sorted by score (highest first)
    # If not, sort them
    sorted_results = sorted(results, key=lambda x: x.score, reverse=True)

    for result in sorted_results:
        # Check if this chunk is too similar to any already selected chunk
        is_duplicate = False

        for seen_text in seen_texts:
            # Calculate text similarity using SequenceMatcher
            similarity = difflib.SequenceMatcher(
                None,
                result.chunk_text.lower().strip(),
                seen_text.lower().strip()
            ).ratio()

            if similarity >= similarity_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            deduplicated.append(result)
            seen_texts.append(result.chunk_text)

            # Stop if we have enough unique chunks
            if len(deduplicated) >= max_chunks:
                break

    return deduplicated


def filter_by_page_diversity(
    results: List[RetrievalResult],
    max_per_page: int = 2
) -> List[RetrievalResult]:
    """
    Limit chunks from the same page to ensure diversity

    Prevents retrieving multiple chunks from the same page which often
    contain redundant information

    Args:
        results: List of retrieval results
        max_per_page: Maximum chunks to keep from any single page

    Returns:
        Filtered list with page diversity
    """
    if not results:
        return []

    page_counts = {}
    filtered = []

    for result in results:
        # Get primary page (first page in the list)
        primary_page = result.page_numbers[0] if result.page_numbers else None

        if primary_page is None:
            # Keep chunks without page numbers
            filtered.append(result)
            continue

        # Track count for this page
        if primary_page not in page_counts:
            page_counts[primary_page] = 0

        # Only keep if under the limit
        if page_counts[primary_page] < max_per_page:
            filtered.append(result)
            page_counts[primary_page] += 1

    return filtered


def smart_deduplicate(
    results: List[RetrievalResult],
    similarity_threshold: float = 0.75,
    max_chunks: int = 5,
    max_per_page: int = 2
) -> List[RetrievalResult]:
    """
    Smart deduplication combining similarity and page diversity

    This is the recommended deduplication method for financial RAG

    Args:
        results: List of retrieval results
        similarity_threshold: Similarity threshold for duplicate detection
        max_chunks: Maximum final chunks to return
        max_per_page: Maximum chunks from same page

    Returns:
        Deduplicated and diversified list
    """
    if not results:
        return []

    # Step 1: Remove highly similar chunks (keeps highest scored)
    unique_chunks = deduplicate_by_similarity(
        results,
        similarity_threshold=similarity_threshold,
        max_chunks=max_chunks * 2  # Get more candidates first
    )

    # Step 2: Ensure page diversity
    diverse_chunks = filter_by_page_diversity(
        unique_chunks,
        max_per_page=max_per_page
    )

    # Step 3: Limit to max_chunks
    return diverse_chunks[:max_chunks]
