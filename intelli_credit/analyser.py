"""
GST Analyser - Cross-check GST returns against bank statements
Detects circular trading, ITC fraud, and turnover mismatches
"""

from typing import List, Optional, Dict, Any
from data_models import (
    FlagItem, FlagCategory, Severity, FinancialData, create_flag
)


# ============================================================================
# GST-BANK CROSS-CHECK LOGIC (Task 11.1)
# ============================================================================

def calculate_gst_gap_percentage(
    gst_turnover: Optional[float],
    bank_credits_annual: Optional[float]
) -> Optional[float]:
    """
    Calculate percentage gap between GST reported turnover and bank inflows.
    
    Formula: gap = (gst_turnover - bank_credits_annual) / gst_turnover * 100
    
    Args:
        gst_turnover: Annual turnover reported in GST returns (₹ Crores)
        bank_credits_annual: Annual bank credit inflows (₹ Crores)
    
    Returns:
        Gap percentage (positive = GST higher than bank, negative = bank higher than GST)
        None if either value is missing
    
    Source: SCORER_CORRECTIONS.md - GST Cross-Check Thresholds
    """
    if gst_turnover is None or bank_credits_annual is None:
        return None
    
    if gst_turnover == 0:
        return None
    
    gap = ((gst_turnover - bank_credits_annual) / gst_turnover) * 100
    return gap


def check_gst_bank_mismatch(
    gst_turnover: Optional[float],
    bank_credits_annual: Optional[float]
) -> Optional[FlagItem]:
    """
    Check for GST-Bank turnover mismatch and apply CORRECTED thresholds.
    
    CORRECTED Thresholds (from SCORER_CORRECTIONS.md):
    - Gap ≥35%: -40 impact, RED severity (Circular trading signal)
    - Gap ≥20%: -25 impact, RED severity (Revenue inflation risk)
    - Gap ≥10%: -10 impact, MEDIUM severity (GST/Bank discrepancy)
    - Gap <10%: Clean (no flag)
    
    Args:
        gst_turnover: Annual turnover from GST returns (₹ Crores)
        bank_credits_annual: Annual bank credits (₹ Crores)
    
    Returns:
        FlagItem if mismatch detected, None otherwise
    
    Validates: Requirements 8.1, 8.2
    """
    gap = calculate_gst_gap_percentage(gst_turnover, bank_credits_annual)
    
    if gap is None:
        return None
    
    # Apply CORRECTED thresholds from SCORER_CORRECTIONS.md
    if gap >= 35.0:
        return create_flag(
            category=FlagCategory.GST_FRAUD,
            severity=Severity.HIGH,
            description=f"GST turnover exceeds bank credits by {gap:.1f}% - Circular trading signal",
            source="GST Returns vs Bank Statements",
            impact=-40.0
        )
    elif gap >= 20.0:
        return create_flag(
            category=FlagCategory.GST_FRAUD,
            severity=Severity.HIGH,
            description=f"GST turnover exceeds bank credits by {gap:.1f}% - Revenue inflation risk",
            source="GST Returns vs Bank Statements",
            impact=-25.0
        )
    elif gap >= 10.0:
        return create_flag(
            category=FlagCategory.GST_FRAUD,
            severity=Severity.MEDIUM,
            description=f"GST turnover exceeds bank credits by {gap:.1f}% - GST/Bank discrepancy",
            source="GST Returns vs Bank Statements",
            impact=-10.0
        )
    
    # Gap < 10% is clean
    return None


# ============================================================================
# CIRCULAR TRADING DETECTION (Task 11.2)
# ============================================================================

def detect_circular_trading(
    gst_data: Optional[Dict[str, Any]],
    bank_data: Optional[Dict[str, Any]]
) -> Optional[FlagItem]:
    """
    Detect circular trading patterns by analyzing same-day credit-debit cycles.
    
    Circular trading indicators:
    - Same-day credit followed by debit of similar amount (within 5% tolerance)
    - Multiple such cycles in a short period
    - Vendor-customer overlap
    
    Thresholds:
    - >5 cycles: HIGH severity, impact -25
    - 3-5 cycles: MEDIUM severity, impact -10
    - <3 cycles: Clean (no flag)
    
    Args:
        gst_data: GST returns data (may contain vendor/customer lists)
        bank_data: Bank statement data with transactions
    
    Returns:
        FlagItem if circular trading detected, None otherwise
    
    Validates: Requirements 8.4, 8.5, 8.6
    """
    if not bank_data or not isinstance(bank_data, dict):
        return None
    
    # Extract transactions from bank data
    transactions = bank_data.get("transactions", [])
    if not transactions:
        return None
    
    # Count same-day credit-debit cycles
    cycle_count = 0
    tolerance = 0.05  # 5% tolerance for transaction charges
    
    # Group transactions by date
    date_groups: Dict[str, List[Dict]] = {}
    for txn in transactions:
        if not isinstance(txn, dict):
            continue
        
        date = txn.get("date")
        if not date:
            continue
        
        if date not in date_groups:
            date_groups[date] = []
        date_groups[date].append(txn)
    
    # Check each date for credit-debit cycles
    for date, txns in date_groups.items():
        credits = [t for t in txns if t.get("type") == "credit"]
        debits = [t for t in txns if t.get("type") == "debit"]
        
        # Check for matching credit-debit pairs
        for credit in credits:
            credit_amt = credit.get("amount", 0)
            if credit_amt == 0:
                continue
            
            for debit in debits:
                debit_amt = debit.get("amount", 0)
                if debit_amt == 0:
                    continue
                
                # Check if amounts match within tolerance
                ratio = abs(debit_amt - credit_amt) / credit_amt
                if ratio <= tolerance:
                    cycle_count += 1
                    break  # Count each credit only once
    
    # Apply thresholds
    if cycle_count > 5:
        return create_flag(
            category=FlagCategory.GST_FRAUD,
            severity=Severity.HIGH,
            description=f"Detected {cycle_count} same-day credit-debit cycles - Circular trading pattern",
            source="Bank Statement Transaction Analysis",
            impact=-25.0
        )
    elif cycle_count >= 3:
        return create_flag(
            category=FlagCategory.GST_FRAUD,
            severity=Severity.MEDIUM,
            description=f"Detected {cycle_count} same-day credit-debit cycles - Potential circular trading",
            source="Bank Statement Transaction Analysis",
            impact=-10.0
        )
    
    # <3 cycles is clean
    return None


# ============================================================================
# ITC FRAUD DETECTION (Task 11.3)
# ============================================================================

def detect_itc_fraud(
    gstr_3b_itc: Optional[float],
    gstr_2a_itc: Optional[float]
) -> Optional[FlagItem]:
    """
    Detect Input Tax Credit (ITC) fraud by comparing GSTR-3B vs GSTR-2A.
    
    GSTR-3B: ITC claimed by the company
    GSTR-2A: ITC available based on supplier filings
    
    CORRECTED Thresholds (from SCORER_CORRECTIONS.md):
    - Gap >15%: -25 impact, RED severity (ITC fraud signal)
    - Gap 5-15%: -10 impact, MEDIUM severity (ITC discrepancy)
    - Gap <5%: Clean (no flag)
    
    Formula: gap = (gstr_3b_itc - gstr_2a_itc) / gstr_3b_itc * 100
    
    Args:
        gstr_3b_itc: ITC claimed in GSTR-3B (₹ Crores)
        gstr_2a_itc: ITC available in GSTR-2A (₹ Crores)
    
    Returns:
        FlagItem if ITC fraud detected, None otherwise
    
    Validates: Requirement 8.3
    """
    if gstr_3b_itc is None or gstr_2a_itc is None:
        return None
    
    if gstr_3b_itc == 0:
        return None
    
    # Calculate ITC gap percentage
    gap = ((gstr_3b_itc - gstr_2a_itc) / gstr_3b_itc) * 100
    
    # Apply CORRECTED thresholds from SCORER_CORRECTIONS.md
    if gap > 15.0:
        return create_flag(
            category=FlagCategory.GST_FRAUD,
            severity=Severity.HIGH,
            description=f"ITC claimed exceeds available ITC by {gap:.1f}% - ITC fraud signal",
            source="GSTR-3B vs GSTR-2A",
            impact=-25.0
        )
    elif gap >= 5.0:
        return create_flag(
            category=FlagCategory.GST_FRAUD,
            severity=Severity.MEDIUM,
            description=f"ITC claimed exceeds available ITC by {gap:.1f}% - ITC discrepancy",
            source="GSTR-3B vs GSTR-2A",
            impact=-10.0
        )
    
    # Gap < 5% is clean
    return None


# ============================================================================
# MASTER CROSS-CHECK FUNCTION (Task 11.4)
# ============================================================================

def cross_check_gst_bank(
    financials: FinancialData,
    gst_data: Optional[Dict[str, Any]] = None,
    bank_data: Optional[Dict[str, Any]] = None
) -> List[FlagItem]:
    """
    Master function to perform all GST-Bank cross-checks.
    
    Runs all detection functions:
    1. GST-Bank turnover mismatch (calculate_gst_gap_percentage)
    2. Circular trading detection (detect_circular_trading)
    3. ITC fraud detection (detect_itc_fraud)
    
    Args:
        financials: FinancialData object with GST and bank data
        gst_data: Optional detailed GST data dictionary
        bank_data: Optional detailed bank statement dictionary
    
    Returns:
        List of FlagItem objects with all detected issues
        Each flag includes source citation for auditability
    
    Validates: Requirements 8.7, 8.8
    """
    flags: List[FlagItem] = []
    
    # Check 1: GST-Bank turnover mismatch
    mismatch_flag = check_gst_bank_mismatch(
        gst_turnover=financials.gst_turnover,
        bank_credits_annual=financials.bank_credits_annual
    )
    if mismatch_flag:
        flags.append(mismatch_flag)
    
    # Check 2: Circular trading detection
    circular_flag = detect_circular_trading(gst_data, bank_data)
    if circular_flag:
        flags.append(circular_flag)
    
    # Check 3: ITC fraud detection
    itc_flag = detect_itc_fraud(
        gstr_3b_itc=financials.gstr_3b_itc,
        gstr_2a_itc=financials.gstr_2a_itc
    )
    if itc_flag:
        flags.append(itc_flag)
    
    return flags


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_currency(amount: Optional[float], unit: str = "Cr") -> str:
    """
    Format currency amount for display.
    
    Args:
        amount: Amount in Crores
        unit: Unit suffix (default "Cr")
    
    Returns:
        Formatted string like "₹123.45 Cr"
    """
    if amount is None:
        return "N/A"
    return f"₹{amount:.2f} {unit}"


def get_gst_summary(financials: FinancialData) -> Dict[str, Any]:
    """
    Generate summary of GST data for reporting.
    
    Args:
        financials: FinancialData object
    
    Returns:
        Dictionary with GST summary metrics
    """
    gap = calculate_gst_gap_percentage(
        financials.gst_turnover,
        financials.bank_credits_annual
    )
    
    return {
        "gst_turnover": format_currency(financials.gst_turnover),
        "bank_credits": format_currency(financials.bank_credits_annual),
        "gap_percentage": f"{gap:.1f}%" if gap is not None else "N/A",
        "gstr_3b_itc": format_currency(financials.gstr_3b_itc),
        "gstr_2a_itc": format_currency(financials.gstr_2a_itc),
    }
