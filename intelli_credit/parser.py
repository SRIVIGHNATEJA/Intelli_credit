"""
PDF Parser - Extract financial data from PDF documents
Implements robust extraction with fallback chain: pdfplumber → OCR → Groq cleanup

CRITICAL SAFEGUARDS:
1. Robust JSON parsing: Strip Markdown code blocks before parsing
2. Defensive OCR: Wrap pytesseract/pdf2image in try/except for missing binaries
3. Corrupted PDF guard: Wrap pdfplumber.open() in try/except for malformed PDFs
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

import pdfplumber
from groq import Groq

from prompts import (
    get_extraction_prompt,
    get_ocr_cleanup_prompt,
    enforce_json_output,
    get_system_message
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_FILE_SIZE_MB = 8
MAX_PAGES = 20
VALID_DOCUMENT_TYPES = [
    "balance_sheet",
    "profit_loss",
    "bank_statements",
    "gst_returns",
    "itr",
    "sanction_letter"
]


# ============================================================================
# FILE VALIDATION (Task 15.1)
# ============================================================================

def validate_file_size(file_path: str) -> tuple[bool, Optional[str]]:
    """
    Validate that file size is within acceptable limits (≤8MB).
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        if file_size_mb > MAX_FILE_SIZE_MB:
            error_msg = f"File size {file_size_mb:.2f}MB exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB"
            logger.warning(error_msg)
            return False, error_msg
        
        logger.info(f"File size validation passed: {file_size_mb:.2f}MB")
        return True, None
        
    except Exception as e:
        error_msg = f"Error checking file size: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def count_pages(file_path: str) -> tuple[Optional[int], Optional[str]]:
    """
    Count pages in PDF and validate against limit (≤20 pages).
    
    SAFEGUARD: Wraps pdfplumber.open() in try/except for corrupted PDFs.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        tuple: (page_count, error_message)
    """
    try:
        # SAFEGUARD 3: Wrap pdfplumber.open() for corrupted PDFs
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            
            if page_count > MAX_PAGES:
                error_msg = f"Document has {page_count} pages, exceeds maximum of {MAX_PAGES} pages"
                logger.warning(error_msg)
                return page_count, error_msg
            
            logger.info(f"Page count validation passed: {page_count} pages")
            return page_count, None
            
    except Exception as e:
        error_msg = f"Error reading PDF (possibly corrupted): {str(e)}"
        logger.error(error_msg)
        return None, error_msg


# ============================================================================
# EXTRACTION WITH FALLBACK CHAIN (Task 15.2)
# ============================================================================

def extract_with_pdfplumber(file_path: str) -> Optional[str]:
    """
    Extract text from digital PDF using pdfplumber.
    
    SAFEGUARD: Wraps pdfplumber.open() in try/except for corrupted PDFs.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        str: Extracted text, or None if extraction fails
    """
    try:
        # SAFEGUARD 3: Wrap pdfplumber.open() for corrupted PDFs
        with pdfplumber.open(file_path) as pdf:
            text_parts = []
            
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            full_text = "\n".join(text_parts)
            
            if full_text.strip():
                logger.info(f"Successfully extracted {len(full_text)} characters with pdfplumber")
                return full_text
            else:
                logger.warning("pdfplumber extracted empty text")
                return None
                
    except Exception as e:
        logger.error(f"pdfplumber extraction failed: {str(e)}")
        return None


def extract_with_ocr(file_path: str) -> Optional[str]:
    """
    Extract text from scanned PDF using OCR (pytesseract + pdf2image).
    
    SAFEGUARD: Wraps pytesseract and pdf2image in try/except for missing system binaries.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        str: Extracted text, or None if OCR fails
    """
    try:
        # SAFEGUARD 2: Defensive OCR - wrap imports and calls
        import pytesseract
        from pdf2image import convert_from_path
        
        logger.info("Attempting OCR extraction...")
        
        # Convert PDF pages to images
        images = convert_from_path(file_path)
        
        text_parts = []
        for i, image in enumerate(images):
            # Extract text from each page image
            page_text = pytesseract.image_to_string(image)
            if page_text:
                text_parts.append(page_text)
            logger.info(f"OCR processed page {i+1}/{len(images)}")
        
        full_text = "\n".join(text_parts)
        
        if full_text.strip():
            logger.info(f"Successfully extracted {len(full_text)} characters with OCR")
            return full_text
        else:
            logger.warning("OCR extracted empty text")
            return None
            
    except ImportError as e:
        logger.error(f"OCR libraries not available: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"OCR extraction failed (possibly missing Poppler or Tesseract binaries): {str(e)}")
        return None


def cleanup_with_groq(
    ocr_text: str,
    document_type: str,
    groq_client: Optional[Groq] = None
) -> Optional[Dict[str, Any]]:
    """
    Clean OCR artifacts and structure data using Groq API.
    
    SAFEGUARD: Strips Markdown code blocks (```json ... ```) before parsing JSON.
    
    Args:
        ocr_text: Raw OCR text with potential artifacts
        document_type: Type of document being processed
        groq_client: Optional Groq client instance
        
    Returns:
        dict: Cleaned and structured data, or None if cleanup fails
    """
    try:
        # Initialize Groq client if not provided
        if groq_client is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                logger.error("GROQ_API_KEY not found in environment")
                return None
            groq_client = Groq(api_key=api_key)
        
        # Get cleanup prompt
        prompt = enforce_json_output(get_ocr_cleanup_prompt(ocr_text))
        
        logger.info("Calling Groq API for OCR cleanup...")
        
        # Call Groq API
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": get_system_message()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # SAFEGUARD 1: Strip Markdown code blocks before parsing JSON
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith("```"):
            response_text = response_text[3:]  # Remove ```
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Remove trailing ```
        
        response_text = response_text.strip()
        
        # Parse JSON
        cleaned_data = json.loads(response_text)
        
        logger.info("Successfully cleaned OCR text with Groq")
        return cleaned_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Groq response as JSON: {str(e)}")
        logger.error(f"Response text: {response_text[:500]}")
        return None
    except Exception as e:
        logger.error(f"Groq cleanup failed: {str(e)}")
        return None


# ============================================================================
# MASTER EXTRACTION FUNCTION (Task 15.3)
# ============================================================================

def extract_from_pdf(
    file_path: str,
    document_type: str,
    groq_client: Optional[Groq] = None
) -> Optional[Dict[str, Any]]:
    """
    Master function to extract financial data from PDF with fallback chain.
    
    Extraction chain:
    1. Validate file size and page count
    2. Try pdfplumber extraction (digital PDFs)
    3. If fails, try OCR extraction (scanned PDFs)
    4. If OCR has artifacts, use Groq cleanup
    5. If all fail, return None and log error
    
    Args:
        file_path: Path to PDF file
        document_type: One of VALID_DOCUMENT_TYPES
        groq_client: Optional Groq client instance
        
    Returns:
        dict: Extracted financial data, or None if all methods fail
    """
    # Validate document type
    if document_type not in VALID_DOCUMENT_TYPES:
        logger.error(f"Invalid document type: {document_type}. Must be one of {VALID_DOCUMENT_TYPES}")
        return None
    
    # Validate file exists
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None
    
    logger.info(f"Starting extraction for {document_type} from {file_path}")
    
    # Step 1: Validate file size
    size_valid, size_error = validate_file_size(file_path)
    if not size_valid:
        logger.error(f"File validation failed: {size_error}")
        return None
    
    # Step 2: Validate page count
    page_count, page_error = count_pages(file_path)
    if page_error:
        logger.error(f"Page count validation failed: {page_error}")
        return None
    
    # Step 3: Try pdfplumber extraction
    logger.info("Attempting pdfplumber extraction...")
    text = extract_with_pdfplumber(file_path)
    
    # Step 4: If pdfplumber fails, try OCR
    if not text or len(text.strip()) < 100:
        logger.info("pdfplumber extraction insufficient, trying OCR...")
        text = extract_with_ocr(file_path)
    
    # Step 5: If all extraction fails, return None
    if not text or len(text.strip()) < 50:
        logger.error("All extraction methods failed - no usable text extracted")
        return None
    
    # Step 6: Use Groq to structure the extracted text
    logger.info("Structuring extracted text with Groq...")
    
    try:
        # Initialize Groq client if not provided
        if groq_client is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                logger.error("GROQ_API_KEY not found in environment")
                return None
            groq_client = Groq(api_key=api_key)
        
        # Get extraction prompt for document type
        prompt = enforce_json_output(get_extraction_prompt(document_type, text))
        
        # Call Groq API
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": get_system_message()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # SAFEGUARD 1: Strip Markdown code blocks before parsing JSON
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith("```"):
            response_text = response_text[3:]  # Remove ```
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Remove trailing ```
        
        response_text = response_text.strip()
        
        # Parse JSON
        extracted_data = json.loads(response_text)
        
        logger.info(f"Successfully extracted data from {document_type}")
        return extracted_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Groq response as JSON: {str(e)}")
        logger.error(f"Response text: {response_text[:500]}")
        
        # If JSON parsing fails and we have OCR text, try cleanup
        if text and "tesseract" in str(e).lower():
            logger.info("Attempting Groq cleanup for OCR artifacts...")
            cleaned = cleanup_with_groq(text, document_type, groq_client)
            if cleaned and "extracted_data" in cleaned:
                return cleaned["extracted_data"]
        
        return None
        
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        return None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_all_documents(
    uploaded_files: Dict[str, str],
    groq_client: Optional[Groq] = None
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Extract data from multiple uploaded documents.
    
    Args:
        uploaded_files: Dict mapping document_type to file_path
        groq_client: Optional Groq client instance
        
    Returns:
        dict: Mapping of document_type to extracted data
    """
    results = {}
    
    for doc_type, file_path in uploaded_files.items():
        if doc_type not in VALID_DOCUMENT_TYPES:
            logger.warning(f"Skipping invalid document type: {doc_type}")
            continue
        
        logger.info(f"Processing {doc_type}...")
        extracted = extract_from_pdf(file_path, doc_type, groq_client)
        results[doc_type] = extracted
    
    return results


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    """Test parser with sample PDF"""
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    if len(sys.argv) < 3:
        print("Usage: python parser.py <pdf_path> <document_type>")
        print(f"Valid document types: {', '.join(VALID_DOCUMENT_TYPES)}")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    doc_type = sys.argv[2]
    
    print(f"\n{'='*60}")
    print(f"Testing PDF Parser")
    print(f"{'='*60}")
    print(f"File: {pdf_path}")
    print(f"Type: {doc_type}")
    print(f"{'='*60}\n")
    
    result = extract_from_pdf(pdf_path, doc_type)
    
    if result:
        print("\n✓ Extraction successful!")
        print(json.dumps(result, indent=2))
    else:
        print("\n✗ Extraction failed")
        sys.exit(1)
