"""
Vision OCR Module - Qwen 2.5 VL Integration

Handles OCR extraction for scanned pages using Qwen 2.5 VL vision-language model.
Fallback for pages where pdfplumber fails to extract text.
"""
import base64
import requests
import json
from typing import Dict, Optional, Tuple
from io import BytesIO
from PIL import Image
import pdfplumber


class VisionOCR:
    """
    Vision-based OCR using Qwen 2.5 VL for scanned document pages

    Features:
    - Automatic detection of scanned pages (no text extractable)
    - Multi-modal extraction: text, tables, numbers, structure
    - Financial document optimization
    - Structured JSON output
    """

    def __init__(
        self,
        vision_endpoint: str = "http://10.100.20.76:11434/v1/chat/completions",
        vision_model: str = "qwen2.5vl:latest",
        temperature: float = 0.1  # Low temperature for accurate OCR
    ):
        """
        Initialize Vision OCR system

        Args:
            vision_endpoint: Qwen 2.5 VL API endpoint
            vision_model: Model name (qwen2.5vl:latest)
            temperature: Temperature for generation (0.1 for precision)
        """
        self.endpoint = vision_endpoint
        self.model = vision_model
        self.temperature = temperature

        # Optimized prompt for financial document OCR
        self.system_prompt = """You are an expert financial document analyst specializing in high-precision OCR.
Your mission is to extract text and tables from financial document images with 100% accuracy.

CRITICAL INSTRUCTIONS:
1. TABLE EXTRACTION:
   - Identify every table in the image.
   - Extract tables as valid GitHub-Flavored Markdown tables.
   - Ensure every number is placed in its correct row and column.
   - Preserve all headers, sub-headers, and totals exactly as they appear.
   - If a table has nested headers, represent them as best as possible in Markdown.

2. TEXT & STRUCTURE:
   - Extract all other text (paragraphs, titles, signatures).
   - Preserve the hierarchical structure (e.g., "1. Assets -> (a) Non-current assets").
   - Maintain the reading order of the document.

3. NUMBERS & SYMBOLS:
   - Capture all currency symbols (₹, Rs., INR) and units (Lakhs, Crores).
   - DO NOT drop decimal points or commas in figures.
   - If a number is in parentheses like (1,234.50), keep the parentheses as they indicate negative values.

4. LOGO & FOOTNOTES:
   - Include company names, logos (as text), and page numbers if visible.
   - Capture small print and footnotes at the bottom of the page.

OUTPUT FORMAT:
Provide the output as a stream of text with embedded Markdown tables. Do not include any meta-commentary like "Here is the extracted text". Only output the document content."""

    def is_scanned_page(self, page_text: Optional[str], min_chars: int = 50) -> bool:
        """
        Determine if a page is scanned (no extractable text)

        Args:
            page_text: Text extracted by pdfplumber
            min_chars: Minimum characters to consider page as "has text"

        Returns:
            True if page appears to be scanned (no text), False otherwise
        """
        if not page_text:
            return True

        # Strip whitespace and check length
        clean_text = page_text.strip()

        if len(clean_text) < min_chars:
            return True

        # Check if text is mostly garbage characters (corrupted extraction)
        # Count alphanumeric vs total characters
        alnum_count = sum(c.isalnum() for c in clean_text)
        total_count = len(clean_text)

        if total_count > 0:
            alnum_ratio = alnum_count / total_count
            # If less than 20% alphanumeric, likely corrupted/scanned (Financial docs have many symbols, so 20% is safer)
            if alnum_ratio < 0.2:
                return True

        return False

    def pdf_page_to_image(self, pdf_path: str, page_num: int, dpi: int = 400) -> bytes:
        """
        Convert PDF page to image bytes

        Args:
            pdf_path: Path to PDF file
            page_num: Page number (1-indexed)
            dpi: Resolution for image conversion (400 recommended for high-precision OCR)

        Returns:
            Image bytes (PNG format)
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[page_num - 1]  # pdfplumber is 0-indexed

                # Convert page to PIL Image
                im = page.to_image(resolution=dpi)

                # Convert to bytes
                img_byte_arr = BytesIO()
                im.original.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)

                return img_byte_arr.getvalue()

        except Exception as e:
            raise Exception(f"Failed to convert PDF page to image: {e}")

    def image_to_base64(self, image_bytes: bytes) -> str:
        """
        Convert image bytes to base64 string

        Args:
            image_bytes: Image bytes (PNG/JPEG)

        Returns:
            Base64 encoded string
        """
        return base64.b64encode(image_bytes).decode('utf-8')

    def extract_text_from_image(
        self,
        image_bytes: bytes,
        extract_tables: bool = True,
        verbose: bool = False
    ) -> Dict[str, any]:
        """
        Extract text from image using Qwen 2.5 VL

        Args:
            image_bytes: Image bytes (PNG/JPEG)
            extract_tables: Whether to explicitly request table extraction
            verbose: Print debug information

        Returns:
            Dictionary with:
                - text: Extracted text
                - success: Boolean
                - error: Error message if failed
        """
        try:
            # Convert image to base64
            image_b64 = self.image_to_base64(image_bytes)

            # Construct user prompt
            user_prompt = "Extract all text from this document image while preserving its structure and layout."

            if extract_tables:
                user_prompt += "\n\nPay special attention to tables - extract them in a structured format showing rows and columns clearly."

            # Prepare request payload
            # Qwen 2.5 VL API format
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": self.temperature,
                "max_tokens": 4000,  # Allow long outputs for full page extraction
                "top_p": 0.9
            }

            if verbose:
                print(f"Sending OCR request to {self.endpoint}")
                print(f"Model: {self.model}")
                print(f"Temperature: {self.temperature}")

            # Make API request
            response = requests.post(
                self.endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120  # 2 minutes timeout for OCR
            )

            if response.status_code != 200:
                return {
                    'text': '',
                    'success': False,
                    'error': f"API returned status {response.status_code}: {response.text}"
                }

            # Parse response
            result = response.json()

            # Extract text from response
            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0].get('message', {})
                extracted_text = message.get('content', '')

                if verbose:
                    print(f"OCR Success! Extracted {len(extracted_text)} characters")

                return {
                    'text': extracted_text,
                    'success': True,
                    'error': None
                }
            else:
                return {
                    'text': '',
                    'success': False,
                    'error': "No content in API response"
                }

        except requests.exceptions.Timeout:
            return {
                'text': '',
                'success': False,
                'error': "OCR request timed out after 120 seconds"
            }
        except Exception as e:
            return {
                'text': '',
                'success': False,
                'error': f"OCR extraction failed: {str(e)}"
            }

    def extract_page_with_fallback(
        self,
        pdf_path: str,
        page_num: int,
        pdfplumber_text: Optional[str],
        verbose: bool = False
    ) -> Tuple[str, str]:
        """
        Extract page text with OCR fallback

        Workflow:
        1. Check if pdfplumber_text is valid
        2. If scanned page detected, use Vision OCR
        3. Return extracted text and extraction method

        Args:
            pdf_path: Path to PDF file
            page_num: Page number (1-indexed)
            pdfplumber_text: Text already extracted by pdfplumber (or None)
            verbose: Print debug information

        Returns:
            Tuple of (extracted_text, extraction_method)
            extraction_method: 'pdfplumber' or 'vision_ocr'
        """
        # Check if page is scanned
        if not self.is_scanned_page(pdfplumber_text):
            # pdfplumber text is good
            if verbose:
                print(f"Page {page_num}: Using pdfplumber extraction")
            return (pdfplumber_text, 'pdfplumber')

        # Page is scanned - use Vision OCR
        if verbose:
            print(f"Page {page_num}: Scanned page detected - using Vision OCR")

        try:
            # Convert page to image
            image_bytes = self.pdf_page_to_image(pdf_path, page_num)

            # Extract text using Vision OCR
            ocr_result = self.extract_text_from_image(
                image_bytes,
                extract_tables=True,
                verbose=verbose
            )

            if ocr_result['success']:
                if verbose:
                    print(f"Page {page_num}: OCR successful - {len(ocr_result['text'])} characters")
                return (ocr_result['text'], 'vision_ocr')
            else:
                if verbose:
                    print(f"Page {page_num}: OCR failed - {ocr_result['error']}")
                # Return empty string with OCR method indicator
                return ('', 'vision_ocr_failed')

        except Exception as e:
            if verbose:
                print(f"Page {page_num}: OCR error - {str(e)}")
            return ('', 'vision_ocr_failed')

    def close(self):
        """Close any open connections (placeholder for future cleanup)"""
        pass


# ============================================================================
# TEST/DEMO
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("VISION OCR MODULE - QWEN 2.5 VL TEST")
    print("="*80)

    # Initialize Vision OCR
    print("\nInitializing Vision OCR system...")
    ocr = VisionOCR()
    print("Vision OCR initialized!")

    print("\nConfiguration:")
    print(f"  Endpoint: {ocr.endpoint}")
    print(f"  Model: {ocr.model}")
    print(f"  Temperature: {ocr.temperature}")

    # Test scanned page detection
    print("\n" + "-"*80)
    print("TEST 1: Scanned Page Detection")
    print("-"*80)

    test_cases = [
        ("", "Empty string"),
        ("   \n  \n   ", "Only whitespace"),
        ("Short", "Too short (< 50 chars)"),
        ("This is a normal page with plenty of text that was successfully extracted by pdfplumber.", "Normal text"),
        ("!!!@@@###$$$%%%", "Garbage characters")
    ]

    for text, description in test_cases:
        is_scanned = ocr.is_scanned_page(text)
        print(f"  {description:30s} → Scanned: {is_scanned}")

    print("\n" + "-"*80)
    print("TEST 2: Ready for OCR Extraction")
    print("-"*80)
    print("To test OCR on an actual scanned page:")
    print("  1. Ensure Qwen 2.5 VL is running on the server")
    print("  2. Use extract_page_with_fallback() on a PDF with scanned pages")
    print("  3. System will automatically detect and OCR scanned pages")

    print("\n" + "="*80)
    print("VISION OCR MODULE READY")
    print("="*80)

    ocr.close()
