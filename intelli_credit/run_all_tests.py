#!/usr/bin/env python3
"""
Master Test Runner - Run all tests and validations in sequence
Execute this single file to validate the entire Intelli-Credit system
"""

import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import os


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f" {text}")
    print("="*70 + "\n")


def run_test(test_file, description):
    """Run a test file and report results"""
    print(f"Running: {description}...")
    print(f"File: {test_file}")
    print("-" * 70)
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print(f"✅ {description} PASSED\n")
            return True
        else:
            print(f"❌ {description} FAILED")
            if result.stderr:
                print("Error output:")
                print(result.stderr)
            print()
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ {description} TIMEOUT (>30s)\n")
        return False
    except Exception as e:
        print(f"❌ {description} ERROR: {e}\n")
        return False


def check_environment():
    """Check environment setup"""
    print_header("STEP 1: Environment Check")
    
    # Load .env
    load_dotenv()
    
    # Check API keys
    groq_key = os.getenv("GROQ_API_KEY")
    serper_key = os.getenv("SERPER_API_KEY")
    news_key = os.getenv("NEWSAPI_KEY")
    
    print("API Key Status:")
    print(f"  GROQ_API_KEY: {'✅ SET' if groq_key else '❌ MISSING (REQUIRED)'}")
    print(f"  SERPER_API_KEY: {'✅ SET' if serper_key else '⚠️  NOT SET (Optional)'}")
    print(f"  NEWSAPI_KEY: {'✅ SET' if news_key else '⚠️  NOT SET (Optional)'}")
    
    if not groq_key:
        print("\n❌ CRITICAL: GROQ_API_KEY is required!")
        print("   Please set it in .env file and run again.")
        return False
    
    # Check virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"\nVirtual Environment: {'✅ ACTIVE' if in_venv else '⚠️  NOT ACTIVE (recommended)'}")
    
    # Check required directories
    print("\nDirectory Structure:")
    dirs = ['uploads', 'output', 'demo_cache']
    for d in dirs:
        exists = Path(d).exists()
        print(f"  {d}/: {'✅ EXISTS' if exists else '⚠️  WILL BE CREATED'}")
        if not exists:
            Path(d).mkdir(exist_ok=True)
            print(f"    Created {d}/")
    
    print("\n✅ Environment check complete\n")
    return True


def run_all_tests():
    """Run all test files in sequence"""
    print_header("STEP 2: Component Tests")
    
    tests = [
        ("test_parser.py", "Parser (PDF extraction)"),
        ("test_pipeline.py", "Pipeline (orchestration)"),
        ("test_app.py", "Streamlit UI (app structure)"),
    ]
    
    results = []
    
    for test_file, description in tests:
        if Path(test_file).exists():
            passed = run_test(test_file, description)
            results.append((description, passed))
        else:
            print(f"⚠️  {test_file} not found, skipping...\n")
            results.append((description, None))
    
    return results


def run_validation_tests():
    """Run validation tests that require API calls"""
    print_header("STEP 3: Validation Tests (with API calls)")
    
    validations = [
        ("scorer.py", "Scorer validation (IL&FS test data)"),
        ("test_report_generator.py", "Report generator (creates CAM document)"),
    ]
    
    results = []
    
    for test_file, description in validations:
        if Path(test_file).exists():
            passed = run_test(test_file, description)
            results.append((description, passed))
        else:
            print(f"⚠️  {test_file} not found, skipping...\n")
            results.append((description, None))
    
    return results


def check_generated_files():
    """Check that expected files were generated"""
    print_header("STEP 4: Generated Files Check")
    
    expected_files = [
        ("test_cam_ilfs.docx", "IL&FS CAM document"),
        ("test_cam_ilfs_complete.docx", "IL&FS complete CAM document"),
    ]
    
    print("Checking generated files:")
    for filename, description in expected_files:
        exists = Path(filename).exists()
        if exists:
            size = Path(filename).stat().st_size / 1024  # KB
            print(f"  ✅ {filename}: {size:.1f} KB - {description}")
        else:
            print(f"  ⚠️  {filename}: Not found - {description}")
    
    print()


def print_summary(component_results, validation_results):
    """Print final summary"""
    print_header("FINAL SUMMARY")
    
    print("Component Tests:")
    for description, passed in component_results:
        if passed is None:
            status = "⚠️  SKIPPED"
        elif passed:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"  {status} - {description}")
    
    print("\nValidation Tests:")
    for description, passed in validation_results:
        if passed is None:
            status = "⚠️  SKIPPED"
        elif passed:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"  {status} - {description}")
    
    # Overall status
    all_component_passed = all(r[1] for r in component_results if r[1] is not None)
    all_validation_passed = all(r[1] for r in validation_results if r[1] is not None)
    
    print("\n" + "="*70)
    if all_component_passed and all_validation_passed:
        print(" "*20 + "🎉 ALL TESTS PASSED! 🎉")
        print("="*70)
        print("\n✅ System is ready to use!")
        print("\nNext steps:")
        print("  1. Run: streamlit run app.py")
        print("  2. Open browser at http://localhost:8501")
        print("  3. Try demo mode (IL&FS, TCS, or Byju's)")
        print("  4. Or upload your own PDFs for real mode")
        print("\nNote: Demo cache will be generated in Task 18")
    else:
        print(" "*20 + "⚠️  SOME TESTS FAILED")
        print("="*70)
        print("\nPlease review the errors above and fix before proceeding.")
    
    print()


def main():
    """Main test runner"""
    print("\n" + "="*70)
    print(" "*15 + "INTELLI-CREDIT MASTER TEST RUNNER")
    print("="*70)
    print("\nThis script will validate the entire system:")
    print("  • Environment setup")
    print("  • Component tests (parser, pipeline, app)")
    print("  • Validation tests (scorer, report generator)")
    print("  • Generated files check")
    print()
    
    # Step 1: Environment check
    if not check_environment():
        print("\n❌ Environment check failed. Please fix and run again.")
        sys.exit(1)
    
    # Step 2: Component tests
    component_results = run_all_tests()
    
    # Step 3: Validation tests
    validation_results = run_validation_tests()
    
    # Step 4: Check generated files
    check_generated_files()
    
    # Step 5: Summary
    print_summary(component_results, validation_results)
    
    # Exit code
    all_passed = all(r[1] for r in component_results + validation_results if r[1] is not None)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
