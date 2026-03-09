"""
Test GST Analyser Functions
Simple tests to verify analyser.py implementation
"""

from analyser import (
    calculate_gst_gap_percentage,
    check_gst_bank_mismatch,
    detect_circular_trading,
    detect_itc_fraud,
    cross_check_gst_bank
)
from data_models import FinancialData, FlagCategory, Severity


def test_gst_gap_calculation():
    """Test GST gap percentage calculation"""
    print("\n=== Testing GST Gap Calculation ===")
    
    # Test case 1: 35% gap (should trigger -40 flag)
    gap1 = calculate_gst_gap_percentage(gst_turnover=100.0, bank_credits_annual=65.0)
    print(f"Test 1 - 35% gap: {gap1:.1f}% (expected: 35.0%)")
    assert gap1 == 35.0, f"Expected 35.0%, got {gap1}%"
    
    # Test case 2: 20% gap (should trigger -25 flag)
    gap2 = calculate_gst_gap_percentage(gst_turnover=100.0, bank_credits_annual=80.0)
    print(f"Test 2 - 20% gap: {gap2:.1f}% (expected: 20.0%)")
    assert gap2 == 20.0, f"Expected 20.0%, got {gap2}%"
    
    # Test case 3: 10% gap (should trigger -10 flag)
    gap3 = calculate_gst_gap_percentage(gst_turnover=100.0, bank_credits_annual=90.0)
    print(f"Test 3 - 10% gap: {gap3:.1f}% (expected: 10.0%)")
    assert gap3 == 10.0, f"Expected 10.0%, got {gap3}%"
    
    # Test case 4: 5% gap (clean, no flag)
    gap4 = calculate_gst_gap_percentage(gst_turnover=100.0, bank_credits_annual=95.0)
    print(f"Test 4 - 5% gap: {gap4:.1f}% (expected: 5.0%)")
    assert gap4 == 5.0, f"Expected 5.0%, got {gap4}%"
    
    # Test case 5: None values
    gap5 = calculate_gst_gap_percentage(gst_turnover=None, bank_credits_annual=100.0)
    print(f"Test 5 - None GST: {gap5} (expected: None)")
    assert gap5 is None, f"Expected None, got {gap5}"
    
    print("✓ All GST gap calculation tests passed")


def test_gst_bank_mismatch_thresholds():
    """Test GST-Bank mismatch flag generation with CORRECTED thresholds"""
    print("\n=== Testing GST-Bank Mismatch Thresholds ===")
    
    # Test case 1: Gap ≥35% should trigger -40 RED flag
    flag1 = check_gst_bank_mismatch(gst_turnover=100.0, bank_credits_annual=65.0)
    assert flag1 is not None, "Expected flag for 35% gap"
    assert flag1.impact_score == -40.0, f"Expected -40 impact, got {flag1.impact_score}"
    assert flag1.severity == Severity.HIGH, f"Expected HIGH severity, got {flag1.severity}"
    print(f"✓ Test 1 - Gap 35%: {flag1.description} (impact: {flag1.impact_score})")
    
    # Test case 2: Gap ≥20% should trigger -25 RED flag
    flag2 = check_gst_bank_mismatch(gst_turnover=100.0, bank_credits_annual=80.0)
    assert flag2 is not None, "Expected flag for 20% gap"
    assert flag2.impact_score == -25.0, f"Expected -25 impact, got {flag2.impact_score}"
    assert flag2.severity == Severity.HIGH, f"Expected HIGH severity, got {flag2.severity}"
    print(f"✓ Test 2 - Gap 20%: {flag2.description} (impact: {flag2.impact_score})")
    
    # Test case 3: Gap ≥10% should trigger -10 MEDIUM flag
    flag3 = check_gst_bank_mismatch(gst_turnover=100.0, bank_credits_annual=90.0)
    assert flag3 is not None, "Expected flag for 10% gap"
    assert flag3.impact_score == -10.0, f"Expected -10 impact, got {flag3.impact_score}"
    assert flag3.severity == Severity.MEDIUM, f"Expected MEDIUM severity, got {flag3.severity}"
    print(f"✓ Test 3 - Gap 10%: {flag3.description} (impact: {flag3.impact_score})")
    
    # Test case 4: Gap <10% should be clean (no flag)
    flag4 = check_gst_bank_mismatch(gst_turnover=100.0, bank_credits_annual=95.0)
    assert flag4 is None, f"Expected no flag for 5% gap, got {flag4}"
    print(f"✓ Test 4 - Gap 5%: Clean (no flag)")
    
    print("✓ All GST-Bank mismatch threshold tests passed")


def test_itc_fraud_detection():
    """Test ITC fraud detection with CORRECTED thresholds"""
    print("\n=== Testing ITC Fraud Detection ===")
    
    # Test case 1: Gap >15% should trigger -25 RED flag
    flag1 = detect_itc_fraud(gstr_3b_itc=100.0, gstr_2a_itc=80.0)
    assert flag1 is not None, "Expected flag for 20% ITC gap"
    assert flag1.impact_score == -25.0, f"Expected -25 impact, got {flag1.impact_score}"
    assert flag1.severity == Severity.HIGH, f"Expected HIGH severity, got {flag1.severity}"
    print(f"✓ Test 1 - ITC gap 20%: {flag1.description} (impact: {flag1.impact_score})")
    
    # Test case 2: Gap 5-15% should trigger -10 MEDIUM flag
    flag2 = detect_itc_fraud(gstr_3b_itc=100.0, gstr_2a_itc=90.0)
    assert flag2 is not None, "Expected flag for 10% ITC gap"
    assert flag2.impact_score == -10.0, f"Expected -10 impact, got {flag2.impact_score}"
    assert flag2.severity == Severity.MEDIUM, f"Expected MEDIUM severity, got {flag2.severity}"
    print(f"✓ Test 2 - ITC gap 10%: {flag2.description} (impact: {flag2.impact_score})")
    
    # Test case 3: Gap <5% should be clean (no flag)
    flag3 = detect_itc_fraud(gstr_3b_itc=100.0, gstr_2a_itc=97.0)
    assert flag3 is None, f"Expected no flag for 3% ITC gap, got {flag3}"
    print(f"✓ Test 3 - ITC gap 3%: Clean (no flag)")
    
    # Test case 4: None values should return None
    flag4 = detect_itc_fraud(gstr_3b_itc=None, gstr_2a_itc=100.0)
    assert flag4 is None, f"Expected None for missing data, got {flag4}"
    print(f"✓ Test 4 - Missing data: Clean (no flag)")
    
    print("✓ All ITC fraud detection tests passed")


def test_circular_trading_detection():
    """Test circular trading detection"""
    print("\n=== Testing Circular Trading Detection ===")
    
    # Test case 1: >5 cycles should trigger HIGH flag
    bank_data_high = {
        "transactions": [
            {"date": "2023-01-15", "type": "credit", "amount": 100.0},
            {"date": "2023-01-15", "type": "debit", "amount": 100.0},
            {"date": "2023-01-20", "type": "credit", "amount": 200.0},
            {"date": "2023-01-20", "type": "debit", "amount": 200.0},
            {"date": "2023-01-25", "type": "credit", "amount": 150.0},
            {"date": "2023-01-25", "type": "debit", "amount": 150.0},
            {"date": "2023-02-01", "type": "credit", "amount": 300.0},
            {"date": "2023-02-01", "type": "debit", "amount": 300.0},
            {"date": "2023-02-05", "type": "credit", "amount": 250.0},
            {"date": "2023-02-05", "type": "debit", "amount": 250.0},
            {"date": "2023-02-10", "type": "credit", "amount": 180.0},
            {"date": "2023-02-10", "type": "debit", "amount": 180.0},
        ]
    }
    flag1 = detect_circular_trading(gst_data=None, bank_data=bank_data_high)
    assert flag1 is not None, "Expected flag for >5 cycles"
    assert flag1.impact_score == -25.0, f"Expected -25 impact, got {flag1.impact_score}"
    assert flag1.severity == Severity.HIGH, f"Expected HIGH severity, got {flag1.severity}"
    print(f"✓ Test 1 - 6 cycles: {flag1.description} (impact: {flag1.impact_score})")
    
    # Test case 2: 3-5 cycles should trigger MEDIUM flag
    bank_data_medium = {
        "transactions": [
            {"date": "2023-01-15", "type": "credit", "amount": 100.0},
            {"date": "2023-01-15", "type": "debit", "amount": 100.0},
            {"date": "2023-01-20", "type": "credit", "amount": 200.0},
            {"date": "2023-01-20", "type": "debit", "amount": 200.0},
            {"date": "2023-01-25", "type": "credit", "amount": 150.0},
            {"date": "2023-01-25", "type": "debit", "amount": 150.0},
        ]
    }
    flag2 = detect_circular_trading(gst_data=None, bank_data=bank_data_medium)
    assert flag2 is not None, "Expected flag for 3 cycles"
    assert flag2.impact_score == -10.0, f"Expected -10 impact, got {flag2.impact_score}"
    assert flag2.severity == Severity.MEDIUM, f"Expected MEDIUM severity, got {flag2.severity}"
    print(f"✓ Test 2 - 3 cycles: {flag2.description} (impact: {flag2.impact_score})")
    
    # Test case 3: <3 cycles should be clean
    bank_data_clean = {
        "transactions": [
            {"date": "2023-01-15", "type": "credit", "amount": 100.0},
            {"date": "2023-01-15", "type": "debit", "amount": 100.0},
        ]
    }
    flag3 = detect_circular_trading(gst_data=None, bank_data=bank_data_clean)
    assert flag3 is None, f"Expected no flag for 1 cycle, got {flag3}"
    print(f"✓ Test 3 - 1 cycle: Clean (no flag)")
    
    print("✓ All circular trading detection tests passed")


def test_cross_check_master_function():
    """Test master cross_check_gst_bank function"""
    print("\n=== Testing Master Cross-Check Function ===")
    
    # Create test financial data with multiple issues
    financials = FinancialData(
        gst_turnover=100.0,
        bank_credits_annual=60.0,  # 40% gap - should trigger -40 flag
        gstr_3b_itc=100.0,
        gstr_2a_itc=75.0  # 25% gap - should trigger -25 flag
    )
    
    # Create bank data with circular trading
    bank_data = {
        "transactions": [
            {"date": "2023-01-15", "type": "credit", "amount": 100.0},
            {"date": "2023-01-15", "type": "debit", "amount": 100.0},
            {"date": "2023-01-20", "type": "credit", "amount": 200.0},
            {"date": "2023-01-20", "type": "debit", "amount": 200.0},
            {"date": "2023-01-25", "type": "credit", "amount": 150.0},
            {"date": "2023-01-25", "type": "debit", "amount": 150.0},
            {"date": "2023-02-01", "type": "credit", "amount": 300.0},
            {"date": "2023-02-01", "type": "debit", "amount": 300.0},
            {"date": "2023-02-05", "type": "credit", "amount": 250.0},
            {"date": "2023-02-05", "type": "debit", "amount": 250.0},
            {"date": "2023-02-10", "type": "credit", "amount": 180.0},
            {"date": "2023-02-10", "type": "debit", "amount": 180.0},
        ]
    }
    
    # Run master cross-check
    flags = cross_check_gst_bank(financials, gst_data=None, bank_data=bank_data)
    
    # Should have 3 flags: GST mismatch, circular trading, ITC fraud
    assert len(flags) == 3, f"Expected 3 flags, got {len(flags)}"
    
    # Verify each flag has required fields
    for i, flag in enumerate(flags, 1):
        assert flag.category == FlagCategory.GST_FRAUD, f"Flag {i}: Expected GST_FRAUD category"
        assert flag.source is not None, f"Flag {i}: Missing source"
        assert flag.description is not None, f"Flag {i}: Missing description"
        assert flag.impact_score < 0, f"Flag {i}: Expected negative impact"
        print(f"✓ Flag {i}: {flag.description} (impact: {flag.impact_score}, source: {flag.source})")
    
    # Verify total impact
    total_impact = sum(flag.impact_score for flag in flags)
    print(f"✓ Total impact from all flags: {total_impact}")
    assert total_impact == -90.0, f"Expected -90 total impact, got {total_impact}"
    
    print("✓ Master cross-check function test passed")


def run_all_tests():
    """Run all analyser tests"""
    print("\n" + "="*60)
    print("RUNNING GST ANALYSER TESTS")
    print("="*60)
    
    try:
        test_gst_gap_calculation()
        test_gst_bank_mismatch_thresholds()
        test_itc_fraud_detection()
        test_circular_trading_detection()
        test_cross_check_master_function()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
