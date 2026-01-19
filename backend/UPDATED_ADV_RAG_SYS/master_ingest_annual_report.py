"""
Master Annual Report Ingestion Pipeline
========================================

Complete end-to-end pipeline for ingesting annual reports with rotation correction:

WORKFLOW:
1. Orientation Detection & Correction (annual_report_processor.py)
   - Detects rotated pages (90°, 180°, 270°)
   - Corrects rotations (full page or split halves for landscape)
   - Smart extraction (pymupdf4llm + Dockling for tables)

2. Note-Aware Adaptive Chunking (adaptive_chunker.py)
   - Detects hierarchical note structure (NOTE 1, NOTE 2, 12.1, 12.2, etc.)
   - Preserves note boundaries (never splits NOTE X → NOTE Y)
   - Handles subjective (text) and objective (tables/numbers) content

3. Classification & Embedding (ingest_pdf.py)
   - Multi-label classification (section types, note numbers)
   - BGE-M3 embeddings (1024 dimensions)
   - Vision OCR fallback for scanned pages

4. PostgreSQL Storage with HNSW Indexing
   - Vector similarity search ready
   - Full-text search with GIN index
   - Note metadata stored for hierarchical queries

Author: Financial RAG System V2
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

# Import core modules
from annual_report_processor import AnnualReportProcessor, OrientationCorrector, Logger
from ingest_pdf import PDFIngestionPipeline


class MasterAnnualReportPipeline:
    """
    Master pipeline for complete annual report ingestion

    Combines:
    - Orientation correction (annual_report_processor)
    - Note-aware chunking (adaptive_chunker)
    - Embedding & storage (ingest_pdf)
    """

    def __init__(
        self,
        db_config: Optional[Dict[str, str]] = None,
        output_dir: str = "corrected_pdfs",
        enable_note_aware: bool = True,
        max_chunk_size: int = 2048,
        overlap: int = 200
    ):
        """
        Initialize master pipeline

        Args:
            db_config: PostgreSQL connection config (uses defaults if None)
            output_dir: Directory for corrected PDFs
            enable_note_aware: Enable note-aware chunking (default: True)
            max_chunk_size: Maximum chunk size for non-critical content
            overlap: Overlap between chunks
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
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.enable_note_aware = enable_note_aware
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

        # Initialize orientation corrector
        self.corrector = OrientationCorrector()

        # Initialize ingestion pipeline
        self.ingestion_pipeline = PDFIngestionPipeline(
            db_config=db_config,
            max_chunk_size=max_chunk_size,
            overlap=overlap,
            enable_ocr=True  # Enable Vision OCR for scanned pages
        )

        # Enable note-aware chunking
        self.ingestion_pipeline.chunker.enable_note_aware = enable_note_aware

    def ingest_annual_report(
        self,
        pdf_path: str,
        company_id: str,
        company_name: Optional[str] = None,
        fiscal_year: Optional[str] = None,
        skip_correction: bool = False
    ) -> Dict[str, any]:
        """
        Complete annual report ingestion with all processing stages

        Args:
            pdf_path: Path to annual report PDF
            company_id: Company identifier (e.g., 'PHX_FXD')
            company_name: Company name (optional)
            fiscal_year: Fiscal year (optional, e.g., '2024-25')
            skip_correction: Skip orientation correction (for already corrected PDFs)

        Returns:
            Dictionary with comprehensive statistics from all stages
        """
        Logger.header("MASTER ANNUAL REPORT INGESTION PIPELINE")
        Logger.info(f"PDF: {os.path.basename(pdf_path)}")
        Logger.info(f"Company: {company_id} ({company_name or 'N/A'})")
        Logger.info(f"Fiscal Year: {fiscal_year or 'N/A'}")
        Logger.info(f"Note-Aware Chunking: {'ENABLED' if self.enable_note_aware else 'DISABLED'}")
        print()

        stats = {
            'pdf_path': pdf_path,
            'company_id': company_id,
            'company_name': company_name,
            'fiscal_year': fiscal_year,
            'start_time': datetime.now().isoformat(),
            'stages': {}
        }

        try:
            # STAGE 1: Orientation Detection & Correction
            if not skip_correction:
                Logger.header("STAGE 1: ORIENTATION DETECTION & CORRECTION")

                corrected_pdf_path = self.output_dir / f"corrected_{Path(pdf_path).name}"

                corrected_pdf, detection_results, page_mapping = self.corrector.process_pdf(
                    str(pdf_path),
                    str(corrected_pdf_path)
                )

                # Store stage 1 stats
                rotated_pages = sum(1 for r in detection_results if r['detected_orientation'] != 0)
                stats['stages']['orientation_correction'] = {
                    'total_pages': len(detection_results),
                    'rotated_pages': rotated_pages,
                    'corrected_pdf': corrected_pdf,
                    'page_mapping': page_mapping
                }

                Logger.success(f"Stage 1 Complete: {rotated_pages} rotated pages corrected")
                print()
            else:
                Logger.info("Skipping orientation correction (using original PDF)")
                corrected_pdf = pdf_path
                stats['stages']['orientation_correction'] = {
                    'skipped': True,
                    'corrected_pdf': pdf_path
                }

            # STAGE 2: Note-Aware Chunking + Embedding + Storage
            Logger.header("STAGE 2: INGESTION INTO RAG SYSTEM")
            Logger.info("Components:")
            Logger.info("  - Page extraction (pdfplumber + Vision OCR)", indent=1)
            Logger.info(f"  - Adaptive chunking (Note-aware: {self.enable_note_aware})", indent=1)
            Logger.info("  - Multi-label classification", indent=1)
            Logger.info("  - BGE-M3 embeddings (1024-dim)", indent=1)
            Logger.info("  - PostgreSQL storage (HNSW + GIN indexes)", indent=1)
            print()

            ingestion_stats = self.ingestion_pipeline.ingest_pdf(
                pdf_path=corrected_pdf,
                company_id=company_id,
                company_name=company_name,
                fiscal_year=fiscal_year
            )

            stats['stages']['rag_ingestion'] = ingestion_stats

            # STAGE 3: Summary
            Logger.header("INGESTION COMPLETE - SUMMARY")

            Logger.info(f"Company: {company_id}")
            if company_name:
                Logger.info(f"Name: {company_name}")
            if fiscal_year:
                Logger.info(f"Fiscal Year: {fiscal_year}")
            Logger.info(f"Source PDF: {os.path.basename(pdf_path)}")

            if not skip_correction:
                Logger.info("Stage 1 - Orientation Correction:")
                Logger.info(f"Total pages: {stats['stages']['orientation_correction']['total_pages']}", indent=1)
                Logger.info(f"Rotated pages corrected: {stats['stages']['orientation_correction']['rotated_pages']}", indent=1)
                Logger.info(f"Output: {os.path.basename(corrected_pdf)}", indent=1)

            Logger.info("Stage 2 - RAG Ingestion:")
            Logger.info(f"Pages processed: {ingestion_stats['pages_processed']}", indent=1)
            Logger.info(f"Chunks created: {ingestion_stats['chunks_created']}", indent=1)
            Logger.info(f"Critical chunks: {ingestion_stats['critical_chunks']}", indent=2)
            Logger.info(f"Regular chunks: {ingestion_stats['chunks_created'] - ingestion_stats['critical_chunks']}", indent=2)
            Logger.success(f"Chunks stored: {ingestion_stats['chunks_stored']}", indent=1)
            if ingestion_stats['failed_chunks'] > 0:
                Logger.warning(f"Failed chunks: {ingestion_stats['failed_chunks']}", indent=1)

            stats['end_time'] = datetime.now().isoformat()
            stats['status'] = 'success'

            Logger.success(f"Status: SUCCESS (Database: {self.db_config['database']})")
            Logger.success("INGESTION COMPLETE - Annual report is now searchable in the RAG system!")

            return stats

        except Exception as e:
            stats['end_time'] = datetime.now().isoformat()
            stats['status'] = 'failed'
            stats['error'] = str(e)

            Logger.error(f"Pipeline failed: {e}")
            raise

        finally:
            # Close connections
            self.ingestion_pipeline.close()

    def close(self):
        """Close all connections"""
        self.ingestion_pipeline.close()


# ============================================================================
# COMMAND-LINE INTERFACE
# ============================================================================

def main():
    """Main entry point for command-line usage"""

    if len(sys.argv) < 3:
        print("="*80)
        print("MASTER ANNUAL REPORT INGESTION PIPELINE")
        print("="*80)
        print("\nUsage:")
        print("  python master_ingest_annual_report.py <pdf_path> <company_id> [options]")
        print("\nRequired Arguments:")
        print("  pdf_path      Path to annual report PDF")
        print("  company_id    Company identifier (e.g., PHX_FXD)")
        print("\nOptional Arguments:")
        print("  --company_name <name>       Company full name")
        print("  --fiscal_year <year>        Fiscal year (e.g., 2024-25)")
        print("  --skip_correction           Skip orientation correction")
        print("  --disable_note_aware        Disable note-aware chunking")
        print("  --max_chunk_size <size>     Maximum chunk size (default: 2048)")
        print("  --overlap <size>            Chunk overlap (default: 200)")
        print("\nExamples:")
        print('  python master_ingest_annual_report.py "annual_report.pdf" PHX_FXD')
        print('  python master_ingest_annual_report.py "report.pdf" PHX_FXD --company_name "Phoenix Mills" --fiscal_year "2024-25"')
        print('  python master_ingest_annual_report.py "corrected.pdf" PHX_FXD --skip_correction')
        print("\n" + "="*80)
        sys.exit(1)

    # Parse arguments
    pdf_path = sys.argv[1]
    company_id = sys.argv[2]

    # Optional arguments
    company_name = None
    fiscal_year = None
    skip_correction = False
    enable_note_aware = True
    max_chunk_size = 2048
    overlap = 200

    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == '--company_name' and i + 1 < len(sys.argv):
            company_name = sys.argv[i + 1]
            i += 2
        elif arg == '--fiscal_year' and i + 1 < len(sys.argv):
            fiscal_year = sys.argv[i + 1]
            i += 2
        elif arg == '--skip_correction':
            skip_correction = True
            i += 1
        elif arg == '--disable_note_aware':
            enable_note_aware = False
            i += 1
        elif arg == '--max_chunk_size' and i + 1 < len(sys.argv):
            max_chunk_size = int(sys.argv[i + 1])
            i += 2
        elif arg == '--overlap' and i + 1 < len(sys.argv):
            overlap = int(sys.argv[i + 1])
            i += 2
        else:
            print(f"Unknown argument: {arg}")
            sys.exit(1)

    # Validate PDF exists
    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    # Initialize pipeline
    pipeline = MasterAnnualReportPipeline(
        enable_note_aware=enable_note_aware,
        max_chunk_size=max_chunk_size,
        overlap=overlap
    )

    try:
        # Run ingestion
        stats = pipeline.ingest_annual_report(
            pdf_path=pdf_path,
            company_id=company_id,
            company_name=company_name,
            fiscal_year=fiscal_year,
            skip_correction=skip_correction
        )

        print("\nNext Steps:")
        print("  1. Query the RAG system:")
        print(f'     python interactive_rag.py')
        print(f'     > Company: {company_id}')
        print(f'     > Query: What is the Fair Value of Investment Properties?')
        print()

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
