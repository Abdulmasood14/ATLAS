"""
Section Context Detector for Financial Documents
==================================================

Detects which section of the annual report a chunk belongs to:
- Directors' Report / Board's Report
- Consolidated Financial Statements (Balance Sheet, P&L, Notes)
- Standalone Financial Statements (Balance Sheet, P&L, Notes)

This enables context-aware note extraction where "Note 10" in Consolidated FS
is different from "Note 10" in Standalone FS or Directors' Report.

Author: Financial RAG V2 Enhancement
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SectionType(Enum):
    """Types of sections in annual reports"""
    UNKNOWN = "unknown"
    DIRECTORS_REPORT = "directors_report"
    CONSOLIDATED_BALANCE_SHEET = "consolidated_balance_sheet"
    CONSOLIDATED_PL = "consolidated_pl"
    CONSOLIDATED_CASH_FLOW = "consolidated_cash_flow"
    CONSOLIDATED_EQUITY = "consolidated_equity"
    CONSOLIDATED_NOTES = "consolidated_notes"
    STANDALONE_BALANCE_SHEET = "standalone_balance_sheet"
    STANDALONE_PL = "standalone_pl"
    STANDALONE_CASH_FLOW = "standalone_cash_flow"
    STANDALONE_EQUITY = "standalone_equity"
    STANDALONE_NOTES = "standalone_notes"
    AUDITORS_REPORT = "auditors_report"
    MANAGEMENT_DISCUSSION = "management_discussion"


@dataclass
class SectionBoundary:
    """Represents a section boundary in the document"""
    section_type: SectionType
    section_name: str
    start_pos: int
    end_pos: Optional[int]
    statement_type: str  # 'consolidated', 'standalone', or 'other'
    confidence: float  # 0.0 to 1.0


class SectionContextDetector:
    """
    Detects section boundaries in financial annual reports

    Identifies sections like:
    - Consolidated Financial Statement Notes
    - Standalone Financial Statement Notes
    - Directors' Report
    - etc.
    """

    def __init__(self):
        """Initialize section detector with regex patterns"""

        # CONSOLIDATED patterns
        self.consolidated_patterns = {
            'balance_sheet': [
                r'CONSOLIDATED\s+BALANCE\s+SHEET',
                r'CONSOLIDATED\s+STATEMENT\s+OF\s+FINANCIAL\s+POSITION'
            ],
            'pl': [
                r'CONSOLIDATED\s+STATEMENT\s+OF\s+PROFIT\s+AND\s+LOSS',
                r'CONSOLIDATED\s+PROFIT\s+(?:AND|&)\s+LOSS',
                r'CONSOLIDATED\s+STATEMENT\s+OF\s+COMPREHENSIVE\s+INCOME'
            ],
            'cash_flow': [
                r'CONSOLIDATED\s+CASH\s+FLOW\s+STATEMENT',
                r'CONSOLIDATED\s+STATEMENT\s+OF\s+CASH\s+FLOWS'
            ],
            'equity': [
                r'CONSOLIDATED\s+STATEMENT\s+OF\s+CHANGES\s+IN\s+EQUITY'
            ],
            'notes': [
                r'NOTES?\s+TO\s+(?:THE\s+)?CONSOLIDATED\s+FINANCIAL\s+STATEMENTS?',
                r'NOTES?\s+FORMING\s+PART\s+OF\s+(?:THE\s+)?CONSOLIDATED\s+FINANCIAL\s+STATEMENTS?',
                r'NOTES?\s+(?:ON|TO)\s+CONSOLIDATED\s+(?:ACCOUNTS?|BALANCE\s+SHEET)'
            ]
        }

        # STANDALONE patterns (FIXED: Better detection for implicit standalone sections)
        self.standalone_patterns = {
            'balance_sheet': [
                r'\bBALANCE\s+SHEET\b',  # Will filter out consolidated later
                r'\bSTATEMENT\s+OF\s+FINANCIAL\s+POSITION\b'
            ],
            'pl': [
                r'\bSTATEMENT\s+OF\s+PROFIT\s+AND\s+LOSS\b',
                r'\bPROFIT\s+(?:AND|&)\s+LOSS\b'
            ],
            'cash_flow': [
                r'\bCASH\s+FLOW\s+STATEMENT\b',
                r'\bSTATEMENT\s+OF\s+CASH\s+FLOWS\b'
            ],
            'equity': [
                r'\bSTATEMENT\s+OF\s+CHANGES\s+IN\s+EQUITY\b'
            ],
            'notes': [
                r'NOTES?\s+TO\s+(?:THE\s+)?FINANCIAL\s+STATEMENTS?',
                r'NOTES?\s+FORMING\s+PART\s+OF\s+(?:THE\s+)?FINANCIAL\s+STATEMENTS?',
                r'NOTES?\s+(?:ON|TO)\s+(?:ACCOUNTS?|BALANCE\s+SHEET)'
            ]
        }

        # OTHER patterns
        self.other_patterns = {
            'directors_report': [
                r'DIRECTORS?\s+REPORT',
                r'BOARD\s+REPORT',
                r'REPORT\s+OF\s+THE\s+BOARD\s+OF\s+DIRECTORS?'
            ],
            'auditors_report': [
                r'INDEPENDENT\s+AUDITORS?\s+REPORT',
                r'AUDITORS?\s+REPORT'
            ],
            'md_analysis': [
                r'MANAGEMENT\s+DISCUSSION\s+(?:AND|&)\s+ANALYSIS',
                r'MD\s*&\s*A'
            ]
        }

    def detect_sections(self, text: str) -> List[SectionBoundary]:
        """
        Detect all section boundaries in the document

        Args:
            text: Full document text

        Returns:
            List of SectionBoundary objects sorted by start_pos
        """
        boundaries = []

        # Detect CONSOLIDATED sections FIRST (higher priority)
        consolidated_boundaries = self._detect_pattern_group(
            text, self.consolidated_patterns, 'consolidated'
        )
        boundaries.extend(consolidated_boundaries)

        # Detect STANDALONE sections (filter out if "consolidated" keyword nearby)
        standalone_candidates = self._detect_pattern_group(
            text, self.standalone_patterns, 'standalone'
        )

        # FIXED: Filter out standalone candidates that are actually consolidated
        for candidate in standalone_candidates:
            # Check context around the match (50 chars before and after)
            context_start = max(0, candidate.start_pos - 50)
            context_end = min(len(text), candidate.start_pos + len(candidate.section_name) + 50)
            context = text[context_start:context_end].lower()

            # Skip if "consolidated" keyword is nearby
            if 'consolidat' not in context:
                # Also skip if this position overlaps with a consolidated boundary
                overlaps = False
                for cons_boundary in consolidated_boundaries:
                    if abs(candidate.start_pos - cons_boundary.start_pos) < 20:
                        overlaps = True
                        break

                if not overlaps:
                    boundaries.append(candidate)

        # Detect OTHER sections
        boundaries.extend(self._detect_other_sections(text))

        # Sort by position
        boundaries.sort(key=lambda x: x.start_pos)

        # Set end positions
        for i in range(len(boundaries)):
            if i < len(boundaries) - 1:
                boundaries[i].end_pos = boundaries[i + 1].start_pos
            else:
                boundaries[i].end_pos = len(text)

        # Filter overlapping boundaries (keep highest confidence)
        boundaries = self._filter_overlaps(boundaries)

        return boundaries

    def _detect_pattern_group(
        self,
        text: str,
        pattern_dict: Dict[str, List[str]],
        statement_type: str
    ) -> List[SectionBoundary]:
        """Detect sections using a pattern dictionary"""
        boundaries = []

        for sub_type, patterns in pattern_dict.items():
            for pattern_str in patterns:
                pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)

                for match in pattern.finditer(text):
                    section_type = self._map_to_section_type(sub_type, statement_type)

                    boundaries.append(SectionBoundary(
                        section_type=section_type,
                        section_name=match.group(0).strip(),
                        start_pos=match.start(),
                        end_pos=None,
                        statement_type=statement_type,
                        confidence=1.0
                    ))

        return boundaries

    def _detect_other_sections(self, text: str) -> List[SectionBoundary]:
        """Detect non-financial statement sections"""
        boundaries = []

        for sub_type, patterns in self.other_patterns.items():
            for pattern_str in patterns:
                pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)

                for match in pattern.finditer(text):
                    section_type = self._map_other_section_type(sub_type)

                    boundaries.append(SectionBoundary(
                        section_type=section_type,
                        section_name=match.group(0).strip(),
                        start_pos=match.start(),
                        end_pos=None,
                        statement_type='other',
                        confidence=1.0
                    ))

        return boundaries

    def _map_to_section_type(self, sub_type: str, statement_type: str) -> SectionType:
        """Map sub-type and statement type to SectionType enum"""
        mapping = {
            ('balance_sheet', 'consolidated'): SectionType.CONSOLIDATED_BALANCE_SHEET,
            ('pl', 'consolidated'): SectionType.CONSOLIDATED_PL,
            ('cash_flow', 'consolidated'): SectionType.CONSOLIDATED_CASH_FLOW,
            ('equity', 'consolidated'): SectionType.CONSOLIDATED_EQUITY,
            ('notes', 'consolidated'): SectionType.CONSOLIDATED_NOTES,
            ('balance_sheet', 'standalone'): SectionType.STANDALONE_BALANCE_SHEET,
            ('pl', 'standalone'): SectionType.STANDALONE_PL,
            ('cash_flow', 'standalone'): SectionType.STANDALONE_CASH_FLOW,
            ('equity', 'standalone'): SectionType.STANDALONE_EQUITY,
            ('notes', 'standalone'): SectionType.STANDALONE_NOTES,
        }

        return mapping.get((sub_type, statement_type), SectionType.UNKNOWN)

    def _map_other_section_type(self, sub_type: str) -> SectionType:
        """Map other section types"""
        mapping = {
            'directors_report': SectionType.DIRECTORS_REPORT,
            'auditors_report': SectionType.AUDITORS_REPORT,
            'md_analysis': SectionType.MANAGEMENT_DISCUSSION
        }

        return mapping.get(sub_type, SectionType.UNKNOWN)

    def _filter_overlaps(self, boundaries: List[SectionBoundary]) -> List[SectionBoundary]:
        """Filter overlapping boundaries, keeping highest confidence"""
        if not boundaries:
            return []

        filtered = [boundaries[0]]

        for current in boundaries[1:]:
            previous = filtered[-1]

            # Check if overlapping
            if current.start_pos < previous.end_pos:
                # Keep the one with higher confidence
                if current.confidence > previous.confidence:
                    filtered[-1] = current
                # If same confidence, prefer more specific section
                elif current.confidence == previous.confidence:
                    if self._is_more_specific(current, previous):
                        filtered[-1] = current
            else:
                filtered.append(current)

        return filtered

    def _is_more_specific(self, a: SectionBoundary, b: SectionBoundary) -> bool:
        """Check if section 'a' is more specific than section 'b'"""
        # Notes sections are more specific than general statements
        specific_order = [
            SectionType.CONSOLIDATED_NOTES,
            SectionType.STANDALONE_NOTES,
            SectionType.CONSOLIDATED_BALANCE_SHEET,
            SectionType.STANDALONE_BALANCE_SHEET,
            SectionType.CONSOLIDATED_PL,
            SectionType.STANDALONE_PL,
        ]

        try:
            return specific_order.index(a.section_type) < specific_order.index(b.section_type)
        except ValueError:
            return False

    def get_section_at_position(
        self,
        text: str,
        position: int,
        boundaries: Optional[List[SectionBoundary]] = None
    ) -> Optional[SectionBoundary]:
        """
        Get the section that contains the given position

        Args:
            text: Full document text
            position: Character position in document
            boundaries: Pre-computed boundaries (optional, will detect if not provided)

        Returns:
            SectionBoundary object or None if not found
        """
        if boundaries is None:
            boundaries = self.detect_sections(text)

        for boundary in boundaries:
            if boundary.start_pos <= position < boundary.end_pos:
                return boundary

        return None

    def get_section_for_chunk(
        self,
        text: str,
        chunk_start: int,
        chunk_end: int,
        boundaries: Optional[List[SectionBoundary]] = None
    ) -> Optional[SectionBoundary]:
        """
        Get the section that contains the given chunk

        Args:
            text: Full document text
            chunk_start: Chunk start position
            chunk_end: Chunk end position
            boundaries: Pre-computed boundaries

        Returns:
            SectionBoundary object or None
        """
        if boundaries is None:
            boundaries = self.detect_sections(text)

        # Find section containing the majority of the chunk
        chunk_mid = (chunk_start + chunk_end) // 2
        return self.get_section_at_position(text, chunk_mid, boundaries)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def extract_statement_type_from_query(query: str) -> Optional[str]:
    """
    Extract statement type from user query

    Args:
        query: User's question

    Returns:
        'consolidated', 'standalone', or None
    """
    query_lower = query.lower()

    # Check for consolidated
    if re.search(r'consolidat(?:ed|ion)', query_lower):
        return 'consolidated'

    # Check for standalone
    if re.search(r'standalone|stand\s*alone|separate', query_lower):
        return 'standalone'

    return None


def extract_note_number_from_query(query: str) -> Optional[str]:
    """
    Extract note number from user query

    Args:
        query: User's question

    Returns:
        Note number like 'Note 10', 'Note 9.1', etc. or None
    """
    # Pattern: "Note 10", "Note 9", "Note 12.1", etc.
    pattern = r'(?:note|notes?)\s+(?:no\.?\s*)?(\d+(?:\.\d+)?)'
    match = re.search(pattern, query, re.IGNORECASE)

    if match:
        note_num = match.group(1)
        return f'Note {note_num}'

    return None


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test section detection
    test_text = """
    DIRECTORS' REPORT

    The Board is pleased to present the report...

    CONSOLIDATED BALANCE SHEET AS AT 31ST MARCH, 2025

    Particulars | Note No. | Amount
    Trade receivables | 10 | 1,504.69

    NOTES TO THE CONSOLIDATED FINANCIAL STATEMENTS FOR THE YEAR ENDED 31ST MARCH 2025

    10. Trade receivables

    Current
    Trade Receivables considered good: 1,504.69

    BALANCE SHEET AS AT 31ST MARCH, 2025

    Particulars | Note No. | Amount
    Trade receivables | 9 | 2,082.50

    NOTES TO THE FINANCIAL STATEMENTS FOR THE YEAR ENDED 31ST MARCH 2025

    9. Trade receivables

    Current
    Trade Receivables considered good: 2,082.50
    """

    detector = SectionContextDetector()
    boundaries = detector.detect_sections(test_text)

    print("="*80)
    print("DETECTED SECTIONS")
    print("="*80)
    for b in boundaries:
        print(f"\n{b.section_type.value.upper()}")
        print(f"  Name: {b.section_name}")
        print(f"  Statement Type: {b.statement_type}")
        print(f"  Position: {b.start_pos} - {b.end_pos}")
        print(f"  Text preview: {test_text[b.start_pos:b.start_pos+50]}...")

    # Test query parsing
    print("\n" + "="*80)
    print("QUERY PARSING TESTS")
    print("="*80)

    test_queries = [
        "What is Note 10 about in Consolidated Financial Statement?",
        "What is Note 9 in Standalone?",
        "Show me Note 12.1",
        "Trade receivables standalone"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        print(f"  Statement type: {extract_statement_type_from_query(query)}")
        print(f"  Note number: {extract_note_number_from_query(query)}")
