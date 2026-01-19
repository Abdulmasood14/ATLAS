"""
Universal Financial Document Classifier

Multi-label classification system that works with ANY financial PDF.
Classifies chunks by section type, note number, and statement type.

Based on analysis of 9 different financial PDFs.
"""
import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass


@dataclass
class ChunkClassification:
    """Classification result for a document chunk"""
    section_types: List[str]  # Multi-label: ['balance_sheet', 'fair_value', 'notes']
    note_number: Optional[str]  # 'Note 12', 'Note 5.3', etc.
    statement_type: Optional[str]  # 'standalone', 'consolidated', 'both'
    confidence: float  # 0.0 to 1.0


class UniversalClassifier:
    """
    Universal classifier for financial documents

    Detects:
    - Section types (balance sheet, income statement, notes, etc.)
    - Note numbers (Note 1, Note 12, etc.)
    - Statement types (standalone vs consolidated)
    """

    # Section type keywords (multi-label - chunk can belong to multiple sections)
    SECTION_PATTERNS = {
        'balance_sheet': [
            r'balance\s+sheet',
            r'statement\s+of\s+financial\s+position',
            r'assets\s+and\s+liabilities'
        ],
        'income_statement': [
            r'statement\s+of\s+profit',
            r'income\s+statement',
            r'profit\s+and\s+loss',
            r'statement\s+of\s+comprehensive\s+income'
        ],
        'cash_flow': [
            r'cash\s+flow',
            r'statement\s+of\s+cash\s+flows'
        ],
        'notes': [
            r'notes?\s+to\s+.*?financial\s+statements',
            r'notes?\s+to\s+.*?accounts',
            r'note\s+\d+'
        ],
        'fair_value': [
            r'fair\s+value',
            r'level\s+[123]\s+fair\s+value',
            r'fair\s+value\s+measurement'
        ],
        'investment_property': [
            r'investment\s+propert(?:y|ies)',
            r'rental\s+propert(?:y|ies)',
            r'commercial\s+propert(?:y|ies)'
        ],
        'borrowings': [
            r'borrowings?',
            r'loans?\s+and\s+advances',
            r'debt',
            r'term\s+loans?'
        ],
        'equity': [
            r'equity',
            r'share\s+capital',
            r'reserves\s+and\s+surplus',
            r'shareholders?\s+funds?'
        ],
        'ppe': [
            r'property,?\s+plant\s+and\s+equipment',
            r'fixed\s+assets',
            r'tangible\s+assets'
        ],
        'intangibles': [
            r'intangible\s+assets',
            r'goodwill',
            r'intellectual\s+property'
        ],
        'revenue_details': [
            r'revenue\s+from\s+operations',
            r'revenue\s+recognition',
            r'disaggregation\s+of\s+revenue'
        ],
        'expense_details': [
            r'cost\s+of\s+goods\s+sold',
            r'operating\s+expenses',
            r'administrative\s+expenses'
        ],
        'related_party': [
            r'related\s+part(?:y|ies)',
            r'related\s+entities'
        ],
        'contingencies': [
            r'contingent\s+liabilit(?:y|ies)',
            r'commitments?',
            r'contingencies'
        ],
        'eps': [
            r'earnings?\s+per\s+share',
            r'\beps\b'
        ],
        'segment_reporting': [
            r'segment\s+reporting',
            r'operating\s+segments',
            r'geographical\s+segments'
        ],
        'dividend': [
            r'dividend',
            r'distribution\s+to\s+shareholders'
        ],
        'auditors_report': [
            r'independent\s+auditor',
            r'auditor.?s\s+report',
            r'opinion\s+on\s+.*?financial\s+statements'
        ],
        'md_and_a': [
            r'management.?s?\s+discussion',
            r'md\s*&\s*a',
            r'directors?.?\s+report'
        ],
        'accounting_policies': [
            r'significant\s+accounting\s+policies',
            r'basis\s+of\s+preparation',
            r'accounting\s+standards'
        ],
        'risk_factors': [
            r'risk\s+factors',
            r'risk\s+management',
            r'financial\s+risks?'
        ]
    }

    # Statement type patterns
    STATEMENT_TYPE_PATTERNS = {
        'standalone': [
            r'\bstandalone\b',
            r'\bstand\s*alone\b',
            r'separate\s+financial\s+statements'
        ],
        'consolidated': [
            r'\bconsolidated\b',
            r'consolidated\s+financial\s+statements',
            r'group\s+financial\s+statements'
        ]
    }

    def __init__(self):
        """Initialize classifier with compiled regex patterns"""
        # Compile all patterns for performance
        self.section_patterns_compiled = {
            section: [re.compile(pattern, re.IGNORECASE)
                     for pattern in patterns]
            for section, patterns in self.SECTION_PATTERNS.items()
        }

        self.statement_patterns_compiled = {
            stmt_type: [re.compile(pattern, re.IGNORECASE)
                       for pattern in patterns]
            for stmt_type, patterns in self.STATEMENT_TYPE_PATTERNS.items()
        }

        # Enhanced note number patterns (multiple patterns for better coverage)
        self.note_patterns = [
            # Primary pattern: "Note 10", "NOTE 12", "Note 3A", "Note 10.1"
            re.compile(r'\bnote\s+(\d+[A-Z]?(?:\.\d+)?)\b', re.IGNORECASE),

            # Pattern with separators: "Note 10:", "Note 12 -", "Note 5 –"
            re.compile(r'\bnote\s+(\d+[A-Z]?(?:\.\d+)?)\s*[-–—:]', re.IGNORECASE),

            # Header pattern: "NOTE 10 - Investment Property"
            re.compile(r'^NOTE\s+(\d+[A-Z]?(?:\.\d+)?)\s*[-–—:]?\s*[A-Z]', re.MULTILINE | re.IGNORECASE),

            # Numbered list at line start: "10. Trade receivables"
            re.compile(r'^\s*(\d+[A-Z]?)\.\s+[A-Z]', re.MULTILINE),

            # Sub-note pattern: "10.1", "12.3" in context
            re.compile(r'\b(\d+\.\d+)\s+[A-Z]', re.MULTILINE),

            # Reference pattern: "(Note 10)", "[Note 12]"
            re.compile(r'[\(\[]note\s+(\d+[A-Z]?(?:\.\d+)?)[\)\]]', re.IGNORECASE)
        ]

    def classify(
        self,
        chunk_text: str,
        page_number: Optional[int] = None,
        section_context: Optional[str] = None
    ) -> ChunkClassification:
        """
        Classify a chunk of text

        Args:
            chunk_text: Text to classify
            page_number: Optional page number for context
            section_context: Optional section type ('consolidated', 'standalone', 'other')
                           from document-level section detection. If provided, this
                           OVERRIDES keyword-based detection for better accuracy.

        Returns:
            ChunkClassification with detected labels
        """
        # Detect section types (multi-label)
        section_types = self._detect_sections(chunk_text.lower())

        # Detect note number (use original case for better matching)
        note_number = self._detect_note_number(chunk_text)

        # Detect statement type - use section_context if available
        if section_context:
            # Use document-level section context (more reliable)
            statement_type = section_context
        else:
            # Fall back to keyword-based detection
            statement_type = self._detect_statement_type(chunk_text.lower())

        # Calculate confidence
        confidence = self._calculate_confidence(
            section_types, note_number, statement_type, section_context is not None
        )

        return ChunkClassification(
            section_types=list(section_types),
            note_number=note_number,
            statement_type=statement_type,
            confidence=confidence
        )

    def _detect_sections(self, text_lower: str) -> Set[str]:
        """Detect all matching section types"""
        detected_sections = set()

        for section, patterns in self.section_patterns_compiled.items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    detected_sections.add(section)
                    break  # One match per section is enough

        return detected_sections

    def _detect_note_number(self, text: str) -> Optional[str]:
        """
        Detect note number in text using multiple patterns

        Examples: 'Note 12', 'Note 5.3', 'Note 1', 'Note 3A'

        Returns the FIRST/MOST PROMINENT note number found, prioritizing:
        1. Header patterns (at start of lines)
        2. Explicit "Note X" mentions
        3. Numbered lists
        4. References in parentheses
        """
        # Try each pattern in order of priority
        for pattern in self.note_patterns:
            match = pattern.search(text)
            if match:
                note_num = match.group(1).upper()  # Normalize to uppercase
                # Format consistently
                if '.' in note_num:
                    # Sub-note: "10.1"
                    return f"Note {note_num}"
                elif note_num[-1].isalpha():
                    # Letter suffix: "3A"
                    return f"Note {note_num}"
                else:
                    # Regular note: "10"
                    return f"Note {note_num}"

        return None

    def _detect_statement_type(self, text_lower: str) -> Optional[str]:
        """
        Detect if standalone, consolidated, or both

        Returns: 'standalone', 'consolidated', 'both', or None
        """
        standalone_match = False
        consolidated_match = False

        for pattern in self.statement_patterns_compiled['standalone']:
            if pattern.search(text_lower):
                standalone_match = True
                break

        for pattern in self.statement_patterns_compiled['consolidated']:
            if pattern.search(text_lower):
                consolidated_match = True
                break

        if standalone_match and consolidated_match:
            return 'both'
        elif standalone_match:
            return 'standalone'
        elif consolidated_match:
            return 'consolidated'
        else:
            return None

    def _calculate_confidence(
        self,
        section_types: Set[str],
        note_number: Optional[str],
        statement_type: Optional[str],
        has_section_context: bool = False
    ) -> float:
        """
        Calculate confidence score for classification

        Confidence based on:
        - Number of section matches
        - Presence of note number
        - Presence of statement type
        - Whether section context was provided
        """
        confidence = 0.5  # Base confidence

        # Boost for each section detected
        if section_types:
            confidence += min(len(section_types) * 0.1, 0.3)

        # Boost for note number
        if note_number:
            confidence += 0.15  # Increased from 0.1

        # Boost for statement type
        if statement_type:
            if has_section_context:
                # Higher confidence when using document-level context
                confidence += 0.20
            else:
                # Lower confidence for keyword-based detection
                confidence += 0.05

        return min(confidence, 1.0)

    def is_critical_paragraph(self, text: str) -> bool:
        """
        Detect paragraphs that should NEVER be split during chunking

        Critical paragraphs include:
        - Fair Value disclosures
        - Investment Property descriptions
        - Key accounting policy statements
        - Note introductions
        """
        text_lower = text.lower()

        critical_keywords = [
            'fair value',
            'investment propert',
            'as at march 31',
            'as at',
            'carrying amount',
            'note:', 'note ',
            'significant accounting',
            'the group\'s investment',
            'the company\'s investment',
            'determined based on',
            'fair values of the properties',
            'properties are inr'
        ]

        # Check if text contains any critical keywords
        for keyword in critical_keywords:
            if keyword in text_lower:
                return True

        return False


# ============================================================================
# TEST/DEMO
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("UNIVERSAL CLASSIFIER - TEST")
    print("="*80)

    classifier = UniversalClassifier()

    # Test cases
    test_cases = [
        {
            'name': 'Fair Value Paragraph (Page 196)',
            'text': """The Group's investment properties consists of Retail Malls and
                      Commercial Buildings. As at March 31, 2025 and March 31, 2024,
                      the fair values of the properties are INR 31,34,063.00 lakhs and
                      INR 28,96,370.00 lakhs respectively."""
        },
        {
            'name': 'Balance Sheet',
            'text': """BALANCE SHEET AS AT MARCH 31, 2025
                      (Standalone)

                      ASSETS
                      Non-current assets
                      Investment Property: 3,142.77"""
        },
        {
            'name': 'Note Disclosure',
            'text': """NOTE 12 - INVESTMENT PROPERTY

                      The Group has investment properties comprising of commercial
                      and retail properties."""
        },
        {
            'name': 'Consolidated Income Statement',
            'text': """CONSOLIDATED STATEMENT OF PROFIT AND LOSS
                      FOR THE YEAR ENDED MARCH 31, 2025

                      Revenue from Operations: 1,250.50 crores"""
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'-'*80}")
        print(f"Test {i}: {test['name']}")
        print(f"{'-'*80}")

        result = classifier.classify(test['text'])

        print(f"Section Types: {result.section_types}")
        print(f"Note Number: {result.note_number}")
        print(f"Statement Type: {result.statement_type}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Is Critical: {classifier.is_critical_paragraph(test['text'])}")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
