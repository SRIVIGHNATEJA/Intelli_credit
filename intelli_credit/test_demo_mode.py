#!/usr/bin/env python3
"""
Demo Mode Testing Script
Tests all three demo companies and validates results
"""

import json
from pathlib import Path
from dummy_data import load_demo_cache, DEMO_COMPANIES
from pipeline import process_application
from scorer import calculate_five_cs
from report_generator import generate_cam_word

def test_demo_company(company_key: str):
    """Test a single demo company"""
    print(f"\n{'='*60}")
    print(f"TESTING {company_key.upper()} DEMO MODE")
    print(f"{'='*60}")
    
    company_info = DEMO_COMPANIES[company_key]
    expected_verdict = company_info['expected_verdict']
    
    try:
        # Test 1: Load from cache
        print("Test 1: Loading from demo cache...")
        result = load_demo_cache(company_key)
        
        if not result:
            print("❌ Failed to load demo cache")
            return False
        
        company_data, score_result = result
        print(f"✅ Cache loaded successfully")
        print(f"   Company: {company_data.company_name}")
        print(f"   CIN: {company_data.cin}")
        print(f"   Score: {score_result.total_score:.1f}/100")
        print(f"   Verdict: {score_result.verdict.value}")
        
        # Test 2: Verify verdict matches expected
        print("Test 2: Verifying verdict...")
        if score_result.verdict != expected_verdict:
            print(f"❌ Verdict mismatch!")
            print(f"   Expected: {expected_verdict.value}")
            print(f"   Got: {score_result.verdict.value}")
            return False
        
        print(f"✅ Verdict matches expected: {score_result.verdict.value}")
        
        # Test 3: Test pipeline demo mode
        print("Test 3: Testing pipeline demo mode...")
        pipeline_company_data = process_application(
            cin=company_info['cin'],
            company_name=company_info['company_name'],
            promoter_name=None,
            uploaded_files=None,
            demo_mode=True,
            demo_company_key=company_key
        )
        
        if not pipeline_company_data:
            print("❌ Pipeline returned None")
            return False
        
        print(f"✅ Pipeline demo mode works")
        print(f"   Loaded: {pipeline_company_data.company_name}")
        
        # Test 4: Generate CAM document
        print("Test 4: Generating CAM document...")
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        cam_path = output_dir / f"test_cam_{company_key.lower().replace('&', '').replace(' ', '')}.docx"
        
        generated_path = generate_cam_word(company_data, score_result, str(cam_path))
        
        if not Path(generated_path).exists():
            print("❌ CAM document not generated")
            return False
        
        file_size = Path(generated_path).stat().st_size / 1024
        print(f"✅ CAM document generated: {generated_path}")
        print(f"   File size: {file_size:.1f} KB")
        
        # Test 5: Verify flags have source citations
        print("Test 5: Verifying flag sources...")
        flags_without_source = [f for f in score_result.flags if not f.source or f.source.strip() == ""]
        
        if flags_without_source:
            print(f"❌ {len(flags_without_source)} flags missing source citations")
            return False
        
        print(f"✅ All {len(score_result.flags)} flags have source citations")
        
        # Summary
        print(f"\n📊 {company_key} SUMMARY:")
        print(f"   Score: {score_result.total_score:.1f}/100")
        print(f"   Verdict: {score_result.verdict.value}")
        print(f"   Flags: {len(score_result.flags)}")
        print(f"   Interest Rate: {score_result.interest_rate or 'N/A'}")
        print(f"   Loan Amount: ₹{score_result.loan_amount:.1f}Cr" if score_result.loan_amount else "REJECTED")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing {company_key}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test all demo companies"""
    print("🧪 INTELLI-CREDIT DEMO MODE TESTING")
    print("=" * 60)
    
    success_count = 0
    total_companies = len(DEMO_COMPANIES)
    
    # Test each company
    for company_key in DEMO_COMPANIES.keys():
        success = test_demo_company(company_key)
        if success:
            success_count += 1
    
    # Final summary
    print(f"\n{'='*60}")
    print("DEMO MODE TESTING SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successfully tested: {success_count}/{total_companies} companies")
    
    if success_count == total_companies:
        print("🎉 ALL DEMO MODE TESTS PASSED!")
        print("\n✅ Demo mode is fully functional")
        print("✅ All verdicts match expected results")
        print("✅ CAM documents generate successfully")
        print("✅ All flags have source citations")
        
        print("\n🎯 Ready for hackathon demo!")
        print("   1. Run: streamlit run app.py")
        print("   2. Select any demo company")
        print("   3. Click 'Process Application'")
        print("   4. Navigate through all tabs")
        print("   5. Download CAM document")
        
        return True
    else:
        print(f"⚠️  Only {success_count}/{total_companies} tests passed")
        print("   Check errors above and fix issues")
        return False

if __name__ == "__main__":
    main()