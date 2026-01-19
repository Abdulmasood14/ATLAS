"""
BGE-M3 Embedding Pipeline

Generates 1024-dimensional embeddings for document chunks using BGE-M3 model.
Supports batch processing, progress tracking, and error handling.
"""
import requests
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class EmbeddingResult:
    """Result of embedding generation"""
    text: str
    embedding: List[float]
    success: bool
    error: Optional[str] = None


class BGE_M3_EmbeddingPipeline:
    """
    BGE-M3 embedding generation pipeline

    Features:
    - Batch processing for efficiency
    - Progress tracking
    - Error handling with retries
    - Connection pooling
    """

    def __init__(
        self,
        endpoint: str = "http://10.100.20.76:11434/v1/embeddings",
        model: str = "bge-m3",
        batch_size: int = 32,
        max_retries: int = 3,
        timeout: int = 30
    ):
        """
        Initialize embedding pipeline

        Args:
            endpoint: BGE-M3 API endpoint
            model: Model name
            batch_size: Number of texts to process per batch
            max_retries: Maximum retry attempts on failure
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.timeout = timeout

        # Session for connection pooling
        self.session = requests.Session()

    def embed_single(self, text: str) -> EmbeddingResult:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            EmbeddingResult with embedding or error
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    self.endpoint,
                    json={
                        "model": self.model,
                        "input": text
                    },
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    embedding = data['data'][0]['embedding']

                    return EmbeddingResult(
                        text=text,
                        embedding=embedding,
                        success=True
                    )
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"

                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        return EmbeddingResult(
                            text=text,
                            embedding=[],
                            success=False,
                            error=error_msg
                        )

            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return EmbeddingResult(
                        text=text,
                        embedding=[],
                        success=False,
                        error="Request timeout"
                    )

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return EmbeddingResult(
                        text=text,
                        embedding=[],
                        success=False,
                        error=str(e)
                    )

        return EmbeddingResult(
            text=text,
            embedding=[],
            success=False,
            error="Max retries exceeded"
        )

    def embed_batch(self, texts: List[str], show_progress: bool = True) -> List[EmbeddingResult]:
        """
        Generate embeddings for a batch of texts

        Args:
            texts: List of texts to embed
            show_progress: Whether to print progress

        Returns:
            List of EmbeddingResult objects
        """
        results = []
        total = len(texts)

        if show_progress:
            print(f"Generating embeddings for {total} texts...")

        for i, text in enumerate(texts, 1):
            result = self.embed_single(text)
            results.append(result)

            if show_progress and i % 10 == 0:
                success_count = sum(1 for r in results if r.success)
                print(f"  Progress: {i}/{total} ({success_count} successful)")

        if show_progress:
            success_count = sum(1 for r in results if r.success)
            failed_count = total - success_count
            print(f"Completed: {success_count} successful, {failed_count} failed")

        return results

    def embed_chunks(self, chunks: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Generate embeddings for chunks and return successful/failed chunks

        Args:
            chunks: List of chunk dictionaries with 'chunk_id' and 'chunk_text'

        Returns:
            Tuple of (successful_chunks, failed_chunks)
        """
        successful = []
        failed = []

        total = len(chunks)
        print(f"\n{'='*80}")
        print(f"EMBEDDING PIPELINE - Processing {total} chunks")
        print(f"{'='*80}\n")

        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(chunks) + self.batch_size - 1) // self.batch_size

            print(f"Batch {batch_num}/{total_batches} ({len(batch)} chunks)...")

            # Extract texts
            texts = [chunk['chunk_text'] for chunk in batch]

            # Generate embeddings
            results = self.embed_batch(texts, show_progress=False)

            # Add embeddings to chunks
            for chunk, result in zip(batch, results):
                if result.success:
                    chunk['embedding'] = result.embedding
                    successful.append(chunk)
                else:
                    chunk['error'] = result.error
                    failed.append(chunk)

            success_count = sum(1 for r in results if r.success)
            print(f"  -> {success_count}/{len(batch)} successful\n")

        print(f"{'='*80}")
        print(f"TOTAL: {len(successful)} successful, {len(failed)} failed")
        print(f"{'='*80}\n")

        return successful, failed

    def close(self):
        """Close the session"""
        self.session.close()


# ============================================================================
# TEST/DEMO
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("BGE-M3 EMBEDDING PIPELINE - TEST")
    print("="*80)

    # Initialize pipeline
    pipeline = BGE_M3_EmbeddingPipeline(
        endpoint="http://10.100.20.76:11434/v1/embeddings",
        batch_size=5
    )

    # Test chunks
    test_chunks = [
        {
            'chunk_id': 'chunk_001',
            'chunk_text': "The Group's investment properties consists of Retail Malls and Commercial Buildings. As at March 31, 2025, the fair values of the properties are INR 31,34,063.00 lakhs."
        },
        {
            'chunk_id': 'chunk_002',
            'chunk_text': "BALANCE SHEET AS AT MARCH 31, 2025. Investment Property: 3,142.77 crores"
        },
        {
            'chunk_id': 'chunk_003',
            'chunk_text': "NOTE 12 - INVESTMENT PROPERTY. The Group has investment properties comprising of commercial and retail properties."
        }
    ]

    print("\nTest: Embedding 3 chunks...\n")

    # Generate embeddings
    successful, failed = pipeline.embed_chunks(test_chunks)

    # Display results
    print("\n" + "-"*80)
    print("RESULTS")
    print("-"*80)

    for chunk in successful:
        embedding = chunk['embedding']
        print(f"\nChunk: {chunk['chunk_id']}")
        print(f"  Text: {chunk['chunk_text'][:80]}...")
        print(f"  Embedding dimensions: {len(embedding)}")
        print(f"  Embedding preview: [{embedding[0]:.4f}, {embedding[1]:.4f}, ..., {embedding[-1]:.4f}]")

    if failed:
        print("\n" + "-"*80)
        print("FAILED CHUNKS")
        print("-"*80)
        for chunk in failed:
            print(f"\nChunk: {chunk['chunk_id']}")
            print(f"  Error: {chunk['error']}")

    # Close pipeline
    pipeline.close()

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
