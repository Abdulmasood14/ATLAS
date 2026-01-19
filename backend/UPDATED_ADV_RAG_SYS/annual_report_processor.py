"""
Annual Report Batch Processor
=============================
Standalone script that processes multiple annual reports with rotation correction and extraction.

Features:
- Detects and corrects rotated pages/tables
- Smart extraction routing (Docku.py for corrected pages, pdf_entire.py for normal pages)
- Detailed terminal logging
- Two modes: Full extraction or correction only

Author: Auto-generated integration script
"""

import os
import sys
import time
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
from collections import Counter

# Third-party imports
import fitz  # PyMuPDF
import cv2
import numpy as np
import pandas as pd
from docling.document_converter import DocumentConverter

# Import ingestion broadcaster - use absolute import or relative with fallback
try:
    from services.ingestion_manager import broadcaster, current_upload_id
except ImportError:
    try:
        # Try relative import if in UPDATED_ADV_RAG_SYS
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from chatbot_ui.backend.services.ingestion_manager import broadcaster, current_upload_id
    except ImportError:
        broadcaster = None
        current_upload_id = None

# ============================================================================
# LOGGING UTILITIES
# ============================================================================

class Logger:
    """Detailed terminal logging with color support and timestamps."""

    # ANSI color codes
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def header(msg):
        print(f"\n{Logger.HEADER}{Logger.BOLD}{'='*80}{Logger.ENDC}")
        print(f"{Logger.HEADER}{Logger.BOLD}{msg.center(80)}{Logger.ENDC}")
        print(f"{Logger.HEADER}{Logger.BOLD}{'='*80}{Logger.ENDC}\n")
        if broadcaster and current_upload_id:
            uid = current_upload_id.get()
            if uid:
                broadcaster.broadcast(uid, f"--- {msg} ---", "info")

    @staticmethod
    def section(msg):
        print(f"\n{Logger.OKBLUE}{Logger.BOLD}[{datetime.now().strftime('%H:%M:%S')}] {msg}{Logger.ENDC}")
        print(f"{Logger.OKBLUE}{'-'*80}{Logger.ENDC}")

    @staticmethod
    def info(msg, indent=0):
        prefix = "  " * indent
        print(f"{prefix}{Logger.OKCYAN}[i] {msg}{Logger.ENDC}")
        if broadcaster and current_upload_id:
            uid = current_upload_id.get()
            if uid:
                broadcaster.broadcast(uid, msg, "info")

    @staticmethod
    def success(msg, indent=0):
        prefix = "  " * indent
        print(f"{prefix}{Logger.OKGREEN}[OK] {msg}{Logger.ENDC}")
        if broadcaster and current_upload_id:
            uid = current_upload_id.get()
            if uid:
                broadcaster.broadcast(uid, msg, "success")

    @staticmethod
    def warning(msg, indent=0):
        prefix = "  " * indent
        print(f"{prefix}{Logger.WARNING}[!] {msg}{Logger.ENDC}")
        if broadcaster and current_upload_id:
            uid = current_upload_id.get()
            if uid:
                broadcaster.broadcast(uid, msg, "warning")

    @staticmethod
    def error(msg, indent=0):
        prefix = "  " * indent
        print(f"{prefix}{Logger.FAIL}[X] {msg}{Logger.ENDC}")
        if broadcaster and current_upload_id:
            uid = current_upload_id.get()
            if uid:
                broadcaster.broadcast(uid, msg, "error")

    @staticmethod
    def progress(msg, indent=0):
        prefix = "  " * indent
        print(f"{prefix}{Logger.BOLD}-> {msg}{Logger.ENDC}")


# ============================================================================
# ORIENTATION DETECTION & CORRECTION MODULE
# ============================================================================

class OrientationCorrector:
    """Detects and corrects rotated content in PDFs."""

    def __init__(self, min_rotated_threshold=0.15, min_rotated_lines=20):
        self.min_rotated_threshold = min_rotated_threshold
        self.min_rotated_lines = min_rotated_lines

    def pdf_page_to_image(self, page: fitz.Page, dpi: int = 150) -> np.ndarray:
        """Convert PDF page to OpenCV image."""
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

        if pix.n == 4:  # RGBA
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:  # RGB
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        return img

    def detect_lines(self, image: np.ndarray) -> Tuple[List, List]:
        """Detect horizontal and vertical lines using Hough Transform."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=100,
            minLineLength=50,
            maxLineGap=10
        )

        horizontal_angles = []
        vertical_angles = []

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]

                if x2 - x1 == 0:
                    angle = 90
                else:
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))

                angle = angle % 180

                if abs(angle) < 15 or abs(angle - 180) < 15:
                    horizontal_angles.append(angle)
                elif abs(angle - 90) < 15:
                    vertical_angles.append(angle)

        return horizontal_angles, vertical_angles

    def detect_table_presence(self, image: np.ndarray) -> bool:
        """Detect if there's a table in the image."""
        horizontal_angles, vertical_angles = self.detect_lines(image)
        has_horizontal = len(horizontal_angles) > 3
        has_vertical = len(vertical_angles) > 3
        return has_horizontal and has_vertical

    def analyze_text_orientation(self, page: fitz.Page) -> Tuple[int, Dict]:
        """Analyze text block orientations on a page."""
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        rotations = []

        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    dir_x = line.get("dir", (1, 0))[0]
                    dir_y = line.get("dir", (1, 0))[1]
                    angle = np.degrees(np.arctan2(dir_y, dir_x))

                    if -45 <= angle < 45:
                        rotations.append(0)
                    elif 45 <= angle < 135:
                        rotations.append(90)
                    elif angle >= 135 or angle < -135:
                        rotations.append(180)
                    else:
                        rotations.append(270)

        if not rotations:
            return 0, {"total_lines": 0, "rotation_counts": {}, "has_mixed_content": False}

        counter = Counter(rotations)
        total_lines = len(rotations)

        stats = {
            "total_lines": total_lines,
            "rotation_counts": dict(counter),
            "has_mixed_content": len(counter) > 1
        }

        for rot_angle in [90, 180, 270]:
            count = counter.get(rot_angle, 0)
            percentage = count / total_lines
            if percentage >= self.min_rotated_threshold and count >= self.min_rotated_lines:
                stats["rotated_percentage"] = percentage
                return rot_angle, stats

        return 0, stats

    def get_page_orientation(self, page: fitz.Page) -> str:
        """Determine if page is portrait or landscape."""
        rect = page.rect
        return "portrait" if rect.height > rect.width else "landscape"

    def analyze_half_page_orientation(self, page: fitz.Page, half: str) -> Tuple[int, Dict]:
        """Analyze text orientation for left or right half of landscape page."""
        rect = page.rect
        page_width = rect.width
        midpoint = page_width / 2

        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        rotations = []

        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:
                block_bbox = block.get("bbox", (0, 0, 0, 0))
                block_center_x = (block_bbox[0] + block_bbox[2]) / 2

                if half == "left" and block_center_x >= midpoint:
                    continue
                if half == "right" and block_center_x < midpoint:
                    continue

                for line in block.get("lines", []):
                    line_bbox = line.get("bbox", (0, 0, 0, 0))
                    line_center_x = (line_bbox[0] + line_bbox[2]) / 2

                    if half == "left" and line_center_x >= midpoint:
                        continue
                    if half == "right" and line_center_x < midpoint:
                        continue

                    dir_x = line.get("dir", (1, 0))[0]
                    dir_y = line.get("dir", (1, 0))[1]
                    angle = np.degrees(np.arctan2(dir_y, dir_x))

                    if -45 <= angle < 45:
                        rotations.append(0)
                    elif 45 <= angle < 135:
                        rotations.append(90)
                    elif angle >= 135 or angle < -135:
                        rotations.append(180)
                    else:
                        rotations.append(270)

        if not rotations:
            return 0, {"total_lines": 0, "rotation_counts": {}, "has_mixed_content": False}

        counter = Counter(rotations)
        total_lines = len(rotations)

        stats = {
            "total_lines": total_lines,
            "rotation_counts": dict(counter),
            "has_mixed_content": len(counter) > 1
        }

        for rot_angle in [90, 180, 270]:
            count = counter.get(rot_angle, 0)
            percentage = count / total_lines if total_lines > 0 else 0
            if percentage >= self.min_rotated_threshold and count >= self.min_rotated_lines:
                stats["rotated_percentage"] = percentage
                return rot_angle, stats

        return 0, stats

    def detect_page_orientation(self, page: fitz.Page, page_num: int) -> Dict:
        """Detect orientation for a single page."""
        page_orientation = self.get_page_orientation(page)

        result = {
            "page_number": page_num,
            "page_rotation": page.rotation,
            "page_orientation": page_orientation,
            "text_orientation": 0,
            "has_table": False,
            "detected_orientation": 0,
            "has_mixed_content": False,
            "rotation_stats": {},
            "left_half_rotation": None,
            "right_half_rotation": None,
            "rotated_half": None
        }

        image = self.pdf_page_to_image(page)
        result["has_table"] = self.detect_table_presence(image)

        text_orientation, stats = self.analyze_text_orientation(page)
        result["text_orientation"] = text_orientation
        result["has_mixed_content"] = stats.get("has_mixed_content", False)
        result["rotation_stats"] = stats.get("rotation_counts", {})
        result["detected_orientation"] = text_orientation

        if page_orientation == "landscape" and result["detected_orientation"] != 0:
            left_rotation, left_stats = self.analyze_half_page_orientation(page, "left")
            result["left_half_rotation"] = left_rotation
            result["left_half_stats"] = left_stats

            right_rotation, right_stats = self.analyze_half_page_orientation(page, "right")
            result["right_half_rotation"] = right_rotation
            result["right_half_stats"] = right_stats

            left_rotated = left_rotation != 0
            right_rotated = right_rotation != 0

            if left_rotated and right_rotated:
                result["rotated_half"] = "both"
            elif left_rotated:
                result["rotated_half"] = "left"
            elif right_rotated:
                result["rotated_half"] = "right"
            else:
                result["rotated_half"] = "none"

        return result

    def get_counter_rotation(self, detected_rotation: int) -> int:
        """Calculate counter-rotation to normalize."""
        if detected_rotation == 90:
            return 90
        elif detected_rotation == 180:
            return 180
        elif detected_rotation == 270:
            return -90
        else:
            return 0

    def correct_portrait_page(self, src_doc: fitz.Document, page_idx: int,
                             detected_rotation: int, out_doc: fitz.Document) -> None:
        """Correct portrait page with native rotation."""
        counter_rotation = self.get_counter_rotation(detected_rotation)
        out_doc.insert_pdf(src_doc, from_page=page_idx, to_page=page_idx)
        new_page = out_doc[-1]
        current_rotation = new_page.rotation
        new_rotation = (current_rotation + counter_rotation) % 360
        new_page.set_rotation(new_rotation)

    def correct_landscape_page(self, src_doc: fitz.Document, page_idx: int,
                               left_rotation: int, right_rotation: int,
                               out_doc: fitz.Document) -> None:
        """Correct landscape page by splitting halves."""
        src_page = src_doc[page_idx]
        src_rect = src_page.rect
        width = src_rect.width
        height = src_rect.height
        midpoint = width / 2

        left_clip = fitz.Rect(0, 0, midpoint, height)
        right_clip = fitz.Rect(midpoint, 0, width, height)

        left_counter = self.get_counter_rotation(left_rotation) if left_rotation != 0 else 0
        right_counter = self.get_counter_rotation(right_rotation) if right_rotation != 0 else 0

        # Left half
        if left_counter in [90, -90]:
            left_page_width = height
            left_page_height = midpoint
        else:
            left_page_width = midpoint
            left_page_height = height

        left_page = out_doc.new_page(width=left_page_width, height=left_page_height)
        left_dest_rect = fitz.Rect(0, 0, left_page_width, left_page_height)
        left_page.show_pdf_page(left_dest_rect, src_doc, page_idx, clip=left_clip, rotate=left_counter)

        # Right half
        if right_counter in [90, -90]:
            right_page_width = height
            right_page_height = midpoint
        else:
            right_page_width = midpoint
            right_page_height = height

        right_page = out_doc.new_page(width=right_page_width, height=right_page_height)
        right_dest_rect = fitz.Rect(0, 0, right_page_width, right_page_height)
        right_page.show_pdf_page(right_dest_rect, src_doc, page_idx, clip=right_clip, rotate=right_counter)

    def process_pdf(self, pdf_path: str, output_path: str) -> Tuple[str, List[Dict], Dict]:
        """
        Process PDF with rotation detection and correction.

        Returns:
            - output_path: Path to corrected PDF
            - all_results: Detection results for original pages
            - page_mapping: Mapping of corrected page numbers to processing methods
        """
        Logger.section(f"Processing: {Path(pdf_path).name}")

        src_doc = fitz.open(pdf_path)
        total_pages = len(src_doc)
        Logger.info(f"Total pages in PDF: {total_pages}", indent=1)

        # Phase 1: Detection
        Logger.info("Phase 1: Detecting rotated content...", indent=1)
        all_results = []
        rotated_count = 0

        for page_idx in range(total_pages):
            page = src_doc[page_idx]
            result = self.detect_page_orientation(page, page_idx + 1)
            all_results.append(result)

            if result["detected_orientation"] != 0:
                rotated_count += 1
                Logger.warning(
                    f"Page {page_idx + 1}: {result['page_orientation'].upper()} - "
                    f"ROTATED {result['detected_orientation']}° "
                    f"(lines: {result['rotation_stats']})",
                    indent=2
                )
            else:
                Logger.info(f"Page {page_idx + 1}: Normal orientation", indent=2)

        Logger.success(f"Detection complete: {rotated_count} rotated pages found", indent=1)

        # Phase 2: Correction
        if rotated_count > 0:
            Logger.info("Phase 2: Applying corrections...", indent=1)
            out_doc = fitz.open()
            page_mapping = {}
            corrected_page_num = 1

            for idx, result in enumerate(all_results):
                page_orientation = result["page_orientation"]
                detected_orientation = result["detected_orientation"]

                if page_orientation == "portrait" and detected_orientation != 0:
                    # Portrait correction
                    self.correct_portrait_page(src_doc, idx, detected_orientation, out_doc)
                    page_mapping[corrected_page_num] = {"method": "both", "original_page": idx + 1}
                    Logger.success(f"Corrected page {idx + 1} → Output page {corrected_page_num}", indent=2)
                    corrected_page_num += 1

                elif page_orientation == "landscape" and result["rotated_half"] not in [None, "none"]:
                    # Landscape split
                    left_rot = result.get("left_half_rotation", 0) or 0
                    right_rot = result.get("right_half_rotation", 0) or 0

                    self.correct_landscape_page(src_doc, idx, left_rot, right_rot, out_doc)

                    # Left half
                    if left_rot != 0:
                        page_mapping[corrected_page_num] = {"method": "both", "original_page": idx + 1, "half": "left"}
                        Logger.success(f"Corrected page {idx + 1} (LEFT half) → Output page {corrected_page_num}", indent=2)
                    else:
                        page_mapping[corrected_page_num] = {"method": "pdf_entire_only", "original_page": idx + 1, "half": "left"}
                        Logger.info(f"Page {idx + 1} (LEFT half) → Output page {corrected_page_num} (no correction)", indent=2)
                    corrected_page_num += 1

                    # Right half
                    if right_rot != 0:
                        page_mapping[corrected_page_num] = {"method": "both", "original_page": idx + 1, "half": "right"}
                        Logger.success(f"Corrected page {idx + 1} (RIGHT half) → Output page {corrected_page_num}", indent=2)
                    else:
                        page_mapping[corrected_page_num] = {"method": "pdf_entire_only", "original_page": idx + 1, "half": "right"}
                        Logger.info(f"Page {idx + 1} (RIGHT half) → Output page {corrected_page_num} (no correction)", indent=2)
                    corrected_page_num += 1

                else:
                    # Normal page
                    out_doc.insert_pdf(src_doc, from_page=idx, to_page=idx)
                    page_mapping[corrected_page_num] = {"method": "pdf_entire_only", "original_page": idx + 1}
                    Logger.info(f"Page {idx + 1} → Output page {corrected_page_num} (no correction)", indent=2)
                    corrected_page_num += 1

            out_doc.save(output_path)
            out_doc.close()
            Logger.success(f"Saved corrected PDF: {output_path}", indent=1)

        else:
            Logger.info("No rotations detected, using original PDF", indent=1)
            page_mapping = {i+1: {"method": "pdf_entire_only", "original_page": i+1}
                           for i in range(total_pages)}
            output_path = pdf_path  # Use original PDF

        src_doc.close()

        return output_path, all_results, page_mapping


# ============================================================================
# TABLE EXTRACTION MODULE (Docku.py Integration)
# ============================================================================

class TableExtractor:
    """Advanced table extraction using Docling."""

    def __init__(self):
        self.converter = DocumentConverter()

    def extract_table_from_page(self, pdf_path: str, page_num: int) -> str:
        """
        Extract tables from a specific page and return as HTML markdown.

        Returns:
            Markdown string with HTML tables embedded
        """
        Logger.info(f"Extracting tables from page {page_num} with Docku.py...", indent=2)

        try:
            # Convert single page
            result = self.converter.convert(pdf_path, page_range=(page_num, page_num))
            doc = result.document

            # Extract tables
            tables_data = []
            for table_idx, table in enumerate(doc.tables, 1):
                table_dict = table.model_dump() if hasattr(table, 'model_dump') else table.dict()
                if 'data' in table_dict:
                    tables_data.append({
                        'table_index': table_idx,
                        'raw_cells': table_dict['data'].get('table_cells', [])
                    })

            if not tables_data:
                Logger.warning(f"No tables found on page {page_num}", indent=3)
                return ""

            # Build HTML tables
            markdown_output = []
            for table_data in tables_data:
                structure = self._build_table_structure(table_data['raw_cells'])
                html = self._build_html_table(structure)
                markdown_output.append(f"\n### Table {table_data['table_index']}\n\n{html}\n")
                Logger.success(f"Extracted Table {table_data['table_index']} ({structure['num_rows']}x{structure['num_cols']})", indent=3)

            return "\n".join(markdown_output)

        except Exception as e:
            Logger.error(f"Failed to extract tables: {e}", indent=3)
            return ""

    def _build_table_structure(self, cells: List[Dict]) -> Dict[str, Any]:
        """Build table structure (simplified from Docku.py)."""
        if not cells:
            return {'grid': {}, 'row_positions': [], 'col_positions': [], 'num_rows': 0, 'num_cols': 0}

        row_positions = sorted(set(c['start_row_offset_idx'] for c in cells))
        col_positions = sorted(set(c['start_col_offset_idx'] for c in cells))

        grid = {}
        for cell in cells:
            row_start = cell['start_row_offset_idx']
            col_start = cell['start_col_offset_idx']
            text = cell.get('text', '').strip()

            grid[(row_start, col_start)] = {
                'text': text,
                'row_span': cell.get('row_span', 1),
                'col_span': cell.get('col_span', 1),
                'row_start': row_start,
                'col_start': col_start
            }

        return {
            'grid': grid,
            'row_positions': row_positions,
            'col_positions': col_positions,
            'num_rows': len(row_positions),
            'num_cols': len(col_positions)
        }

    def _build_html_table(self, table_structure: Dict) -> str:
        """Build HTML table."""
        grid = table_structure['grid']
        rows = table_structure['row_positions']
        cols = table_structure['col_positions']

        html = ['<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">']
        covered = set()

        for r in rows:
            html.append('  <tr>')
            for c in cols:
                if (r, c) in covered:
                    continue

                cell = grid.get((r, c))
                if not cell:
                    html.append('    <td></td>')
                    continue

                text = cell['text']
                row_span = cell.get('row_span', 1)
                col_span = cell.get('col_span', 1)

                for rr in range(r, r + row_span):
                    for cc in range(c, c + col_span):
                        if (rr, cc) != (r, c):
                            covered.add((rr, cc))

                attrs = []
                if row_span > 1:
                    attrs.append(f'rowspan="{row_span}"')
                if col_span > 1:
                    attrs.append(f'colspan="{col_span}"')

                html.append(f'    <td {" ".join(attrs)}>{text}</td>')

            html.append('  </tr>')

        html.append('</table>')
        return '\n'.join(html)


# ============================================================================
# TEXT EXTRACTION MODULE (pdf_entire.py Integration)
# ============================================================================

class TextExtractor:
    """Text extraction using pymupdf4llm."""

    @staticmethod
    def extract_text_from_page(pdf_path: str, page_num: int) -> str:
        """
        Extract text from a specific page.

        Returns:
            Markdown formatted text
        """
        Logger.info(f"Extracting text from page {page_num} with pdf_entire.py...", indent=2)

        try:
            import pymupdf4llm

            # Extract markdown for single page (0-indexed)
            try:
                md = pymupdf4llm.to_markdown(pdf_path, pages=[page_num - 1], page_chunks=True)
            except:
                md_text = pymupdf4llm.to_markdown(pdf_path, pages=[page_num - 1])
                md = [{"text": md_text}] if isinstance(md_text, str) else md_text

            # Extract text content
            if isinstance(md, list) and len(md) > 0 and isinstance(md[0], dict) and "text" in md[0]:
                page_md = md[0]["text"] or ""
            elif isinstance(md, dict) and "text" in md:
                page_md = md["text"] or ""
            elif isinstance(md, str):
                page_md = md
            else:
                page_md = str(md)

            Logger.success(f"Extracted {len(page_md)} characters of text", indent=3)
            return page_md

        except Exception as e:
            Logger.error(f"Failed to extract text: {e}", indent=3)
            # Fallback to basic PyMuPDF
            try:
                doc = fitz.open(pdf_path)
                page = doc.load_page(page_num - 1)
                text = page.get_text("text")
                doc.close()
                return text
            except:
                return f"[Extraction failed for page {page_num}]"


# ============================================================================
# MAIN PROCESSOR
# ============================================================================

class AnnualReportProcessor:
    """Main processor orchestrating all modules."""

    def __init__(self):
        self.corrector = OrientationCorrector()
        self.table_extractor = TableExtractor()
        self.text_extractor = TextExtractor()

    def process_directory(self, pdf_dir: str, mode: str):
        """
        Process all PDFs in directory.

        Args:
            pdf_dir: Directory containing PDFs
            mode: "full" or "correction_only"
        """
        pdf_dir = Path(pdf_dir)
        if not pdf_dir.exists():
            Logger.error(f"Directory not found: {pdf_dir}")
            return

        pdf_files = list(pdf_dir.glob("*.pdf"))
        if not pdf_files:
            Logger.error(f"No PDF files found in {pdf_dir}")
            return

        Logger.header("ANNUAL REPORT BATCH PROCESSOR")
        Logger.info(f"Directory: {pdf_dir}")
        Logger.info(f"Found {len(pdf_files)} PDF file(s)")
        Logger.info(f"Mode: {mode.upper()}")

        # Create output directories
        corrected_dir = Path("corrected_pdfs")
        corrected_dir.mkdir(exist_ok=True)

        if mode == "full":
            extracted_dir = Path("extracted_data")
            extracted_dir.mkdir(exist_ok=True)

        start_time = time.time()

        # Process each PDF
        for idx, pdf_path in enumerate(pdf_files, 1):
            Logger.header(f"PROCESSING PDF {idx}/{len(pdf_files)}: {pdf_path.name}")

            pdf_name = pdf_path.stem
            corrected_pdf_path = corrected_dir / f"corrected_{pdf_path.name}"

            # Step 1: Orientation correction
            corrected_pdf, all_results, page_mapping = self.corrector.process_pdf(
                str(pdf_path),
                str(corrected_pdf_path)
            )

            # Step 2: Extraction (if full mode)
            if mode == "full":
                self._extract_content(corrected_pdf, pdf_name, page_mapping, extracted_dir)
            else:
                Logger.info("Skipping extraction (correction only mode)", indent=1)

        elapsed = time.time() - start_time

        Logger.header("PROCESSING COMPLETE")
        Logger.success(f"Total time: {elapsed:.2f} seconds")
        Logger.success(f"Corrected PDFs saved to: {corrected_dir.absolute()}")
        if mode == "full":
            Logger.success(f"Extracted data saved to: {extracted_dir.absolute()}")

    def _extract_content(self, corrected_pdf: str, pdf_name: str,
                        page_mapping: Dict, extracted_dir: Path):
        """Extract content from corrected PDF."""
        Logger.section("Extracting Content")

        # Create output directory for this PDF
        output_dir = extracted_dir / pdf_name
        output_dir.mkdir(exist_ok=True)
        Logger.info(f"Output directory: {output_dir}", indent=1)

        # Process each page according to mapping
        for page_num, mapping_info in sorted(page_mapping.items()):
            method = mapping_info["method"]
            original_page = mapping_info.get("original_page", page_num)

            Logger.progress(f"Processing page {page_num} (original: {original_page})", indent=1)
            Logger.info(f"Method: {method}", indent=2)

            markdown_content = []
            markdown_content.append(f"# Page {page_num}\n")
            markdown_content.append(f"*Original page: {original_page}*\n")

            if "half" in mapping_info:
                markdown_content.append(f"*Half: {mapping_info['half'].upper()}*\n")

            markdown_content.append("\n---\n\n")

            if method == "both":
                # Extract with both Docku.py and pdf_entire.py
                markdown_content.append("## Text Content\n\n")
                text_content = self.text_extractor.extract_text_from_page(corrected_pdf, page_num)
                markdown_content.append(text_content)

                markdown_content.append("\n\n## Tables\n\n")
                tables_content = self.table_extractor.extract_table_from_page(corrected_pdf, page_num)
                if tables_content:
                    markdown_content.append(tables_content)
                else:
                    markdown_content.append("*No tables detected on this page.*\n")

            else:
                # Extract with pdf_entire.py only
                text_content = self.text_extractor.extract_text_from_page(corrected_pdf, page_num)
                markdown_content.append(text_content)

            # Save to file
            output_file = output_dir / f"page_{page_num}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(''.join(markdown_content))

            Logger.success(f"Saved: {output_file.name}", indent=2)

        Logger.success(f"Extraction complete for {pdf_name}", indent=1)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    Logger.header("ANNUAL REPORT BATCH PROCESSOR")
    print(f"{Logger.OKCYAN}This tool processes annual reports with rotation correction and extraction.{Logger.ENDC}\n")

    # Get directory
    pdf_dir = input("Enter directory path containing annual report PDFs: ").strip().strip('"')

    if not os.path.exists(pdf_dir):
        Logger.error("Directory not found!")
        sys.exit(1)

    # Get mode
    print(f"\n{Logger.BOLD}Select processing mode:{Logger.ENDC}")
    print("  1. Full extraction process (correction + extraction)")
    print("  2. Only create corrected PDFs (correction only)")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        mode = "full"
    elif choice == "2":
        mode = "correction_only"
    else:
        Logger.error("Invalid choice!")
        sys.exit(1)

    # Process
    processor = AnnualReportProcessor()
    processor.process_directory(pdf_dir, mode)


if __name__ == "__main__":
    main()
