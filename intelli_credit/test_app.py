"""
Test script for app.py
Validates Streamlit safeguards and function structure
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_safeguard_comments():
    """Test that all 5 safeguard comments are present"""
    print("\n" + "="*60)
    print("Testing Streamlit Safeguards")
    print("="*60)
    
    # Read app.py source
    with open("app.py", "r") as f:
        source = f.read()
    
    safeguards = [
        "SAFEGUARD 1",
        "SAFEGUARD 2",
        "SAFEGUARD 3",
        "SAFEGUARD 4",
        "SAFEGUARD 5"
    ]
    
    print("\nChecking for safeguard comments:")
    all_present = True
    for i, safeguard in enumerate(safeguards, 1):
        present = safeguard in source
        print(f"   {i}. {safeguard}: {'✓ PRESENT' if present else '✗ MISSING'}")
        if not present:
            all_present = False
    
    print("\n" + "="*60)
    print("Safeguard Tests Complete")
    print("="*60)
    
    return all_present


def test_function_signatures():
    """Test that all required functions exist"""
    print("\n" + "="*60)
    print("Testing Function Signatures")
    print("="*60)
    
    from app import (
        initialize_session_state,
        page_upload,
        page_results,
        main
    )
    
    functions = [
        ("initialize_session_state", initialize_session_state),
        ("page_upload", page_upload),
        ("page_results", page_results),
        ("main", main)
    ]
    
    print("\nChecking function existence:")
    all_exist = True
    for name, func in functions:
        exists = callable(func)
        print(f"   {name}(): {'✓ EXISTS' if exists else '✗ MISSING'}")
        if not exists:
            all_exist = False
    
    print("\n" + "="*60)
    print("Function Signature Tests Complete")
    print("="*60)
    
    return all_exist


def test_session_state_variables():
    """Test that all required session state variables are initialized"""
    print("\n" + "="*60)
    print("Testing Session State Variables")
    print("="*60)
    
    # Read app.py source
    with open("app.py", "r") as f:
        source = f.read()
    
    required_vars = [
        "company_data",
        "score_result",
        "processing_complete",
        "demo_mode",
        "cam_document_path",
        "uploaded_file_paths"
    ]
    
    print("\nChecking session state variables:")
    all_present = True
    for var in required_vars:
        present = f"st.session_state.{var}" in source
        print(f"   {var}: {'✓ PRESENT' if present else '✗ MISSING'}")
        if not present:
            all_present = False
    
    print("\n" + "="*60)
    print("Session State Tests Complete")
    print("="*60)
    
    return all_present


def test_compliance_ui():
    """Test that compliance UI block is present"""
    print("\n" + "="*60)
    print("Testing Compliance UI Block")
    print("="*60)
    
    # Read app.py source
    with open("app.py", "r") as f:
        source = f.read()
    
    compliance_elements = [
        "System Audit & Compliance",
        "CIBIL Commercial CMR Rank",
        "High Risk CMR detected",
        "Auto-routing to Senior Credit Committee"
    ]
    
    print("\nChecking compliance UI elements:")
    all_present = True
    for element in compliance_elements:
        present = element in source
        print(f"   '{element}': {'✓ PRESENT' if present else '✗ MISSING'}")
        if not present:
            all_present = False
    
    print("\n" + "="*60)
    print("Compliance UI Tests Complete")
    print("="*60)
    
    return all_present


def test_ui_components():
    """Test that all required UI components are present"""
    print("\n" + "="*60)
    print("Testing UI Components")
    print("="*60)
    
    # Read app.py source
    with open("app.py", "r") as f:
        source = f.read()
    
    components = {
        "File uploaders": [
            "Balance Sheet",
            "Profit & Loss",
            "Bank Statements",
            "GST Returns",
            "Income Tax Returns",
            "Sanction Letter"
        ],
        "Tabs": [
            "Executive Summary",
            "Five Cs Breakdown",
            "Flags & Warnings",
            "Officer Notes",
            "Research Findings"
        ],
        "Buttons": [
            "Process Application",
            "Download CAM",
            "New Application"
        ],
        "Progress indicators": [
            "st.spinner",
            "st.progress"
        ]
    }
    
    print("\nChecking UI components:")
    for category, items in components.items():
        print(f"\n{category}:")
        for item in items:
            present = item in source
            print(f"   '{item}': {'✓ PRESENT' if present else '✗ MISSING'}")
    
    print("\n" + "="*60)
    print("UI Component Tests Complete")
    print("="*60)


def test_error_handling():
    """Test that error handling is present"""
    print("\n" + "="*60)
    print("Testing Error Handling")
    print("="*60)
    
    # Read app.py source
    with open("app.py", "r") as f:
        source = f.read()
    
    error_patterns = [
        "st.error",
        "st.warning",
        "st.exception",
        "try:",
        "except Exception"
    ]
    
    print("\nChecking error handling patterns:")
    all_present = True
    for pattern in error_patterns:
        present = pattern in source
        print(f"   '{pattern}': {'✓ PRESENT' if present else '✗ MISSING'}")
        if not present:
            all_present = False
    
    print("\n" + "="*60)
    print("Error Handling Tests Complete")
    print("="*60)
    
    return all_present


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" "*20 + "APP.PY TEST SUITE")
    print("="*70)
    
    try:
        results = []
        
        results.append(("Safeguard Comments", test_safeguard_comments()))
        results.append(("Function Signatures", test_function_signatures()))
        results.append(("Session State Variables", test_session_state_variables()))
        results.append(("Compliance UI", test_compliance_ui()))
        test_ui_components()  # Visual check only
        results.append(("Error Handling", test_error_handling()))
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        all_passed = True
        for test_name, passed in results:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{test_name}: {status}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n" + "="*70)
            print(" "*25 + "ALL TESTS PASSED ✓")
            print("="*70 + "\n")
        else:
            print("\n" + "="*70)
            print(" "*25 + "SOME TESTS FAILED ✗")
            print("="*70 + "\n")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
