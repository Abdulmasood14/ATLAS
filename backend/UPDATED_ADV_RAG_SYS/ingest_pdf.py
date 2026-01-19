"""
PDF Ingestion Pipeline

Complete pipeline to ingest financial PDFs into the system:
PDF → Extract → Classify → Chunk → Embed → Store in PostgreSQL
"""
import pdfplumber
import psycopg2
from psycopg2.extras import execute_values
from typing import List, Dict, Tuple, Optional
import os
from datetime import datetime
import json

from annual_report_processor import Logger


from universal_classifier import UniversalClassifier
from adaptive_chunker import AdaptiveChunker, Chunk
from embedding_pipeline import BGE_M3_EmbeddingPipeline
from vision_ocr import VisionOCR
from section_context_detector import SectionContextDetector


class PDFIngestionPipeline:
    """
    Complete PDF ingestion pipeline

    Steps:
    1. Extract text from all pages using pdfplumber
    2. Chunk adaptively (preserves critical paragraphs)
    3. Classify chunks (multi-label)
    4. Generate embeddings (BGE-M3)
    5. Store in PostgreSQL
    """

    def __init__(
        self,
        db_config: Dict[str, str],
        max_chunk_size: int = 2048,
        overlap: int = 200,
        enable_ocr: bool = True  # Enable OCR fallback for scanned pages
    ):
        """
        Initialize ingestion pipeline

        Args:
            db_config: PostgreSQL connection config
            max_chunk_size: Maximum chunk size for non-critical content
            overlap: Overlap between chunks
            enable_ocr: Whether to enable Vision OCR for scanned pages
        """
        self.db_config = db_config
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.enable_ocr = enable_ocr

        # Initialize components
        self.classifier = UniversalClassifier()
        self.chunker = AdaptiveChunker(max_chunk_size, overlap)
        self.embedder = BGE_M3_EmbeddingPipeline()
        self.section_detector = SectionContextDetector()

        # Initialize Vision OCR if enabled
        if self.enable_ocr:
            self.vision_ocr = VisionOCR()
        else:
            self.vision_ocr = None

        # Database connection
        self.conn = None
        self.cursor = None

        # Store document-level data
        self.full_document_text = ""
        self.section_boundaries = []

    def _connect(self):
        """Connect to PostgreSQL"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()

    def close(self):
        """Close connections"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.embedder.close()
        if self.vision_ocr:
            self.vision_ocr.close()

    def ingest_pdf(
        self,
        pdf_path: str,
        company_id: str,
        company_name: Optional[str] = None,
        fiscal_year: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Ingest a PDF file into the system

        Args:
            pdf_path: Path to PDF file
            company_id: Company identifier (e.g., 'PHX_FXD')
            company_name: Company name (optional)
            fiscal_year: Fiscal year (optional, e.g., '2024-25')

        Returns:
            Dictionary with ingestion statistics
        """
        Logger.header(f"PDF INGESTION PIPELINE - {os.path.basename(pdf_path)}")

        stats = {
            'pdf_path': pdf_path,
            'company_id': company_id,
            'pages_processed': 0,
            'chunks_created': 0,
            'chunks_stored': 0,
            'critical_chunks': 0,
            'failed_chunks': 0,
            'start_time': datetime.now().isoformat()
        }

        # Connect to database
        self._connect()

        try:
            # Step 1: Extract pages from PDF
            Logger.info("Step 1: Extracting pages from PDF...")
            pages = self._extract_pages(pdf_path)
            stats['pages_processed'] = len(pages)
            Logger.success(f"Extracted {len(pages)} pages")

            # Step 1.5: Detect section boundaries in full document
            Logger.info("Step 1.5: Detecting section boundaries...")
            self.full_document_text = "\n\n".join(text for _, text in pages)
            self.section_boundaries = self.section_detector.detect_sections(self.full_document_text)
            consolidated_count = sum(1 for b in self.section_boundaries if b.statement_type == 'consolidated')
            standalone_count = sum(1 for b in self.section_boundaries if b.statement_type == 'standalone')
            Logger.info(f"Detected {len(self.section_boundaries)} section boundaries")
            Logger.info(f"Consolidated sections: {consolidated_count}", indent=1)
            Logger.info(f"Standalone sections: {standalone_count}", indent=1)

            # Step 2: Chunk adaptively
            Logger.info("Step 2: Chunking document adaptively...")
            chunks = self.chunker.chunk_document(pages)
            stats['chunks_created'] = len(chunks)
            stats['critical_chunks'] = sum(1 for c in chunks if c.is_critical)
            Logger.success(f"Created {len(chunks)} chunks")
            Logger.info(f"Critical chunks (preserved whole): {stats['critical_chunks']}", indent=1)

            # Step 3: Classify chunks with section context
            Logger.info("Step 3: Classifying chunks with section context...")
            classified_chunks = self._classify_chunks_with_context(chunks)
            Logger.success(f"Classified {len(classified_chunks)} chunks")

            # Step 4: Generate embeddings
            Logger.info("Step 4: Generating embeddings...")
            embedded_chunks = self._prepare_chunks_for_embedding(
                classified_chunks, company_id, company_name, fiscal_year,
                os.path.basename(pdf_path)
            )

            successful_chunks, failed_chunks = self.embedder.embed_chunks(embedded_chunks)
            stats['failed_chunks'] = len(failed_chunks)
            Logger.success(f"Successfully embedded {len(successful_chunks)} chunks")

            if failed_chunks:
                Logger.warning(f"{len(failed_chunks)} chunks failed embedding")

            # Step 5: Store in PostgreSQL
            Logger.info("Step 5: Storing chunks in PostgreSQL...")
            stored_count = self._store_chunks(successful_chunks)
            stats['chunks_stored'] = stored_count
            Logger.success(f"Stored {stored_count} chunks in database")

            # Commit transaction
            self.conn.commit()

            stats['end_time'] = datetime.now().isoformat()
            stats['status'] = 'success'

            print("\n" + "="*80)
            print("INGESTION COMPLETE")
            print("="*80)
            self._print_stats(stats)

            return stats

        except Exception as e:
            # Rollback on error
            if self.conn:
                self.conn.rollback()

            stats['status'] = 'failed'
            stats['error'] = str(e)
            stats['end_time'] = datetime.now().isoformat()

            print("\n" + "="*80)
            print("INGESTION FAILED")
            print("="*80)
            print(f"Error: {e}")

            raise

    def _extract_pages(self, pdf_path: str) -> List[Tuple[int, str]]:
        """
        Extract text from all pages in PDF with Vision OCR fallback for scanned pages

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of (page_number, page_text) tuples
        """
        pages = []
        scanned_pages_count = 0
        ocr_success_count = 0
        ocr_failed_count = 0

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

            for page_num, page in enumerate(pdf.pages, 1):
                # Try pdfplumber extraction first
                text = page.extract_text()

                # Check if Vision OCR fallback is needed
                if self.enable_ocr and self.vision_ocr:
                    extracted_text, method = self.vision_ocr.extract_page_with_fallback(
                        pdf_path=pdf_path,
                        page_num=page_num,
                        pdfplumber_text=text,
                        verbose=False
                    )

                    if method == 'vision_ocr':
                        scanned_pages_count += 1
                        if extracted_text:
                            ocr_success_count += 1
                            pages.append((page_num, extracted_text))
                            Logger.success(f"Page {page_num}: Scanned page - OCR successful ({len(extracted_text)} chars)", indent=1)
                        else:
                            ocr_failed_count += 1
                            Logger.warning(f"Page {page_num}: Scanned page - OCR failed (skipped)", indent=1)
                    elif method == 'vision_ocr_failed':
                        scanned_pages_count += 1
                        ocr_failed_count += 1
                        Logger.error(f"Page {page_num}: Scanned page - OCR failed (skipped)", indent=1)
                    else:
                        # pdfplumber extraction was successful
                        pages.append((page_num, extracted_text))

                else:
                    # OCR disabled - use only pdfplumber
                    if text and text.strip():
                        pages.append((page_num, text))

        # Print summary
        if scanned_pages_count > 0:
            Logger.info(f"Scanned pages detected: {scanned_pages_count}")
            Logger.success(f"OCR successful: {ocr_success_count}", indent=1)
            if ocr_failed_count > 0:
                Logger.warning(f"OCR failed: {ocr_failed_count}", indent=1)

        return pages

    def _classify_chunks_with_context(self, chunks: List[Chunk]) -> List[Dict]:
        """
        Classify all chunks using document-level section context

        Args:
            chunks: List of Chunk objects

        Returns:
            List of dicts with chunk data and classifications
        """
        classified = []

        # Build position map: chunk text -> estimated position in full document
        current_pos = 0
        chunk_positions = []

        for chunk in chunks:
            # Find chunk in full document text
            chunk_start = self.full_document_text.find(chunk.text[:100], current_pos)
            if chunk_start == -1:
                # Fallback: use approximate position
                chunk_start = current_pos
            chunk_end = chunk_start + len(chunk.text)
            chunk_positions.append((chunk_start, chunk_end))
            current_pos = chunk_end

        # Classify each chunk with section context
        for i, chunk in enumerate(chunks):
            chunk_start, chunk_end = chunk_positions[i]

            # Get section context for this chunk
            section_boundary = self.section_detector.get_section_for_chunk(
                self.full_document_text,
                chunk_start,
                chunk_end,
                self.section_boundaries
            )

            # Determine section context
            section_context = None
            if section_boundary:
                section_context = section_boundary.statement_type

            # Classify chunk with section context
            classification = self.classifier.classify(
                chunk.text,
                page_number=chunk.page_numbers[0] if chunk.page_numbers else None,
                section_context=section_context
            )

            classified.append({
                'text': chunk.text,
                'chunk_type': chunk.chunk_type,
                'page_numbers': chunk.page_numbers,
                'is_critical': chunk.is_critical,
                'section_types': classification.section_types,
                'note_number': classification.note_number,
                'statement_type': classification.statement_type,
                'confidence': classification.confidence,
                'section_boundary': section_boundary.section_name if section_boundary else None
            })

        return classified

    def _prepare_chunks_for_embedding(
        self,
        classified_chunks: List[Dict],
        company_id: str,
        company_name: Optional[str],
        fiscal_year: Optional[str],
        source_pdf: str
    ) -> List[Dict]:
        """
        Prepare chunks for embedding generation

        Args:
            classified_chunks: Classified chunks
            company_id: Company identifier
            company_name: Company name
            fiscal_year: Fiscal year
            source_pdf: Source PDF filename

        Returns:
            List of chunks ready for embedding
        """
        prepared = []

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        for i, chunk in enumerate(classified_chunks):
            chunk_id = f"chunk_{timestamp}_{i:06d}"

            prepared.append({
                'chunk_id': chunk_id,
                'company_id': company_id,
                'company_name': company_name,
                'fiscal_year': fiscal_year,
                'chunk_text': chunk['text'],
                'chunk_type': chunk['chunk_type'],
                'section_types': chunk['section_types'],
                'note_number': chunk['note_number'],
                'statement_type': chunk['statement_type'],
                'page_numbers': chunk['page_numbers'],
                'source_pdf': source_pdf,
                'metadata': json.dumps({
                    'is_critical': chunk['is_critical'],
                    'classification_confidence': chunk['confidence']
                })
            })

        return prepared

    def _store_chunks(self, chunks: List[Dict]) -> int:
        """
        Store chunks in PostgreSQL with progress feedback

        Args:
            chunks: Chunks with embeddings

        Returns:
            Number of chunks stored
        """
        if not chunks:
            return 0

        # Helper function to sanitize text (remove null bytes)
        def sanitize_text(text):
            if text is None:
                return None
            if isinstance(text, str):
                return text.replace('\x00', '')
            return text

        # Prepare data for batch insert
        values = []
        for chunk in chunks:
            values.append((
                chunk['chunk_id'],
                chunk['company_id'],
                sanitize_text(chunk.get('company_name')),
                chunk.get('fiscal_year'),
                sanitize_text(chunk['chunk_text']),  # Sanitize chunk text
                chunk['chunk_type'],
                chunk['section_types'],
                sanitize_text(chunk.get('note_number')),
                chunk.get('statement_type'),
                chunk['page_numbers'],
                sanitize_text(chunk.get('source_pdf')),
                sanitize_text(chunk.get('metadata')),  # Sanitize metadata JSON
                chunk['embedding']  # Already a list of floats
            ))

        # Batch insert with progress feedback
        insert_query = """
            INSERT INTO document_chunks_v2 (
                chunk_id, company_id, company_name, fiscal_year,
                chunk_text, chunk_type, section_types, note_number,
                statement_type, page_numbers, source_pdf, metadata, embedding
            ) VALUES %s
            ON CONFLICT (chunk_id) DO UPDATE SET
                chunk_text = EXCLUDED.chunk_text,
                embedding = EXCLUDED.embedding,
                updated_at = NOW()
        """

        # Process in smaller batches with progress indicators
        batch_size = 50
        total_chunks = len(values)
        stored_count = 0

        for i in range(0, total_chunks, batch_size):
            batch = values[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size

            print(f"  -> Batch {batch_num}/{total_batches}: Storing {len(batch)} chunks... (HNSW indexing may take 10-30s per batch)", end='', flush=True)

            execute_values(self.cursor, insert_query, batch, page_size=batch_size)
            stored_count += len(batch)

            print(f" ✓ Done ({stored_count}/{total_chunks})")

        return len(chunks)

    def _print_stats(self, stats: Dict):
        """Print ingestion statistics"""
        Logger.info(f"Company: {stats['company_id']}")
        Logger.info(f"PDF: {os.path.basename(stats['pdf_path'])}")
        Logger.info(f"Pages processed: {stats['pages_processed']}")
        Logger.info(f"Chunks created: {stats['chunks_created']}")
        Logger.info(f"Critical chunks: {stats['critical_chunks']}", indent=1)
        Logger.info(f"Regular chunks: {stats['chunks_created'] - stats['critical_chunks']}", indent=1)
        Logger.success(f"Chunks stored: {stats['chunks_stored']}")
        if stats['failed_chunks'] > 0:
            Logger.warning(f"Failed chunks: {stats['failed_chunks']}")
        Logger.info(f"Status: {stats['status']}")


# ============================================================================
# COMMAND-LINE INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Ingest a financial PDF into the RAG system')
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('company_id', help='Company identifier (e.g., PHX_FXD)')
    parser.add_argument('--company_name', help='Company name (optional)')
    parser.add_argument('--fiscal_year', help='Fiscal year (optional, e.g., 2024-25)')

    args = parser.parse_args()

    # Database config
    db_config = {
        'host': 'localhost',
        'database': 'financial_rag',
        'user': 'postgres',
        'password': 'Prasanna!@#2002'
    }

    # Initialize pipeline
    pipeline = PDFIngestionPipeline(db_config)

    try:
        # Ingest PDF
        stats = pipeline.ingest_pdf(
            args.pdf_path,
            args.company_id,
            args.company_name,
            args.fiscal_year
        )

        print("\n" + "="*80)
        print("SUCCESS - PDF ingested successfully!")
        print("="*80)

    except Exception as e:
        print(f"\nERROR: {e}")
        exit(1)

    finally:
        pipeline.close()
