#!/usr/bin/env python3
"""
Demo Cache Generator for Intelli-Credit
Generates cached CompanyData + ScoreResult for IL&FS, TCS, and Byju's
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

from data_models import (
    CompanyData, FinancialData, ResearchResult, NewsItem, StockData,
    OfficerNote, EarlyWarning, FlagCategory, Severity
)
from scorer import calculate_five_cs
from dummy_data import DEMO_COMPANIES

# Load environment variables
load_dotenv()

def create_ilfs_financial_data() -> FinancialData:
    """Create realistic IL&FS financial data (distressed company)"""
    return FinancialData(
        # Revenue declining (Infrastructure Finance sector)
        revenue=[8500.0, 12000.0, 15000.0],  # Current, -1, -2 years (₹ Crores)
        net_profit=[-2500.0, -1800.0, 500.0],  # Losses in recent years
        ebitda=-1200.0,
        
        # Poor debt servicing
        dscr=0.58,  # Very poor coverage
        interest_coverage=0.45,
        total_debt=91000.0,  # High debt
        
        # Weak balance sheet
        net_worth=[-15000.0, -8000.0, 5000.0],  # Negative net worth
        current_ratio=0.85,
        debt_equity_ratio=7.80,  # Very high leverage
        
        # Promoter issues
        promoter_contribution_pct=8.0,  # Very low
        promoter_pledge_pct=72.0,  # High distress signal
        
        # Poor banking conduct
        cheque_bounces_count=9,
        od_utilization_percent=94.0,  # Overextended
        bank_credits_annual=25000.0,
        
        # GST issues (circular trading)
        gst_turnover_annual=8500.0,
        gstr_3b_itc=850.0,
        gstr_2a_itc=750.0,  # ITC gap
        
        # Collateral
        collateral_value=45000.0,
        collateral_type="Property",
        guarantee_type="Corporate",
        loan_requested=1000.0,
        
        # Audit issues
        audit_opinion="Qualified",
        going_concern_flag=True,
        
        # Legal cases
        nclt_cases=1,
        drt_cases=0,
        criminal_cases=0,
        sebi_actions=0,
        ed_actions=0,
        
        # MCA and rating
        mca_status="Active",
        din_deactivated=False,
        credit_rating="D",
        rating_downgrade_months=6  # Downgraded 6 months ago
    )

def create_tcs_financial_data() -> FinancialData:
    """Create realistic TCS financial data (strong IT company)"""
    return FinancialData(
        # Strong revenue growth (IT Services)
        revenue=[164000.0, 156000.0, 146000.0],  # Growing
        net_profit=[38500.0, 36000.0, 32400.0],  # Consistent profits
        ebitda=52000.0,
        
        # Excellent debt servicing
        dscr=8.5,  # Very strong
        interest_coverage=45.0,
        total_debt=2500.0,  # Low debt
        
        # Strong balance sheet
        net_worth=[85000.0, 78000.0, 72000.0],  # Growing
        current_ratio=2.8,
        debt_equity_ratio=0.2,  # Very low leverage
        
        # Strong promoter base
        promoter_contribution_pct=72.0,  # Tata Group
        promoter_pledge_pct=0.0,  # No pledge
        
        # Excellent banking conduct
        cheque_bounces_count=0,
        od_utilization_percent=15.0,  # Conservative
        bank_credits_annual=180000.0,
        
        # Clean GST
        gst_turnover_annual=164000.0,
        gstr_3b_itc=8200.0,
        gstr_2a_itc=8150.0,  # Minimal gap
        
        # Strong collateral
        collateral_value=120000.0,
        collateral_type="Property",
        guarantee_type="Corporate",
        loan_requested=5000.0,
        
        # Clean audit
        audit_opinion="Clean",
        going_concern_flag=False,
        
        # No legal issues
        nclt_cases=0,
        drt_cases=0,
        criminal_cases=0,
        sebi_actions=0,
        ed_actions=0,
        
        # Strong MCA and rating
        mca_status="Active",
        din_deactivated=False,
        credit_rating="AAA",
        rating_downgrade_months=None
    )

def create_byjus_financial_data() -> FinancialData:
    """Create realistic Byju's financial data (distressed EdTech)"""
    return FinancialData(
        # Declining revenue (EdTech sector)
        revenue=[2200.0, 2800.0, 2400.0],  # Volatile
        net_profit=[-1800.0, -1200.0, -800.0],  # Consistent losses
        ebitda=-900.0,
        
        # Poor debt servicing
        dscr=0.35,  # Very poor
        interest_coverage=0.2,
        total_debt=8500.0,  # High for size
        
        # Deteriorating balance sheet
        net_worth=[-2500.0, -800.0, 1200.0],  # Negative
        current_ratio=0.65,
        debt_equity_ratio=12.5,  # Extremely high
        
        # Promoter issues
        promoter_contribution_pct=15.0,  # Low
        promoter_pledge_pct=85.0,  # Very high distress
        
        # Banking issues
        cheque_bounces_count=12,
        od_utilization_percent=98.0,  # Maxed out
        bank_credits_annual=3500.0,
        
        # GST compliance issues
        gst_turnover_annual=2200.0,
        gstr_3b_itc=330.0,
        gstr_2a_itc=250.0,  # Significant ITC gap
        
        # Limited collateral
        collateral_value=1500.0,
        collateral_type="Receivables",
        guarantee_type="Personal",
        loan_requested=800.0,
        
        # Audit concerns
        audit_opinion="Qualified",
        going_concern_flag=True,
        
        # Some legal issues
        nclt_cases=0,
        drt_cases=2,
        criminal_cases=0,
        sebi_actions=1,
        ed_actions=0,
        
        # MCA issues
        mca_status="Active",
        din_deactivated=False,
        credit_rating="BB-",
        rating_downgrade_months=3
    )

def create_research_data(company_key: str) -> ResearchResult:
    """Create research data for each company"""
    if company_key == "IL&FS":
        return ResearchResult(
            sector="Infrastructure Finance",
            sector_outlook="DISTRESSED",
            sector_npa_rate=18.4,
            mca_status="Active",
            news_items=[
                NewsItem(
                    title="IL&FS Crisis: NCLT Admits Company for Insolvency Resolution",
                    source="Economic Times",
                    date="2023-09-15",
                    url="https://economictimes.indiatimes.com/news/ilfs-crisis",
                    snippet="Infrastructure Leasing and Financial Services faces severe liquidity crisis..."
                ),
                NewsItem(
                    title="IL&FS Default Triggers Broader NBFC Concerns",
                    source="Business Standard",
                    date="2023-08-22",
                    url="https://business-standard.com/ilfs-default",
                    snippet="The company's default on commercial paper has raised concerns..."
                ),
                NewsItem(
                    title="Government Intervenes in IL&FS Resolution Process",
                    source="Mint",
                    date="2023-07-10",
                    url="https://livemint.com/ilfs-resolution",
                    snippet="Ministry of Corporate Affairs takes control of the board..."
                )
            ],
            stock_data=StockData(
                ticker=None,
                current_price=None,
                market_cap=None,
                is_listed=False
            )
        )
    
    elif company_key == "TCS":
        return ResearchResult(
            sector="IT Services",
            sector_outlook="STABLE",
            sector_npa_rate=0.8,
            mca_status="Active",
            news_items=[
                NewsItem(
                    title="TCS Reports Strong Q4 Results, Revenue Grows 16.8%",
                    source="Economic Times",
                    date="2023-10-12",
                    url="https://economictimes.indiatimes.com/tcs-results",
                    snippet="Tata Consultancy Services reported robust growth in revenue..."
                ),
                NewsItem(
                    title="TCS Wins Major Digital Transformation Deal",
                    source="Business Standard",
                    date="2023-09-28",
                    url="https://business-standard.com/tcs-deal",
                    snippet="The IT giant secured a multi-year contract worth $2.25 billion..."
                ),
                NewsItem(
                    title="TCS Expands AI and Cloud Capabilities",
                    source="Mint",
                    date="2023-09-05",
                    url="https://livemint.com/tcs-ai-cloud",
                    snippet="Company invests heavily in artificial intelligence and cloud services..."
                )
            ],
            stock_data=StockData(
                ticker="TCS.NS",
                current_price=3450.75,
                market_cap=1250000.0,  # ₹12.5 lakh crores
                is_listed=True
            )
        )
    
    else:  # Byju's
        return ResearchResult(
            sector="Education Technology",
            sector_outlook="DECLINING",
            sector_npa_rate=12.3,
            mca_status="Active",
            news_items=[
                NewsItem(
                    title="Byju's Faces Funding Crunch, Delays Employee Salaries",
                    source="Economic Times",
                    date="2023-10-01",
                    url="https://economictimes.indiatimes.com/byjus-funding",
                    snippet="The edtech giant is struggling with cash flow issues..."
                ),
                NewsItem(
                    title="Byju's Valuation Drops to $5.1 Billion from Peak of $22 Billion",
                    source="Business Standard",
                    date="2023-09-18",
                    url="https://business-standard.com/byjus-valuation",
                    snippet="Investors mark down the company's valuation significantly..."
                ),
                NewsItem(
                    title="Byju's Faces Regulatory Scrutiny Over Business Practices",
                    source="Mint",
                    date="2023-08-30",
                    url="https://livemint.com/byjus-regulatory",
                    snippet="Education ministry raises concerns about aggressive sales tactics..."
                )
            ],
            stock_data=StockData(
                ticker=None,
                current_price=None,
                market_cap=None,
                is_listed=False
            )
        )

def create_officer_notes(company_key: str) -> list:
    """Create sample officer notes for each company"""
    if company_key == "IL&FS":
        return [
            OfficerNote(
                note_text="Company has significant exposure to stalled infrastructure projects. Management quality deteriorated post-crisis.",
                affected_c=FlagCategory.CHARACTER,
                adjustment=-5.0
            ),
            OfficerNote(
                note_text="Cash flow generation severely impacted by asset-liability mismatch. Recovery prospects uncertain.",
                affected_c=FlagCategory.CAPACITY,
                adjustment=-8.0
            ),
            OfficerNote(
                note_text="Asset quality concerns due to NPAs in subsidiary portfolio. Collateral may not cover exposure.",
                affected_c=FlagCategory.COLLATERAL,
                adjustment=-3.0
            )
        ]
    
    elif company_key == "TCS":
        return [
            OfficerNote(
                note_text="Excellent corporate governance and transparent reporting. Strong management track record.",
                affected_c=FlagCategory.CHARACTER,
                adjustment=2.0
            ),
            OfficerNote(
                note_text="Diversified client base and strong recurring revenue model. Minimal customer concentration risk.",
                affected_c=FlagCategory.CAPACITY,
                adjustment=3.0
            ),
            OfficerNote(
                note_text="Conservative capital structure with minimal debt. Strong cash generation and dividend history.",
                affected_c=FlagCategory.CAPITAL,
                adjustment=1.0
            )
        ]
    
    else:  # Byju's
        return [
            OfficerNote(
                note_text="Aggressive accounting practices and frequent auditor changes raise governance concerns.",
                affected_c=FlagCategory.CHARACTER,
                adjustment=-7.0
            ),
            OfficerNote(
                note_text="Business model sustainability questioned due to high customer acquisition costs and churn.",
                affected_c=FlagCategory.CAPACITY,
                adjustment=-5.0
            ),
            OfficerNote(
                note_text="Rapid expansion funded through debt has created significant leverage. Refinancing risk high.",
                affected_c=FlagCategory.CAPITAL,
                adjustment=-4.0
            )
        ]

def generate_cache_for_company(company_key: str, company_info: dict):
    """Generate cache for a single company"""
    print(f"\n{'='*60}")
    print(f"GENERATING CACHE FOR {company_info['company_name'].upper()}")
    print(f"{'='*60}")
    
    try:
        # Step 1: Create realistic financial data
        print("Step 1: Creating realistic financial data...")
        if company_key == "IL&FS":
            financials = create_ilfs_financial_data()
        elif company_key == "TCS":
            financials = create_tcs_financial_data()
        else:  # Byju's
            financials = create_byjus_financial_data()
        
        # Step 2: Create research data
        print("Step 2: Creating research data...")
        research = create_research_data(company_key)
        
        # Step 3: Create officer notes
        print("Step 3: Creating officer notes...")
        officer_notes = create_officer_notes(company_key)
        
        # Step 4: Create CompanyData
        print("Step 4: Assembling company data...")
        company_data = CompanyData(
            cin=company_info['cin'],
            company_name=company_info['company_name'],
            promoter_name=f"Promoter of {company_info['company_name']}",
            financials=financials,
            research=research,
            officer_notes=officer_notes,
            early_warnings=[],  # Will be populated by scorer
            demo_mode=True
        )
        
        print(f"✅ Company data created for {company_data.company_name}")
        print(f"   CIN: {company_data.cin}")
        print(f"   Sector: {company_data.research.sector}")
        print(f"   Revenue: ₹{financials.revenue[0]:,.0f} Cr")
        print(f"   Net Worth: ₹{financials.net_worth[0]:,.0f} Cr")
        print(f"   D/E Ratio: {financials.debt_equity_ratio:.2f}")
        
        # Step 5: Calculate Five Cs score
        print("Step 5: Calculating Five Cs score...")
        score_result = calculate_five_cs(company_data)
        
        print(f"✅ Scoring complete:")
        print(f"   CHARACTER: {score_result.character_score:.1f}/100")
        print(f"   CAPACITY: {score_result.capacity_score:.1f}/100")
        print(f"   CAPITAL: {score_result.capital_score:.1f}/100")
        print(f"   COLLATERAL: {score_result.collateral_score:.1f}/100")
        print(f"   CONDITIONS: {score_result.conditions_score:.1f}/100")
        print(f"   TOTAL: {score_result.final_score:.1f}/100")
        print(f"   VERDICT: {score_result.verdict.value}")
        print(f"   FLAGS: {len(score_result.flags)}")
        
        # Verify expected verdict
        expected_verdict = company_info['expected_verdict']
        if score_result.verdict != expected_verdict:
            print(f"⚠️  Verdict mismatch! Expected: {expected_verdict.value}, Got: {score_result.verdict.value}")
        else:
            print(f"✅ Verdict matches expected: {score_result.verdict.value}")
        
        # Step 6: Create cache data structure
        cache_data = {
            "company_data": company_data.to_dict(),
            "score_result": score_result.to_dict()
        }
        
        # Step 7: Save to cache file
        cache_dir = Path("demo_cache")
        cache_dir.mkdir(exist_ok=True)
        
        cache_file = cache_dir / f"{company_key.lower().replace('&', '').replace(' ', '')}_cache.json"
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Cache saved to {cache_file}")
        print(f"   File size: {cache_file.stat().st_size / 1024:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating cache for {company_info['company_name']}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Generate demo cache for all companies"""
    print("🚀 INTELLI-CREDIT DEMO CACHE GENERATOR")
    print("=" * 60)
    
    # Check environment
    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not found in environment")
        return False
    
    print("✅ Environment check passed")
    
    # Generate cache for each company
    success_count = 0
    total_companies = len(DEMO_COMPANIES)
    
    for company_key, company_info in DEMO_COMPANIES.items():
        success = generate_cache_for_company(company_key, company_info)
        if success:
            success_count += 1
    
    # Final summary
    print(f"\n{'='*60}")
    print("DEMO CACHE GENERATION SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successfully generated: {success_count}/{total_companies} companies")
    
    if success_count == total_companies:
        print("🎉 ALL DEMO CACHES GENERATED SUCCESSFULLY!")
        print("\nGenerated files:")
        cache_dir = Path("demo_cache")
        for cache_file in cache_dir.glob("*_cache.json"):
            size_kb = cache_file.stat().st_size / 1024
            print(f"   📄 {cache_file.name} ({size_kb:.1f} KB)")
        
        print("\n🎯 Demo mode is now ready!")
        print("   Run: streamlit run app.py")
        print("   Select any demo company from the dropdown")
        
        return True
    else:
        print(f"⚠️  Only {success_count}/{total_companies} caches generated")
        print("   Check errors above and retry")
        return False

if __name__ == "__main__":
    main()