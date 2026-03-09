"""
Five Cs Scorer - Deterministic credit scoring using pure Python math
NO ML/LLM - all decisions are traceable and explainable

CRITICAL: Uses exact thresholds from SCORER_CORRECTIONS.md
"""

from typing import Tuple, List, Optional, Dict
import os
from groq import Groq

from data_models import (
    CompanyData, FinancialData, ResearchResult, ScoreResult,
    FlagItem, FlagCategory, Severity, Verdict, create_flag
)
from prompts import get_sector_outlook_prompt


# ============================================================================
# SECTOR NPA RATES (from SCORER_CORRECTIONS.md)
# ============================================================================

SECTOR_NPA = {
    "Infrastructure Finance": 18.4,
    "Infrastructure": 18.4,
    "IT Services": 0.8,
    "IT": 0.8,
    "Education Technology": 12.3,
    "Education": 12.3,
    "Manufacturing": 4.2,
    "FMCG": 1.8,
    "Real Estate": 9.6,
    "RealEstate": 9.6,
    "Telecom": 6.1,
    "Banking": 3.9,
    "NBFC": 7.2,
    "Pharma": 2.1,
    "Retail": 3.4,
    "Construction": 8.8
}


# ============================================================================
# TASK 7.1: UTILITY FUNCTIONS
# ============================================================================

def apply_floor_ceiling(score: float, floor: float = 10.0, ceiling: float = 100.0) -> float:
    """
    Enforce score bounds.
    
    Args:
        score: Raw score
        floor: Minimum score (default 10)
        ceiling: Maximum score (default 100)
        
    Returns:
        float: Bounded score
    """
    return max(floor, min(ceiling, score))


def generate_reasoning(
    total_score: float,
    character_score: float,
    capacity_score: float,
    capital_score: float,
    collateral_score: float,
    conditions_score: float,
    flags: List[FlagItem]
) -> str:
    """
    Generate human-readable reasoning for the credit decision.
    
    Args:
        total_score: Final weighted score
        character_score: CHARACTER score
        capacity_score: CAPACITY score
        capital_score: CAPITAL score
        collateral_score: COLLATERAL score
        conditions_score: CONDITIONS score
        flags: All flags generated during scoring
        
    Returns:
        str: Reasoning text
    """
    # Sort flags by severity and impact
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "GREEN": 3}
    sorted_flags = sorted(
        flags,
        key=lambda f: (severity_order.get(f.severity.value, 4), abs(f.impact_score)),
        reverse=True
    )
    
    # Build reasoning
    lines = [
        f"Total Credit Score: {total_score:.1f}/100",
        "",
        "Component Scores:",
        f"  CHARACTER (25%): {character_score:.1f}/100",
        f"  CAPACITY (30%): {capacity_score:.1f}/100",
        f"  CAPITAL (20%): {capital_score:.1f}/100",
        f"  COLLATERAL (15%): {collateral_score:.1f}/100",
        f"  CONDITIONS (10%): {conditions_score:.1f}/100",
        "",
        "Key Findings:"
    ]
    
    # Add top 5 flags
    for flag in sorted_flags[:5]:
        lines.append(f"  [{flag.severity.value}] {flag.description} (Source: {flag.source})")
    
    return "\n".join(lines)


# ============================================================================
# TASK 7.2: CHARACTER SCORE CALCULATION
# ============================================================================

def calculate_character_score(company_data: CompanyData) -> Tuple[float, List[FlagItem]]:
    """
    Calculate CHARACTER score (25% weight).
    Base: 100 | Floor: 10
    
    Assesses integrity, management quality, legal issues, audit opinions.
    
    Args:
        company_data: Complete company data
        
    Returns:
        Tuple of (score, flags)
    """
    score = 100.0
    flags = []
    financials = company_data.financials
    
    if not financials:
        return 50.0, [create_flag(
            FlagCategory.CHARACTER,
            Severity.MEDIUM,
            "No financial data available",
            "System",
            -50.0
        )]
    
    # NCLT/DRT civil cases: -10 per case
    if financials.nclt_cases > 0:
        deduction = financials.nclt_cases * 10
        score -= deduction
        flags.append(create_flag(
            FlagCategory.CHARACTER,
            Severity.MEDIUM,
            f"{financials.nclt_cases} NCLT case(s) found",
            "Legal Records",
            -deduction
        ))
    
    if financials.drt_cases > 0:
        deduction = financials.drt_cases * 10
        score -= deduction
        flags.append(create_flag(
            FlagCategory.CHARACTER,
            Severity.MEDIUM,
            f"{financials.drt_cases} DRT case(s) found",
            "Legal Records",
            -deduction
        ))
    
    # Criminal cases: -25
    if financials.criminal_cases > 0:
        score -= 25
        flags.append(create_flag(
            FlagCategory.CHARACTER,
            Severity.HIGH,
            f"{financials.criminal_cases} criminal case(s) found",
            "Legal Records",
            -25.0
        ))
    
    # SEBI/ED actions: -20
    if financials.sebi_actions > 0:
        score -= 20
        flags.append(create_flag(
            FlagCategory.CHARACTER,
            Severity.HIGH,
            f"SEBI enforcement action(s): {financials.sebi_actions}",
            "Regulatory Records",
            -20.0
        ))
    
    if financials.ed_actions > 0:
        score -= 20
        flags.append(create_flag(
            FlagCategory.CHARACTER,
            Severity.HIGH,
            f"ED enforcement action(s): {financials.ed_actions}",
            "Regulatory Records",
            -20.0
        ))
    
    # MCA strike-off: -30
    if financials.mca_status and "strike" in financials.mca_status.lower():
        score -= 30
        flags.append(create_flag(
            FlagCategory.CHARACTER,
            Severity.HIGH,
            f"MCA status: {financials.mca_status}",
            "MCA Portal",
            -30.0
        ))
    
    # DIN deactivated: -15
    if financials.din_deactivated:
        score -= 15
        flags.append(create_flag(
            FlagCategory.CHARACTER,
            Severity.MEDIUM,
            "Director DIN deactivated",
            "MCA Portal",
            -15.0
        ))
    
    # Rating downgrade
    if financials.rating_downgrade_months is not None:
        if financials.rating_downgrade_months < 12:
            score -= 15
            flags.append(create_flag(
                FlagCategory.CHARACTER,
                Severity.MEDIUM,
                f"Rating downgraded {financials.rating_downgrade_months} months ago",
                "Credit Rating Agency",
                -15.0
            ))
        elif financials.rating_downgrade_months <= 24:
            score -= 8
            flags.append(create_flag(
                FlagCategory.CHARACTER,
                Severity.LOW,
                f"Rating downgraded {financials.rating_downgrade_months} months ago",
                "Credit Rating Agency",
                -8.0
            ))
    
    # Going concern flag: -20
    if financials.going_concern_flag:
        score -= 20
        flags.append(create_flag(
            FlagCategory.CHARACTER,
            Severity.HIGH,
            "Going concern flag raised by auditor",
            "Audit Report",
            -20.0
        ))
    
    # Audit opinion
    if financials.audit_opinion:
        opinion = financials.audit_opinion.lower()
        if "qualified" in opinion:
            score -= 20
            flags.append(create_flag(
                FlagCategory.CHARACTER,
                Severity.MEDIUM,
                "Qualified audit opinion",
                "Audit Report",
                -20.0
            ))
        elif "adverse" in opinion:
            score -= 25
            flags.append(create_flag(
                FlagCategory.CHARACTER,
                Severity.HIGH,
                "Adverse audit opinion",
                "Audit Report",
                -25.0
            ))
        elif "disclaimer" in opinion:
            score -= 25
            flags.append(create_flag(
                FlagCategory.CHARACTER,
                Severity.HIGH,
                "Disclaimer of opinion",
                "Audit Report",
                -25.0
            ))
        elif "clean" in opinion or "unqualified" in opinion:
            score += 5
            flags.append(create_flag(
                FlagCategory.CHARACTER,
                Severity.GREEN,
                "Clean audit opinion",
                "Audit Report",
                5.0
            ))
    
    # Promoter pledge percentage
    if financials.promoter_pledge_pct is not None:
        if financials.promoter_pledge_pct > 50:
            score -= 40
            flags.append(create_flag(
                FlagCategory.CHARACTER,
                Severity.HIGH,
                f"High promoter pledge: {financials.promoter_pledge_pct:.1f}%",
                "Stock Exchange Filing",
                -40.0
            ))
        elif financials.promoter_pledge_pct > 25:
            score -= 25
            flags.append(create_flag(
                FlagCategory.CHARACTER,
                Severity.MEDIUM,
                f"Moderate promoter pledge: {financials.promoter_pledge_pct:.1f}%",
                "Stock Exchange Filing",
                -25.0
            ))
        elif financials.promoter_pledge_pct > 10:
            score -= 10
            flags.append(create_flag(
                FlagCategory.CHARACTER,
                Severity.LOW,
                f"Low promoter pledge: {financials.promoter_pledge_pct:.1f}%",
                "Stock Exchange Filing",
                -10.0
            ))
    
    # Apply floor
    score = apply_floor_ceiling(score, floor=10.0)
    
    return score, flags


# ============================================================================
# TASK 7.3: CAPACITY SCORE CALCULATION
# ============================================================================

def calculate_capacity_score(financials: FinancialData, gst_flags: List[FlagItem]) -> Tuple[float, List[FlagItem]]:
    """
    Calculate CAPACITY score (30% weight).
    Base: 100 | Floor: 10
    
    Assesses ability to repay based on cash flow, DSCR, revenue growth, banking conduct.
    
    Args:
        financials: Financial data
        gst_flags: GST cross-check flags (for circular trading impact)
        
    Returns:
        Tuple of (score, flags)
    """
    score = 100.0
    flags = []
    
    if not financials:
        return 50.0, [create_flag(
            FlagCategory.CAPACITY,
            Severity.MEDIUM,
            "No financial data available",
            "System",
            -50.0
        )]
    
    # DSCR (5 bands) - CRITICAL
    if financials.dscr is not None:
        if financials.dscr >= 2.0:
            pass  # No deduction
        elif financials.dscr >= 1.5:
            score -= 5
            flags.append(create_flag(
                FlagCategory.CAPACITY,
                Severity.LOW,
                f"DSCR {financials.dscr:.2f} (adequate but not strong)",
                "Financial Statements",
                -5.0
            ))
        elif financials.dscr >= 1.25:
            score -= 15
            flags.append(create_flag(
                FlagCategory.CAPACITY,
                Severity.MEDIUM,
                f"DSCR {financials.dscr:.2f} (below comfort level)",
                "Financial Statements",
                -15.0
            ))
        elif financials.dscr >= 1.1:
            score -= 25
            flags.append(create_flag(
                FlagCategory.CAPACITY,
                Severity.HIGH,
                f"DSCR {financials.dscr:.2f} (marginal coverage)",
                "Financial Statements",
                -25.0
            ))
        else:  # < 1.1
            score -= 40
            flags.append(create_flag(
                FlagCategory.CAPACITY,
                Severity.HIGH,
                f"DSCR {financials.dscr:.2f} (insufficient coverage)",
                "Financial Statements",
                -40.0
            ))
    else:
        score -= 15
        flags.append(create_flag(
            FlagCategory.CAPACITY,
            Severity.MEDIUM,
            "DSCR not available",
            "Financial Statements",
            -15.0
        ))
    
    # Revenue YoY Growth
    if financials.revenue_history and len(financials.revenue_history) >= 2:
        rev = financials.revenue_history
        
        # Check for two consecutive year decline
        if len(rev) >= 3 and rev[0] < rev[1] and rev[1] < rev[2]:
            score -= 35
            flags.append(create_flag(
                FlagCategory.CAPACITY,
                Severity.HIGH,
                "Two consecutive years of revenue decline",
                "Financial Statements",
                -35.0
            ))
        else:
            # Calculate YoY growth
            if rev[1] > 0:
                growth = ((rev[0] - rev[1]) / rev[1]) * 100
                
                if growth >= 15:
                    pass  # No deduction
                elif growth >= 5:
                    score -= 5
                    flags.append(create_flag(
                        FlagCategory.CAPACITY,
                        Severity.LOW,
                        f"Revenue growth {growth:.1f}% (moderate)",
                        "Financial Statements",
                        -5.0
                    ))
                elif growth >= 0:
                    score -= 15
                    flags.append(create_flag(
                        FlagCategory.CAPACITY,
                        Severity.MEDIUM,
                        f"Revenue growth {growth:.1f}% (low)",
                        "Financial Statements",
                        -15.0
                    ))
                else:  # Negative growth
                    score -= 25
                    flags.append(create_flag(
                        FlagCategory.CAPACITY,
                        Severity.HIGH,
                        f"Revenue declined {abs(growth):.1f}%",
                        "Financial Statements",
                        -25.0
                    ))
    
    # Cheque bounces
    if financials.cheque_bounces_12m > 5:
        score -= 40
        flags.append(create_flag(
            FlagCategory.CAPACITY,
            Severity.HIGH,
            f"{financials.cheque_bounces_12m} cheque bounces in 12 months",
            "Bank Statements",
            -40.0
        ))
    elif financials.cheque_bounces_12m >= 3:
        score -= 25
        flags.append(create_flag(
            FlagCategory.CAPACITY,
            Severity.MEDIUM,
            f"{financials.cheque_bounces_12m} cheque bounces in 12 months",
            "Bank Statements",
            -25.0
        ))
    elif financials.cheque_bounces_12m >= 1:
        score -= 10
        flags.append(create_flag(
            FlagCategory.CAPACITY,
            Severity.LOW,
            f"{financials.cheque_bounces_12m} cheque bounce(s) in 12 months",
            "Bank Statements",
            -10.0
        ))
    
    # OD Utilization
    if financials.od_utilization_pct is not None:
        if financials.od_utilization_pct > 90:
            score -= 25
            flags.append(create_flag(
                FlagCategory.CAPACITY,
                Severity.HIGH,
                f"OD utilization {financials.od_utilization_pct:.1f}% (overextended)",
                "Bank Statements",
                -25.0
            ))
        elif financials.od_utilization_pct > 70:
            score -= 15
            flags.append(create_flag(
                FlagCategory.CAPACITY,
                Severity.MEDIUM,
                f"OD utilization {financials.od_utilization_pct:.1f}% (high)",
                "Bank Statements",
                -15.0
            ))
        elif financials.od_utilization_pct > 50:
            score -= 5
            flags.append(create_flag(
                FlagCategory.CAPACITY,
                Severity.LOW,
                f"OD utilization {financials.od_utilization_pct:.1f}% (moderate)",
                "Bank Statements",
                -5.0
            ))
    
    # GST circular trading impact
    for gst_flag in gst_flags:
        if "circular trading" in gst_flag.description.lower():
            score += gst_flag.impact_score  # Already negative
            flags.append(gst_flag)
        elif "GST/Bank discrepancy" in gst_flag.description or "revenue inflation" in gst_flag.description.lower():
            score += gst_flag.impact_score  # Already negative
            flags.append(gst_flag)
    
    # Apply floor
    score = apply_floor_ceiling(score, floor=10.0)
    
    return score, flags


# ============================================================================
# TASK 7.4: CAPITAL SCORE CALCULATION
# ============================================================================

def calculate_capital_score(financials: FinancialData) -> Tuple[float, List[FlagItem]]:
    """
    Calculate CAPITAL score (20% weight).
    Base: 100 | Floor: 10
    
    Assesses financial strength, net worth, D/E ratio, promoter contribution.
    
    Args:
        financials: Financial data
        
    Returns:
        Tuple of (score, flags)
    """
    score = 100.0
    flags = []
    
    if not financials:
        return 50.0, [create_flag(
            FlagCategory.CAPITAL,
            Severity.MEDIUM,
            "No financial data available",
            "System",
            -50.0
        )]
    
    # D/E Ratio (5 bands) - CRITICAL
    if financials.debt_equity_ratio is not None:
        de_ratio = financials.debt_equity_ratio
        if de_ratio < 1.0:
            pass  # No deduction
        elif de_ratio < 1.5:
            score -= 10
            flags.append(create_flag(
                FlagCategory.CAPITAL,
                Severity.LOW,
                f"D/E ratio {de_ratio:.2f} (acceptable)",
                "Financial Statements",
                -10.0
            ))
        elif de_ratio < 2.5:
            score -= 20
            flags.append(create_flag(
                FlagCategory.CAPITAL,
                Severity.MEDIUM,
                f"D/E ratio {de_ratio:.2f} (elevated)",
                "Financial Statements",
                -20.0
            ))
        elif de_ratio < 3.0:
            score -= 30
            flags.append(create_flag(
                FlagCategory.CAPITAL,
                Severity.HIGH,
                f"D/E ratio {de_ratio:.2f} (high leverage)",
                "Financial Statements",
                -30.0
            ))
        else:  # >= 3.0
            score -= 45
            flags.append(create_flag(
                FlagCategory.CAPITAL,
                Severity.HIGH,
                f"D/E ratio {de_ratio:.2f} (excessive leverage)",
                "Financial Statements",
                -45.0
            ))
    else:
        score -= 10
        flags.append(create_flag(
            FlagCategory.CAPITAL,
            Severity.MEDIUM,
            "D/E ratio not available",
            "Financial Statements",
            -10.0
        ))
    
    # Net Worth trend
    if financials.net_worth_history and len(financials.net_worth_history) >= 2:
        nw = financials.net_worth_history
        
        # Check if negative
        if nw[0] < 0:
            score -= 50
            flags.append(create_flag(
                FlagCategory.CAPITAL,
                Severity.HIGH,
                f"Negative net worth: ₹{nw[0]:.2f} Cr",
                "Financial Statements",
                -50.0
            ))
        elif nw[0] < nw[1]:
            score -= 25
            flags.append(create_flag(
                FlagCategory.CAPITAL,
                Severity.MEDIUM,
                "Net worth declining",
                "Financial Statements",
                -25.0
            ))
        elif abs(nw[0] - nw[1]) / nw[1] < 0.05:  # Flat (< 5% change)
            score -= 10
            flags.append(create_flag(
                FlagCategory.CAPITAL,
                Severity.LOW,
                "Net worth flat (not growing)",
                "Financial Statements",
                -10.0
            ))
    
    # Promoter contribution %
    if financials.promoter_contribution_pct is not None:
        contrib = financials.promoter_contribution_pct
        if contrib > 30:
            pass  # No deduction
        elif contrib >= 20:
            score -= 10
            flags.append(create_flag(
                FlagCategory.CAPITAL,
                Severity.LOW,
                f"Promoter contribution {contrib:.1f}% (moderate)",
                "Financial Statements",
                -10.0
            ))
        elif contrib >= 10:
            score -= 20
            flags.append(create_flag(
                FlagCategory.CAPITAL,
                Severity.MEDIUM,
                f"Promoter contribution {contrib:.1f}% (low)",
                "Financial Statements",
                -20.0
            ))
        else:  # < 10%
            score -= 35
            flags.append(create_flag(
                FlagCategory.CAPITAL,
                Severity.HIGH,
                f"Promoter contribution {contrib:.1f}% (very low)",
                "Financial Statements",
                -35.0
            ))
    
    # Promoter pledge % (also affects CAPITAL)
    if financials.promoter_pledge_pct is not None:
        pledge = financials.promoter_pledge_pct
        if pledge > 50:
            score -= 40
            flags.append(create_flag(
                FlagCategory.CAPITAL,
                Severity.HIGH,
                f"Promoter pledge {pledge:.1f}% (high distress signal)",
                "Stock Exchange Filing",
                -40.0
            ))
        elif pledge > 25:
            score -= 25
            flags.append(create_flag(
                FlagCategory.CAPITAL,
                Severity.MEDIUM,
                f"Promoter pledge {pledge:.1f}% (moderate concern)",
                "Stock Exchange Filing",
                -25.0
            ))
        elif pledge > 10:
            score -= 10
            flags.append(create_flag(
                FlagCategory.CAPITAL,
                Severity.LOW,
                f"Promoter pledge {pledge:.1f}% (minor concern)",
                "Stock Exchange Filing",
                -10.0
            ))
    
    # Apply floor
    score = apply_floor_ceiling(score, floor=10.0)
    
    return score, flags


# ============================================================================
# TASK 7.5: COLLATERAL SCORE CALCULATION
# ============================================================================

def calculate_collateral_score(financials: FinancialData) -> Tuple[float, List[FlagItem]]:
    """
    Calculate COLLATERAL score (15% weight).
    Base: 100 | Floor: 10
    
    Assesses security coverage with haircuts and guarantees.
    
    Args:
        financials: Financial data
        
    Returns:
        Tuple of (score, flags)
    """
    score = 100.0
    flags = []
    
    if not financials:
        return 50.0, [create_flag(
            FlagCategory.COLLATERAL,
            Severity.MEDIUM,
            "No financial data available",
            "System",
            -50.0
        )]
    
    # Coverage ratio calculation
    if financials.collateral_value is not None and financials.loan_requested is not None:
        # Apply 75% haircut
        coverage_ratio = (financials.collateral_value * 0.75) / financials.loan_requested
        
        if coverage_ratio > 2.0:
            pass  # No deduction
        elif coverage_ratio >= 1.5:
            score -= 10
            flags.append(create_flag(
                FlagCategory.COLLATERAL,
                Severity.LOW,
                f"Coverage ratio {coverage_ratio:.2f}x (adequate)",
                "Collateral Valuation",
                -10.0
            ))
        elif coverage_ratio >= 1.2:
            score -= 20
            flags.append(create_flag(
                FlagCategory.COLLATERAL,
                Severity.MEDIUM,
                f"Coverage ratio {coverage_ratio:.2f}x (moderate)",
                "Collateral Valuation",
                -20.0
            ))
        elif coverage_ratio >= 1.0:
            score -= 35
            flags.append(create_flag(
                FlagCategory.COLLATERAL,
                Severity.HIGH,
                f"Coverage ratio {coverage_ratio:.2f}x (marginal)",
                "Collateral Valuation",
                -35.0
            ))
        else:  # < 1.0
            score -= 60
            flags.append(create_flag(
                FlagCategory.COLLATERAL,
                Severity.HIGH,
                f"Coverage ratio {coverage_ratio:.2f}x (insufficient)",
                "Collateral Valuation",
                -60.0
            ))
    else:
        score -= 25
        flags.append(create_flag(
            FlagCategory.COLLATERAL,
            Severity.HIGH,
            "Collateral value or loan amount not available",
            "Application Data",
            -25.0
        ))
    
    # Asset type penalties
    if financials.collateral_type:
        asset_type = financials.collateral_type.lower()
        if "machinery" in asset_type:
            score -= 15
            flags.append(create_flag(
                FlagCategory.COLLATERAL,
                Severity.MEDIUM,
                "Collateral type: Machinery (depreciation risk)",
                "Collateral Valuation",
                -15.0
            ))
        elif "inventory" in asset_type:
            score -= 20
            flags.append(create_flag(
                FlagCategory.COLLATERAL,
                Severity.MEDIUM,
                "Collateral type: Inventory (perishable risk)",
                "Collateral Valuation",
                -20.0
            ))
        elif "receivable" in asset_type:
            score -= 25
            flags.append(create_flag(
                FlagCategory.COLLATERAL,
                Severity.HIGH,
                "Collateral type: Receivables (collection risk)",
                "Collateral Valuation",
                -25.0
            ))
        # Property has no penalty (most liquid)
    
    # Guarantee additions
    if financials.guarantee_type:
        guarantee = financials.guarantee_type.lower()
        if "corporate" in guarantee:
            score += 10
            flags.append(create_flag(
                FlagCategory.COLLATERAL,
                Severity.GREEN,
                "Corporate guarantee provided",
                "Guarantee Documents",
                10.0
            ))
        elif "personal" in guarantee:
            score += 5
            flags.append(create_flag(
                FlagCategory.COLLATERAL,
                Severity.GREEN,
                "Personal guarantee provided",
                "Guarantee Documents",
                5.0
            ))
    
    # Apply floor and ceiling
    score = apply_floor_ceiling(score, floor=10.0)
    
    return score, flags


# ============================================================================
# TASK 7.6: CONDITIONS SCORE CALCULATION
# ============================================================================

def calculate_conditions_score(sector: str, research: Optional[ResearchResult]) -> Tuple[float, List[FlagItem]]:
    """
    Calculate CONDITIONS score (10% weight).
    Base: 70 (NOT 100) | Floor: 10
    
    Assesses industry and market conditions using sector outlook and NPA rates.
    
    Args:
        sector: Company sector
        research: Research results with sector data
        
    Returns:
        Tuple of (score, flags)
    """
    score = 70.0  # CRITICAL: Base is 70, not 100
    flags = []
    
    # Step 1: Sector outlook (Groq classification)
    sector_outlook = "STABLE"  # Default
    if research and research.sector_outlook:
        sector_outlook = research.sector_outlook.upper()
    
    if sector_outlook == "GROWING":
        score += 15
        flags.append(create_flag(
            FlagCategory.CONDITIONS,
            Severity.GREEN,
            f"Sector outlook: {sector_outlook}",
            "Market Research",
            15.0
        ))
    elif sector_outlook == "STABLE":
        pass  # No adjustment
    elif sector_outlook == "DECLINING":
        score -= 15
        flags.append(create_flag(
            FlagCategory.CONDITIONS,
            Severity.MEDIUM,
            f"Sector outlook: {sector_outlook}",
            "Market Research",
            -15.0
        ))
    elif sector_outlook == "DISTRESSED":
        score -= 30
        flags.append(create_flag(
            FlagCategory.CONDITIONS,
            Severity.HIGH,
            f"Sector outlook: {sector_outlook}",
            "Market Research",
            -30.0
        ))
    
    # Step 2: Sector NPA rate
    npa_rate = SECTOR_NPA.get(sector, None)
    if npa_rate is not None:
        if npa_rate < 3.0:
            score += 5
            flags.append(create_flag(
                FlagCategory.CONDITIONS,
                Severity.GREEN,
                f"Sector NPA rate: {npa_rate}% (low risk)",
                "RBI Sector Data",
                5.0
            ))
        elif npa_rate <= 6.0:
            pass  # No adjustment
        elif npa_rate <= 10.0:
            score -= 10
            flags.append(create_flag(
                FlagCategory.CONDITIONS,
                Severity.MEDIUM,
                f"Sector NPA rate: {npa_rate}% (moderate risk)",
                "RBI Sector Data",
                -10.0
            ))
        else:  # > 10%
            score -= 20
            flags.append(create_flag(
                FlagCategory.CONDITIONS,
                Severity.HIGH,
                f"Sector NPA rate: {npa_rate}% (high risk)",
                "RBI Sector Data",
                -20.0
            ))
    
    # Apply floor
    score = apply_floor_ceiling(score, floor=10.0)
    
    return score, flags


# ============================================================================
# TASK 7.7: VERDICT DETERMINATION LOGIC
# ============================================================================

def determine_verdict(total_score: float, bank_credits_annual: Optional[float], loan_requested: Optional[float]) -> Dict:
    """
    Determine verdict and loan terms based on total score.
    Uses FORMULA-BASED interest rates (not fixed bands).
    
    Args:
        total_score: Final weighted score (10-100)
        bank_credits_annual: Annual bank inflows in ₹ Crores
        loan_requested: Requested loan amount in ₹ Crores
        
    Returns:
        Dict with verdict, loan_amount, interest_rate
    """
    if total_score > 70:
        # APPROVE
        if bank_credits_annual and loan_requested:
            loan_amount = min(bank_credits_annual * 3.5, loan_requested)
        else:
            loan_amount = loan_requested
        
        # Formula: 10.5% + (70 - score) * 0.1
        interest_rate = 10.5 + ((70 - total_score) * 0.1)
        
        return {
            "verdict": Verdict.APPROVE,
            "loan_amount": loan_amount,
            "interest_rate": f"{interest_rate:.2f}% p.a."
        }
    
    elif total_score >= 50:
        # CONDITIONAL APPROVE
        if bank_credits_annual and loan_requested:
            loan_amount = min(bank_credits_annual * 2.0, loan_requested)
        else:
            loan_amount = loan_requested * 0.7 if loan_requested else None
        
        # Formula: 10.5% + (70 - score) * 0.15
        interest_rate = 10.5 + ((70 - total_score) * 0.15)
        
        return {
            "verdict": Verdict.CONDITIONAL,
            "loan_amount": loan_amount,
            "interest_rate": f"{interest_rate:.2f}% p.a."
        }
    
    else:
        # REJECT
        return {
            "verdict": Verdict.REJECT,
            "loan_amount": None,
            "interest_rate": None
        }


# ============================================================================
# TASK 7.8: MASTER CALCULATE_FIVE_CS() FUNCTION
# ============================================================================

def calculate_five_cs(company_data: CompanyData) -> ScoreResult:
    """
    Master scoring function - orchestrates all Five Cs calculations.
    
    Args:
        company_data: Complete company data
        
    Returns:
        ScoreResult with total score, verdict, and all flags
    """
    all_flags = []
    
    # Calculate each C score
    character_score, char_flags = calculate_character_score(company_data)
    all_flags.extend(char_flags)
    
    # For CAPACITY, we need GST flags if available
    gst_flags = []
    if company_data.financials:
        # Check for GST circular trading
        if company_data.financials.gst_turnover and company_data.financials.bank_credits_annual:
            gst_gap = ((company_data.financials.gst_turnover - company_data.financials.bank_credits_annual) 
                      / company_data.financials.gst_turnover * 100)
            
            if gst_gap >= 35:
                gst_flags.append(create_flag(
                    FlagCategory.GST_FRAUD,
                    Severity.HIGH,
                    f"GST/Bank gap {gst_gap:.1f}% - circular trading signal",
                    "GST vs Bank Cross-check",
                    -40.0
                ))
            elif gst_gap >= 20:
                gst_flags.append(create_flag(
                    FlagCategory.GST_FRAUD,
                    Severity.HIGH,
                    f"GST/Bank gap {gst_gap:.1f}% - revenue inflation risk",
                    "GST vs Bank Cross-check",
                    -25.0
                ))
            elif gst_gap >= 10:
                gst_flags.append(create_flag(
                    FlagCategory.GST_FRAUD,
                    Severity.MEDIUM,
                    f"GST/Bank gap {gst_gap:.1f}% - discrepancy detected",
                    "GST vs Bank Cross-check",
                    -10.0
                ))
        
        # Check for ITC fraud
        if company_data.financials.gstr_3b_itc and company_data.financials.gstr_2a_itc:
            if company_data.financials.gstr_3b_itc > 0:
                itc_gap = ((company_data.financials.gstr_3b_itc - company_data.financials.gstr_2a_itc) 
                          / company_data.financials.gstr_3b_itc * 100)
                
                if itc_gap > 15:
                    gst_flags.append(create_flag(
                        FlagCategory.GST_FRAUD,
                        Severity.HIGH,
                        f"ITC gap {itc_gap:.1f}% - fraud signal",
                        "GSTR-3B vs GSTR-2A",
                        -25.0
                    ))
                elif itc_gap >= 5:
                    gst_flags.append(create_flag(
                        FlagCategory.GST_FRAUD,
                        Severity.MEDIUM,
                        f"ITC gap {itc_gap:.1f}% - discrepancy",
                        "GSTR-3B vs GSTR-2A",
                        -10.0
                    ))
    
    capacity_score, cap_flags = calculate_capacity_score(company_data.financials, gst_flags)
    all_flags.extend(cap_flags)
    
    capital_score, capt_flags = calculate_capital_score(company_data.financials)
    all_flags.extend(capt_flags)
    
    collateral_score, coll_flags = calculate_collateral_score(company_data.financials)
    all_flags.extend(coll_flags)
    
    # For CONDITIONS, get sector from research
    sector = "Unknown"
    if company_data.research and company_data.research.sector:
        sector = company_data.research.sector
    
    conditions_score, cond_flags = calculate_conditions_score(sector, company_data.research)
    all_flags.extend(cond_flags)
    
    # Calculate weighted total score
    total_score = (
        character_score * 0.25 +
        capacity_score * 0.30 +
        capital_score * 0.20 +
        collateral_score * 0.15 +
        conditions_score * 0.10
    )
    
    # Apply floor and ceiling
    total_score = apply_floor_ceiling(total_score, 10.0, 100.0)
    
    # Round to 1 decimal place
    total_score = round(total_score, 1)
    
    # Determine verdict and loan terms
    bank_credits = company_data.financials.bank_credits_annual if company_data.financials else None
    loan_requested = company_data.financials.loan_requested if company_data.financials else None
    verdict_data = determine_verdict(total_score, bank_credits, loan_requested)
    
    # Generate reasoning
    reasoning = generate_reasoning(
        total_score,
        character_score,
        capacity_score,
        capital_score,
        collateral_score,
        conditions_score,
        all_flags
    )
    
    # Create decision narrative from top 3 flags
    top_flags = sorted(
        all_flags,
        key=lambda f: ({"HIGH": 0, "MEDIUM": 1, "LOW": 2, "GREEN": 3}.get(f.severity.value, 4), abs(f.impact_score)),
        reverse=True
    )[:3]
    
    if top_flags:
        narrative_parts = [f.description for f in top_flags]
        decision_narrative = "Key factors: " + "; ".join(narrative_parts)
    else:
        decision_narrative = "No significant flags detected"
    
    # Build ScoreResult
    return ScoreResult(
        character_score=round(character_score, 1),
        capacity_score=round(capacity_score, 1),
        capital_score=round(capital_score, 1),
        collateral_score=round(collateral_score, 1),
        conditions_score=round(conditions_score, 1),
        total_score=total_score,
        verdict=verdict_data["verdict"],
        loan_amount=verdict_data["loan_amount"],
        interest_rate=verdict_data["interest_rate"],
        flags=all_flags,
        reasoning=reasoning,
        decision_narrative=decision_narrative
    )


# ============================================================================
# TASK 7.9: VALIDATE SCORER WITH IL&FS TEST DATA
# ============================================================================

def validate_scorer_with_ilfs():
    """
    Validate scorer with hardcoded IL&FS test data.
    Expected: CHARACTER ~10, CAPACITY ~10, CAPITAL ~10, COLLATERAL ~40, CONDITIONS ~35
    Final score: 13-18, verdict: REJECT
    """
    from data_models import FinancialData, ResearchResult, CompanyData
    
    # IL&FS hardcoded data
    ilfs_financials = FinancialData(
        # Revenue and profitability
        revenue_history=[8500.0, 9200.0, 9800.0],  # Declining
        net_profit_history=[-5000.0, -3000.0, 500.0],
        ebitda=1200.0,
        
        # Debt servicing
        dscr=0.58,  # Very poor
        interest_coverage=0.8,
        total_debt=91000.0,
        
        # Balance sheet
        net_worth_history=[-15000.0, -8000.0, 5000.0],  # Negative
        current_ratio=0.6,
        debt_equity_ratio=7.8,  # Excessive
        
        # Promoter details
        promoter_contribution_pct=8.0,  # Very low
        promoter_pledge_pct=72.0,  # Very high
        
        # Banking conduct
        cheque_bounces_12m=9,  # High
        od_utilization_pct=94.0,  # Overextended
        bank_credits_annual=3680.0,
        
        # GST data (56.7% gap for circular trading signal)
        gst_turnover=8500.0,
        gstr_3b_itc=850.0,
        gstr_2a_itc=820.0,
        
        # Collateral (coverage 0.9x for ~40 score)
        collateral_value=1200.0,  # 1200 * 0.75 / 1000 = 0.9x coverage
        collateral_type="Property",
        guarantee_type=None,
        loan_requested=1000.0,
        
        # Audit and compliance
        audit_opinion="Qualified",
        going_concern_flag=True,
        
        # Legal cases
        nclt_cases=1,
        drt_cases=0,
        criminal_cases=0,
        sebi_actions=0,
        ed_actions=0,
        
        # MCA status
        mca_status="Active",
        din_deactivated=False,
        
        # Rating
        credit_rating="D",
        rating_downgrade_months=6
    )
    
    ilfs_research = ResearchResult(
        sector="Infrastructure Finance",
        sector_outlook="DISTRESSED",
        sector_npa_rate=18.4
    )
    
    ilfs_data = CompanyData(
        cin="L65990MH1987PLC044571",
        company_name="IL&FS",
        financials=ilfs_financials,
        research=ilfs_research,
        demo_mode=True
    )
    
    # Calculate score
    result = calculate_five_cs(ilfs_data)
    
    # Print results
    print("\n" + "="*60)
    print("IL&FS VALIDATION TEST")
    print("="*60)
    print(f"\nCHARACTER Score: {result.character_score:.1f}/100 (Expected: ~10)")
    print(f"CAPACITY Score: {result.capacity_score:.1f}/100 (Expected: ~10)")
    print(f"CAPITAL Score: {result.capital_score:.1f}/100 (Expected: ~10)")
    print(f"COLLATERAL Score: {result.collateral_score:.1f}/100 (Expected: ~40)")
    print(f"CONDITIONS Score: {result.conditions_score:.1f}/100 (Expected: ~35)")
    print(f"\nTOTAL SCORE: {result.total_score:.1f}/100 (Expected: 13-18)")
    print(f"VERDICT: {result.verdict.value} (Expected: REJECT)")
    
    # Validate ranges
    assert 8 <= result.character_score <= 15, f"CHARACTER score {result.character_score} out of expected range"
    assert 8 <= result.capacity_score <= 15, f"CAPACITY score {result.capacity_score} out of expected range"
    assert 8 <= result.capital_score <= 15, f"CAPITAL score {result.capital_score} out of expected range"
    assert 35 <= result.collateral_score <= 50, f"COLLATERAL score {result.collateral_score} out of expected range"
    assert 15 <= result.conditions_score <= 40, f"CONDITIONS score {result.conditions_score} out of expected range"
    assert 13 <= result.total_score <= 20, f"TOTAL score {result.total_score} out of expected range (13-20)"
    assert result.verdict == Verdict.REJECT, f"Verdict should be REJECT, got {result.verdict.value}"
    
    print("\n✅ All validations PASSED!")
    print(f"\nTotal Flags Generated: {len(result.flags)}")
    print("\nAll Flags:")
    for i, flag in enumerate(result.flags, 1):
        print(f"  {i}. [{flag.severity.value}] {flag.description} (Impact: {flag.impact_score})")
    
    print("\n" + "="*60)
    
    return result


if __name__ == "__main__":
    # Run validation when script is executed directly
    print("Running IL&FS validation test...")
    validate_scorer_with_ilfs()
