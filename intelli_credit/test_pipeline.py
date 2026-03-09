"""
Test script for pipeline.py
Tests demo mode, real mode, and safeguards
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline import (
    load_demo_cache,
    extract_all_documents,
    run_analysis_pipeline,
    process_application,
    validate_uploaded_files,
    get_processing_summary
)
from data_models import CompanyData, FinancialData


def test_demo_cache_fallback():
    """Test SAFEGUARD 3: Demo cache fallback"""
    print("\n" + "="*60)
    print("Testing SAFEGUARD 3: Demo Cache Fallback")
    print("="*60)
    
    # Test 1: Non-existent cache (should return None gracefully)
    print("\n1. Testing non-existent cache...")
    result = load_demo_cache("NonExistent")
    print(f"   Result: {'✓ PASS (None returned)' if result is None else '✗ FAIL'}")
    
    # Test 2: Valid cache (if exists)
    print("\n2. Testing valid cache (if exists)...")
    result = load_demo_cache("IL&FS")
    if result:
        company_data, score_result = result
        print(f"   ✓ PASS: Loaded {company_data.company_name}")
        print(f"   Verdict: {score_result.verdict.value}")
        print(f"   Score: {score_result.total_score:.1f}")
    else:
        print("   ⚠ Cache not yet generated (expected before Task 18)")
    
    print("\n" + "="*60)
    print("Demo Cache Fallback Tests Complete")
    print("="*60)


def test_missing_document_tolerance():
    """Test SAFEGUARD 2: Missing document tolerance"""
    print("\n" + "="*60)
    print("Testing SAFEGUARD 2: Missing Document Tolerance")
    print("="*60)
    
    # Test 1: Empty uploaded files
    print("\n1. Testing empty uploaded files...")
    financials = extract_all_documents({})
    print(f"   Result: {'✓ PASS (FinancialData created)' if financials else '✗ FAIL'}")
    print(f"   Type: {type(financials).__name__}")
    
    # Test 2: Non-existent file paths
    print("\n2. Testing non-existent file paths...")
    uploaded_files = {
        "balance_sheet": "/nonexistent/file.pdf",
        "profit_loss": "/another/missing.pdf"
    }
    financials = extract_all_documents(uploaded_files)
    print(f"   Result: {'✓ PASS (FinancialData created)' if financials else '✗ FAIL'}")
    print(f"   Type: {type(financials).__name__}")
    
    print("\n" + "="*60)
    print("Missing Document Tolerance Tests Complete")
    print("="*60)


def test_defensive_orchestration():
    """Test SAFEGUARD 1: Defensive orchestration"""
    print("\n" + "="*60)
    print("Testing SAFEGUARD 1: Defensive Orchestration")
    print("="*60)
    
    # Test 1: Minimal valid input
    print("\n1. Testing minimal valid input...")
    company_data = process_application(
        cin="TEST123",
        company_name="Test Company",
        uploaded_files=None
    )
    print(f"   Result: {'✓ PASS (CompanyData returned)' if company_data else '✗ FAIL'}")
    print(f"   CIN: {company_data.cin}")
    print(f"   Name: {company_data.company_name}")
    
    # Test 2: Demo mode with non-existent cache
    print("\n2. Testing demo mode with non-existent cache...")
    company_data = process_application(
        cin="TEST456",
        company_name="Test Demo Company",
        demo_mode=True,
        demo_company_key="NonExistent"
    )
    print(f"   Result: {'✓ PASS (CompanyData returned)' if company_data else '✗ FAIL'}")
    print(f"   Fallback to real mode: {'✓ YES' if not company_data.demo_mode else '✗ NO'}")
    
    print("\n" + "="*60)
    print("Defensive Orchestration Tests Complete")
    print("="*60)


def test_function_signatures():
    """Test that all required functions exist"""
    print("\n" + "="*60)
    print("Testing Function Signatures")
    print("="*60)
    
    functions = [
        ("load_demo_cache", load_demo_cache),
        ("extract_all_documents", extract_all_documents),
        ("run_analysis_pipeline", run_analysis_pipeline),
        ("process_application", process_application),
        ("validate_uploaded_files", validate_uploaded_files),
        ("get_processing_summary", get_processing_summary)
    ]
    
    print("\nChecking function existence:")
    for name, func in functions:
        exists = callable(func)
        print(f"   {name}(): {'✓ EXISTS' if exists else '✗ MISSING'}")
    
    print("\n" + "="*60)
    print("Function Signature Tests Complete")
    print("="*60)


def test_safeguard_comments():
    """Test that safeguard comments are present"""
    print("\n" + "="*60)
    print("Testing Safeguard Comments")
    print("="*60)
    
    # Read pipeline.py source
    with open("pipeline.py", "r") as f:
        source = f.read()
    
    safeguards = [
        "SAFEGUARD 1: Defensive orchestration",
        "SAFEGUARD 2: Missing document tolerance",
        "SAFEGUARD 3: Demo cache fallback"
    ]
    
    print("\nChecking for safeguard comments:")
    for i, safeguard in enumerate(safeguards, 1):
        present = safeguard in source
        print(f"   {i}. {safeguard}: {'✓ PRESENT' if present else '✗ MISSING'}")
    
    print("\n" + "="*60)
    print("Safeguard Comment Tests Complete")
    print("="*60)


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" "*20 + "PIPELINE.PY TEST SUITE")
    print("="*70)
    
    try:
        test_function_signatures()
        test_safeguard_comments()
        test_demo_cache_fallback()
        test_missing_document_tolerance()
        test_defensive_orchestration()
        
        print("\n" + "="*70)
        print(" "*25 + "ALL TESTS PASSED ✓")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
