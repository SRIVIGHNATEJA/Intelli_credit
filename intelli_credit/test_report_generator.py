"""
Test script for report_generator.py
Demonstrates CAM generation with IL&FS test data
"""

from data_models import (
    FinancialData, ResearchResult, CompanyData, NewsItem, StockData,
    OfficerNote, FlagCategory
)
from scorer import calculate_five_cs
from report_generator import generate_cam_word, generate_decision_narrative


def test_ilfs_cam_generation():
    """
    Test CAM generation with IL&FS data including officer notes.
    """
    print("="*70)
    print("TEST: IL&FS CAM GENERATION WITH OFFICER NOTES")
    print("="*70)
    
    # IL&FS financial data
    ilfs_financials = FinancialData(
        revenue=[8500.0, 9200.0, 9800.0],
        net_profit=[-5000.0, -3000.0, 500.0],
        ebitda=1200.0,
        dscr=0.58,
        interest_coverage=0.8,
        total_debt=91000.0,
        net_worth=[-15000.0, -8000.0, 5000.0],
        current_ratio=0.6,
        debt_equity_ratio=7.8,
        promoter_contribution_pct=8.0,
        promoter_pledge_pct=72.0,
        cheque_bounces_count=9,
        od_utilization_percent=94.0,
        bank_credits_annual=3680.0,
        gst_turnover_annual=8500.0,
        gstr_3b_itc=850.0,
        gstr_2a_itc=820.0,
        collateral_value=1200.0,
        collateral_type="Property",
        guarantee_type=None,
        loan_requested=1000.0,
        audit_opinion="Qualified",
        going_concern_flag=True,
        nclt_cases=1,
        drt_cases=0,
        criminal_cases=0,
        sebi_actions=0,
        ed_actions=0,
        mca_status="Active",
        din_deactivated=False,
        credit_rating="D",
        rating_downgrade_months=6
    )
    
    # Research data with news items
    ilfs_research = ResearchResult(
        sector="Infrastructure Finance",
        sector_outlook="DISTRESSED",
        sector_npa_rate=18.4,
        news_items=[
            NewsItem(
                title="IL&FS Crisis: NCLT admits insolvency proceedings",
                source="Economic Times",
                date="2023-09-15",
                url="https://economictimes.com/ilfs-crisis",
                snippet="The National Company Law Tribunal has admitted insolvency proceedings against IL&FS..."
            ),
            NewsItem(
                title="IL&FS defaults on debt obligations worth ₹91,000 crores",
                source="Business Standard",
                date="2023-08-20",
                url="https://business-standard.com/ilfs-default",
                snippet="Infrastructure Leasing & Financial Services has defaulted on multiple debt obligations..."
            ),
            NewsItem(
                title="Rating agencies downgrade IL&FS to D category",
                source="Mint",
                date="2023-07-10",
                url="https://livemint.com/ilfs-downgrade",
                snippet="Major rating agencies have downgraded IL&FS credit rating to D following payment defaults..."
            )
        ],
        mca_status="Active",
        stock_data=StockData(
            ticker="ILFS.NS",
            current_price=12.50,
            market_cap=500.0,
            is_listed=True
        )
    )
    
    # Create company data
    ilfs_data = CompanyData(
        cin="U65990MH1987PLC042230",
        company_name="IL&FS",
        promoter_name="Ravi Parthasarathy",
        financials=ilfs_financials,
        research=ilfs_research,
        cibil_cmr_rank=8,  # Included for backwards compatibility with the new feature
        demo_mode=True
    )
    
    # Add officer notes
    ilfs_data.officer_notes = [
        OfficerNote(
            note_text="Promoter has history of aggressive accounting practices. Multiple red flags in audit reports.",
            affected_c=FlagCategory.CHARACTER,
            adjustment=-15.0,
            timestamp="2024-03-09T10:30:00"
        ),
        OfficerNote(
            note_text="Company has strong infrastructure assets but liquidity crisis is severe. Cash flow projections are unrealistic.",
            affected_c=FlagCategory.CAPACITY,
            adjustment=-10.0,
            timestamp="2024-03-09T11:00:00"
        ),
        OfficerNote(
            note_text="Collateral valuation appears inflated. Independent valuation recommended.",
            affected_c=FlagCategory.COLLATERAL,
            adjustment=-20.0,
            timestamp="2024-03-09T11:30:00"
        )
    ]
    
    print("\n1. Calculating Five Cs score...")
    score_result = calculate_five_cs(ilfs_data)
    
    print(f"\n2. Score Results:")
    print(f"   CHARACTER: {score_result.character_score:.1f}/100")
    print(f"   CAPACITY: {score_result.capacity_score:.1f}/100")
    print(f"   CAPITAL: {score_result.capital_score:.1f}/100")
    print(f"   COLLATERAL: {score_result.collateral_score:.1f}/100")
    print(f"   CONDITIONS: {score_result.conditions_score:.1f}/100")
    print(f"   TOTAL: {score_result.final_score:.1f}/100")
    print(f"   VERDICT: {score_result.verdict.value}")
    
    print(f"\n3. Generating decision narrative from top 3 flags...")
    score_result.decision_narrative = generate_decision_narrative(
        score_result.flags,
        score_result.verdict.value
    )
    print(f"   Narrative: {score_result.decision_narrative}")
    
    print(f"\n4. Generating CAM Word document...")
    output_path = "test_cam_ilfs_complete.docx"
    generated_path = generate_cam_word(ilfs_data, score_result, output_path)
    
    print(f"\n✅ SUCCESS!")
    print(f"\n📄 Document Details:")
    print(f"   Path: {generated_path}")
    print(f"   Sections:")
    print(f"     ✓ Executive Summary with {score_result.verdict.value} verdict")
    print(f"     ✓ Company Overview (CIN, Sector, MCA Status)")
    print(f"     ✓ Financial Analysis (Revenue, Ratios, Banking Conduct)")
    print(f"     ✓ Five Cs Breakdown with {len(score_result.flags)} flags")
    print(f"     ✓ GST Analysis")
    print(f"     ✓ Research Findings with {len(ilfs_research.news_items)} news items")
    print(f"     ✓ Officer Notes ({len(ilfs_data.officer_notes)} notes)")
    print(f"     ✓ Final Recommendation with decision narrative")
    
    print(f"\n📊 Key Metrics:")
    print(f"   Total Flags: {len(score_result.flags)}")
    print(f"   Officer Adjustments: {len(ilfs_data.officer_notes)}")
    print(f"   News Items: {len(ilfs_research.news_items)}")
    print(f"   Loan Requested: ₹ {ilfs_financials.loan_requested:,.2f} Crores")
    print(f"   Loan Approved: {score_result.loan_amount or 'REJECTED'}")
    
    print("\n" + "="*70)
    
    return generated_path


def test_currency_formatting():
    """
    Test currency formatting in Indian format.
    """
    from report_generator import format_currency_inr
    
    print("\n" + "="*70)
    print("TEST: CURRENCY FORMATTING")
    print("="*70)
    
    test_cases = [
        (1000.0, "Crores", "₹ 1,000.00 Crores"),
        (1000.0, "Lakhs", "₹ 1,00,000.00 Lakhs"),
        (91000.0, "Crores", "₹ 91,000.00 Crores"),
        (None, "Crores", "N/A"),
        (0.58, "Crores", "₹ 0.58 Crores")
    ]
    
    print("\nTest Cases:")
    for amount, unit, expected in test_cases:
        result = format_currency_inr(amount, unit)
        status = "✓" if result == expected else "✗"
        print(f"  {status} format_currency_inr({amount}, '{unit}') = {result}")
        if result != expected:
            print(f"     Expected: {expected}")
    
    print("\n" + "="*70)


def test_decision_narrative():
    """
    Test decision narrative generation.
    """
    from data_models import create_flag, FlagCategory, Severity
    from report_generator import generate_decision_narrative
    
    print("\n" + "="*70)
    print("TEST: DECISION NARRATIVE GENERATION")
    print("="*70)
    
    # Create test flags
    test_flags = [
        create_flag(FlagCategory.CHARACTER, Severity.HIGH, "NCLT case pending", "MCA Portal", -10.0),
        create_flag(FlagCategory.CAPACITY, Severity.HIGH, "DSCR below 1.1", "Financial Statements", -40.0),
        create_flag(FlagCategory.CAPITAL, Severity.HIGH, "Negative net worth", "Balance Sheet", -50.0),
        create_flag(FlagCategory.COLLATERAL, Severity.MEDIUM, "Coverage below 1.0x", "Collateral Valuation", -60.0),
        create_flag(FlagCategory.CONDITIONS, Severity.HIGH, "Sector in distress", "Industry Report", -30.0)
    ]
    
    print("\nTest Flags (sorted by impact):")
    for flag in sorted(test_flags, key=lambda f: abs(f.impact_score), reverse=True)[:3]:
        print(f"  - {flag.description} (Impact: {flag.impact_score})")
    
    narrative = generate_decision_narrative(test_flags, "REJECT")
    
    print(f"\nGenerated Narrative:")
    print(f"  {narrative}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    # Run all tests
    print("\n🧪 RUNNING REPORT GENERATOR TESTS\n")
    
    # Test 1: Currency formatting
    test_currency_formatting()
    
    # Test 2: Decision narrative
    test_decision_narrative()
    
    # Test 3: Full CAM generation
    test_ilfs_cam_generation()
    
    print("\n✅ ALL TESTS COMPLETED!\n")
