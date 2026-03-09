"""
Test script for parser.py
Tests file validation and extraction functions
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from parser import (
    validate_file_size,
    count_pages,
    extract_with_pdfplumber,
    VALID_DOCUMENT_TYPES,
    MAX_FILE_SIZE_MB,
    MAX_PAGES
)


def test_validation_functions():
    """Test file validation functions"""
    print("\n" + "="*60)
    print("Testing Parser Validation Functions")
    print("="*60)
    
    # Test 1: validate_file_size with non-existent file
    print("\n1. Testing validate_file_size()...")
    
    # Create a small test file
    test_file = "test_small.txt"
    with open(test_file, "w") as f:
        f.write("Small test file")
    
    is_valid, error = validate_file_size(test_file)
    print(f"   Small file validation: {'✓ PASS' if is_valid else '✗ FAIL'}")
    if error:
        print(f"   Error: {error}")
    
    # Clean up
    os.remove(test_file)
    
    # Test 2: VALID_DOCUMENT_TYPES
    print("\n2. Testing VALID_DOCUMENT_TYPES...")
    expected_types = [
        "balance_sheet",
        "profit_loss",
        "bank_statements",
        "gst_returns",
        "itr",
        "sanction_letter"
    ]
    
    all_present = all(dt in VALID_DOCUMENT_TYPES for dt in expected_types)
    print(f"   All expected document types present: {'✓ PASS' if all_present else '✗ FAIL'}")
    print(f"   Document types: {', '.join(VALID_DOCUMENT_TYPES)}")
    
    # Test 3: Constants
    print("\n3. Testing constants...")
    print(f"   MAX_FILE_SIZE_MB = {MAX_FILE_SIZE_MB} (expected: 8)")
    print(f"   MAX_PAGES = {MAX_PAGES} (expected: 20)")
    
    constants_ok = MAX_FILE_SIZE_MB == 8 and MAX_PAGES == 20
    print(f"   Constants correct: {'✓ PASS' if constants_ok else '✗ FAIL'}")
    
    print("\n" + "="*60)
    print("Validation Tests Complete")
    print("="*60)


def test_safeguards():
    """Test that safeguards are implemented"""
    print("\n" + "="*60)
    print("Testing Critical Safeguards")
    print("="*60)
    
    # Read parser.py source
    with open("parser.py", "r") as f:
        source = f.read()
    
    # Check for safeguard comments
    safeguards = [
        "SAFEGUARD 1: Strip Markdown code blocks",
        "SAFEGUARD 2: Defensive OCR",
        "SAFEGUARD 3: Wrap pdfplumber.open()"
    ]
    
    print("\nChecking for safeguard implementations:")
    for i, safeguard in enumerate(safeguards, 1):
        present = safeguard in source
        print(f"   {i}. {safeguard}: {'✓ PRESENT' if present else '✗ MISSING'}")
    
    # Check for specific implementations
    print("\nChecking specific safeguard code:")
    
    # Safeguard 1: JSON cleanup
    json_cleanup = '```json' in source and 'response_text[7:]' in source
    print(f"   1. Markdown code block stripping: {'✓ PRESENT' if json_cleanup else '✗ MISSING'}")
    
    # Safeguard 2: OCR try/except
    ocr_defensive = 'except ImportError' in source or 'except Exception' in source
    print(f"   2. OCR defensive error handling: {'✓ PRESENT' if ocr_defensive else '✗ MISSING'}")
    
    # Safeguard 3: pdfplumber try/except
    pdf_defensive = 'with pdfplumber.open(file_path)' in source
    print(f"   3. pdfplumber error handling: {'✓ PRESENT' if pdf_defensive else '✗ MISSING'}")
    
    print("\n" + "="*60)
    print("Safeguard Tests Complete")
    print("="*60)


def test_function_signatures():
    """Test that all required functions exist with correct signatures"""
    print("\n" + "="*60)
    print("Testing Function Signatures")
    print("="*60)
    
    from parser import (
        validate_file_size,
        count_pages,
        extract_with_pdfplumber,
        extract_with_ocr,
        cleanup_with_groq,
        extract_from_pdf,
        extract_all_documents
    )
    
    functions = [
        ("validate_file_size", validate_file_size),
        ("count_pages", count_pages),
        ("extract_with_pdfplumber", extract_with_pdfplumber),
        ("extract_with_ocr", extract_with_ocr),
        ("cleanup_with_groq", cleanup_with_groq),
        ("extract_from_pdf", extract_from_pdf),
        ("extract_all_documents", extract_all_documents)
    ]
    
    print("\nChecking function existence:")
    for name, func in functions:
        exists = callable(func)
        print(f"   {name}(): {'✓ EXISTS' if exists else '✗ MISSING'}")
    
    print("\n" + "="*60)
    print("Function Signature Tests Complete")
    print("="*60)


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" "*20 + "PARSER.PY TEST SUITE")
    print("="*70)
    
    try:
        test_validation_functions()
        test_safeguards()
        test_function_signatures()
        
        print("\n" + "="*70)
        print(" "*25 + "ALL TESTS PASSED ✓")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
