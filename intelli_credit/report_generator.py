"""
Report Generator - Generate professional CAM Word documents
Uses python-docx to create formatted Credit Assessment Memorandum documents
"""

from typing import List, Optional, Dict
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

from data_models import (
    CompanyData, ScoreResult, FinancialData, ResearchResult,
    FlagItem, OfficerNote, Severity
)


# ============================================================================
# TASK 12.1: WORD DOCUMENT STRUCTURE FUNCTIONS
# ============================================================================

def format_table(doc: Document, headers: List[str], rows: List[List[str]]) -> None:
    """
    Create a formatted table with headers and data rows.
    
    Args:
        doc: Document object
        headers: List of header strings
        rows: List of row data (each row is a list of strings)
    """
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    try:
        table.style = 'Light Grid Accent 1'
    except KeyError:
        table.style = 'Table Grid'
    
    # Add headers
    header_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        header_cells[i].text = header
        # Bold header text
        for paragraph in header_cells[i].paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(10)
    
    # Add data rows
    for row_idx, row_data in enumerate(rows, start=1):
        cells = table.rows[row_idx].cells
        for col_idx, value in enumerate(row_data):
            cells[col_idx].text = str(value)
            # Set font size
            for paragraph in cells[col_idx].paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)


def format_currency_inr(amount: Optional[float], unit: str = "Crores") -> str:
    if amount is None:
        return "N/A"
    
    if unit == "Lakhs":
        amount = amount * 100
    
    # Indian grouping: last 3, then pairs
    integer_part = str(int(abs(amount)))
    decimal_part = f"{abs(amount) % 1:.2f}"[1:]
    sign = "-" if amount < 0 else ""
    
    n = len(integer_part)
    if n <= 3:
        formatted = integer_part
    else:
        last_three = integer_part[-3:]
        rest = integer_part[:-3]
        
        # Group rest in pairs from right
        pairs = []
        while len(rest) > 2:
            pairs.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            pairs.append(rest)
        pairs.reverse()
        
        formatted = ','.join(pairs) + ',' + last_three
    
    return f"{sign}₹ {formatted}{decimal_part} {unit}"


def add_executive_summary(doc: Document, company_data: CompanyData, score_result: ScoreResult) -> None:
    """
    Add executive summary section with verdict, total score, and key metrics.
    
    Args:
        doc: Document object
        company_data: Company data
        score_result: Scoring results
    """
    doc.add_heading('EXECUTIVE SUMMARY', level=1)
    
    # Verdict box
    verdict_para = doc.add_paragraph()
    verdict_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    verdict_run = verdict_para.add_run(f'CREDIT DECISION: {score_result.verdict.value}')
    verdict_run.font.size = Pt(16)
    verdict_run.font.bold = True
    
    # Color code verdict
    if score_result.verdict.value == "APPROVE":
        verdict_run.font.color.rgb = RGBColor(0, 128, 0)  # Green
    elif score_result.verdict.value == "CONDITIONAL":
        verdict_run.font.color.rgb = RGBColor(255, 140, 0)  # Orange
    else:  # REJECT
        verdict_run.font.color.rgb = RGBColor(255, 0, 0)  # Red
    
    doc.add_paragraph()  # Spacing
    
    # Key metrics table
    key_metrics = [
        ["Total Credit Score", f"{score_result.final_score:.1f}/100"],
        ["Loan Amount Requested", format_currency_inr(company_data.financials.loan_requested if company_data.financials else None)],
        ["Loan Amount Approved", format_currency_inr(score_result.loan_amount)],
        ["Interest Rate", score_result.interest_rate if score_result.interest_rate else "N/A"],
        ["Company Name", company_data.company_name],
        ["CIN", company_data.cin],
        ["Sector", company_data.research.sector if company_data.research else "N/A"]
    ]
    
    format_table(doc, ["Metric", "Value"], key_metrics)
    
    # Decision narrative
    if score_result.decision_narrative:
        doc.add_paragraph()
        doc.add_heading('Decision Summary', level=2)
        doc.add_paragraph(score_result.decision_narrative)


def add_company_overview(doc: Document, company_data: CompanyData) -> None:
    """
    Add company overview section with CIN, name, sector, MCA status.
    
    Args:
        doc: Document object
        company_data: Company data
    """
    doc.add_page_break()
    doc.add_heading('COMPANY OVERVIEW', level=1)
    
    overview_data = [
        ["Company Name", company_data.company_name],
        ["CIN", company_data.cin],
        ["Promoter Name", company_data.promoter_name if company_data.promoter_name else "N/A"],
        ["Sector", company_data.research.sector if company_data.research else "N/A"],
        ["MCA Status", company_data.financials.mca_status if company_data.financials and company_data.financials.mca_status else "N/A"],
        ["Listed Status", "Yes" if company_data.research and company_data.research.stock_data and company_data.research.stock_data.is_listed else "No"]
    ]
    
    if company_data.research and company_data.research.stock_data and company_data.research.stock_data.is_listed:
        overview_data.append(["Stock Ticker", company_data.research.stock_data.ticker or "N/A"])
        overview_data.append(["Market Cap", format_currency_inr(company_data.research.stock_data.market_cap)])
    
    format_table(doc, ["Field", "Value"], overview_data)


# ============================================================================
# TASK 12.2: FINANCIAL ANALYSIS SECTION
# ============================================================================

def add_financial_analysis(doc: Document, financials: Optional[FinancialData]) -> None:
    """
    Add financial analysis section with tables and ratios.
    
    Args:
        doc: Document object
        financials: Financial data
    """
    doc.add_page_break()
    doc.add_heading('FINANCIAL ANALYSIS', level=1)
    
    if not financials:
        doc.add_paragraph("Financial data not available.")
        return
    
    # Revenue and profitability
    doc.add_heading('Revenue and Profitability', level=2)
    
    revenue_rows = []
    if financials.revenue and len(financials.revenue) >= 3:
        revenue_rows.append(["Revenue (Current Year)", format_currency_inr(financials.revenue[0])])
        revenue_rows.append(["Revenue (Year -1)", format_currency_inr(financials.revenue[1])])
        revenue_rows.append(["Revenue (Year -2)", format_currency_inr(financials.revenue[2])])
    
    if financials.net_profit and len(financials.net_profit) >= 3:
        revenue_rows.append(["Net Profit (Current Year)", format_currency_inr(financials.net_profit[0])])
        revenue_rows.append(["Net Profit (Year -1)", format_currency_inr(financials.net_profit[1])])
        revenue_rows.append(["Net Profit (Year -2)", format_currency_inr(financials.net_profit[2])])
    
    if financials.ebitda is not None:
        revenue_rows.append(["EBITDA", format_currency_inr(financials.ebitda)])
    
    if revenue_rows:
        format_table(doc, ["Metric", "Value"], revenue_rows)
    
    # Key financial ratios
    doc.add_heading('Key Financial Ratios', level=2)
    
    ratio_rows = [
        ["DSCR (Debt Service Coverage Ratio)", f"{financials.dscr:.2f}" if financials.dscr is not None else "N/A"],
        ["Debt/Equity Ratio", f"{financials.debt_equity_ratio:.2f}" if financials.debt_equity_ratio is not None else "N/A"],
        ["Current Ratio", f"{financials.current_ratio:.2f}" if financials.current_ratio is not None else "N/A"],
        ["Interest Coverage Ratio", f"{financials.interest_coverage:.2f}" if financials.interest_coverage is not None else "N/A"],
        ["Total Debt", format_currency_inr(financials.total_debt)]
    ]
    
    if financials.net_worth and len(financials.net_worth) > 0:
        ratio_rows.append(["Net Worth (Current)", format_currency_inr(financials.net_worth[0])])
    
    format_table(doc, ["Ratio", "Value"], ratio_rows)
    
    # Banking conduct
    doc.add_heading('Banking Conduct', level=2)
    
    banking_rows = [
        ["Cheque Bounces (12 months)", str(financials.cheque_bounces_count)],
        ["OD Utilization", f"{financials.od_utilization_percent:.1f}%" if financials.od_utilization_percent is not None else "N/A"],
        ["Annual Bank Credits", format_currency_inr(financials.bank_credits_annual)]
    ]
    
    format_table(doc, ["Metric", "Value"], banking_rows)
    
    # Promoter details
    doc.add_heading('Promoter Details', level=2)
    
    promoter_rows = [
        ["Promoter Contribution", f"{financials.promoter_contribution_pct:.1f}%" if financials.promoter_contribution_pct is not None else "N/A"],
        ["Promoter Pledge", f"{financials.promoter_pledge_pct:.1f}%" if financials.promoter_pledge_pct is not None else "N/A"]
    ]
    
    format_table(doc, ["Metric", "Value"], promoter_rows)


# ============================================================================
# TASK 12.3: FIVE Cs BREAKDOWN SECTION
# ============================================================================

def add_five_cs_breakdown(doc: Document, score_result: ScoreResult) -> None:
    """
    Add Five Cs breakdown with score table and flag details.
    
    Args:
        doc: Document object
        score_result: Scoring results
    """
    doc.add_page_break()
    doc.add_heading('FIVE Cs CREDIT ASSESSMENT', level=1)
    
    # Score summary table
    doc.add_heading('Score Summary', level=2)
    
    score_rows = [
        ["CHARACTER", f"{score_result.character_score:.1f}", "25%", f"{score_result.character_score * 0.25:.1f}"],
        ["CAPACITY", f"{score_result.capacity_score:.1f}", "30%", f"{score_result.capacity_score * 0.30:.1f}"],
        ["CAPITAL", f"{score_result.capital_score:.1f}", "20%", f"{score_result.capital_score * 0.20:.1f}"],
        ["COLLATERAL", f"{score_result.collateral_score:.1f}", "15%", f"{score_result.collateral_score * 0.15:.1f}"],
        ["CONDITIONS", f"{score_result.conditions_score:.1f}", "10%", f"{score_result.conditions_score * 0.10:.1f}"],
        ["TOTAL WEIGHTED SCORE", "", "", f"{score_result.final_score:.1f}"]
    ]
    
    format_table(doc, ["Category", "Score (/100)", "Weight", "Weighted Score"], score_rows)
    
    # Flags by category
    doc.add_heading('Detailed Findings and Flags', level=2)
    
    # Group flags by category
    flags_by_category: Dict[str, List[FlagItem]] = {}
    for flag in score_result.flags:
        category = flag.category.value
        if category not in flags_by_category:
            flags_by_category[category] = []
        flags_by_category[category].append(flag)
    
    # Display flags for each category
    for category in ["CHARACTER", "CAPACITY", "CAPITAL", "COLLATERAL", "CONDITIONS", "GST_FRAUD", "EARLY_WARNING"]:
        if category in flags_by_category:
            doc.add_heading(f'{category} Flags', level=3)
            
            flag_rows = []
            for flag in flags_by_category[category]:
                flag_rows.append([
                    flag.severity.value,
                    flag.description,
                    flag.source,
                    f"{flag.impact_score:.1f}"
                ])
            
            format_table(doc, ["Severity", "Description", "Source", "Impact"], flag_rows)
            doc.add_paragraph()  # Spacing


# ============================================================================
# TASK 12.4: SUPPORTING SECTIONS
# ============================================================================

def add_gst_analysis(doc: Document, score_result: ScoreResult) -> None:
    """
    Add GST fraud analysis section.
    
    Args:
        doc: Document object
        score_result: Scoring results (contains GST flags)
    """
    doc.add_page_break()
    doc.add_heading('GST FRAUD ANALYSIS', level=1)
    
    # Extract GST-related flags
    gst_flags = [flag for flag in score_result.flags if flag.category.value == "GST_FRAUD"]
    
    if not gst_flags:
        doc.add_paragraph("No GST fraud indicators detected.")
        return
    
    doc.add_paragraph("The following GST fraud patterns were detected through cross-checking GST returns with bank statements:")
    doc.add_paragraph()
    
    gst_rows = []
    for flag in gst_flags:
        gst_rows.append([
            flag.severity.value,
            flag.description,
            flag.source,
            f"{flag.impact_score:.1f}"
        ])
    
    format_table(doc, ["Severity", "Finding", "Source", "Impact"], gst_rows)


def add_research_findings(doc: Document, research: Optional[ResearchResult]) -> None:
    """
    Add research findings section with news, MCA status, stock data.
    
    Args:
        doc: Document object
        research: Research results
    """
    doc.add_page_break()
    doc.add_heading('RESEARCH FINDINGS', level=1)
    
    if not research:
        doc.add_paragraph("Research data not available.")
        return
    
    # Sector analysis
    doc.add_heading('Sector Analysis', level=2)
    
    sector_rows = [
        ["Sector", research.sector or "N/A"],
        ["Sector Outlook", research.sector_outlook or "N/A"],
        ["Sector NPA Rate", f"{research.sector_npa_rate:.1f}%" if research.sector_npa_rate is not None else "N/A"]
    ]
    
    format_table(doc, ["Field", "Value"], sector_rows)
    
    # MCA status
    doc.add_heading('MCA Status', level=2)
    doc.add_paragraph(f"MCA Status: {research.mca_status or 'N/A'}")
    
    # Stock data
    if research.stock_data and research.stock_data.is_listed:
        doc.add_heading('Stock Market Data', level=2)
        
        stock_rows = [
            ["Ticker", research.stock_data.ticker or "N/A"],
            ["Current Price", f"₹ {research.stock_data.current_price:,.2f}" if research.stock_data.current_price else "N/A"],
            ["Market Cap", format_currency_inr(research.stock_data.market_cap)]
        ]
        
        format_table(doc, ["Field", "Value"], stock_rows)
    
    # News items
    if research.news_items:
        doc.add_heading('Recent News', level=2)
        
        news_rows = []
        for news in research.news_items[:10]:  # Limit to 10 news items
            news_rows.append([
                news.title,
                news.source,
                news.date
            ])
        
        format_table(doc, ["Title", "Source", "Date"], news_rows)


def add_officer_notes(doc: Document, notes: List[OfficerNote]) -> None:
    """
    Add officer notes section with qualitative assessments.
    
    Args:
        doc: Document object
        notes: List of officer notes
    """
    doc.add_page_break()
    doc.add_heading('OFFICER QUALITATIVE ASSESSMENTS', level=1)
    
    if not notes:
        doc.add_paragraph("No officer notes recorded.")
        return
    
    doc.add_paragraph("The following qualitative assessments were made by the credit officer:")
    doc.add_paragraph()
    
    note_rows = []
    for note in notes:
        note_rows.append([
            note.affected_c.value,
            note.note_text,
            f"{note.adjustment:+.1f}",
            note.timestamp[:10]  # Date only
        ])
    
    format_table(doc, ["Affected Category", "Note", "Adjustment", "Date"], note_rows)


def generate_decision_narrative(flags: List[FlagItem], verdict: str) -> str:
    """
    Generate one-sentence decision narrative from top 3 highest-impact flags.
    
    Args:
        flags: All flags from scoring
        verdict: Credit decision verdict
        
    Returns:
        str: Decision narrative
    """
    if not flags:
        return f"{verdict}: No significant risk factors identified."
    
    # Sort flags by absolute impact (highest first)
    sorted_flags = sorted(flags, key=lambda f: abs(f.impact_score), reverse=True)
    
    # Get top 3 flags
    top_flags = sorted_flags[:3]
    
    # Verdict-appropriate conclusion
    if verdict == "APPROVE":
        conclusion = "are within acceptable credit parameters."
    elif verdict == "CONDITIONAL":
        conclusion = "warrant conditional approval with monitoring."
    else:
        conclusion = "indicate significant credit risk."
    
    if len(top_flags) == 0:
        return f"{verdict}: No significant risk factors identified."
    elif len(top_flags) == 1:
        return f"{verdict}: {top_flags[0].description} (impact: {top_flags[0].impact_score:.1f}) — {conclusion}"
    elif len(top_flags) == 2:
        return f"{verdict}: {top_flags[0].description} (impact: {top_flags[0].impact_score:.1f}) combined with {top_flags[1].description} — {conclusion}"
    else:
        return f"{verdict}: {top_flags[0].description} (impact: {top_flags[0].impact_score:.1f}) combined with {top_flags[1].description} and {top_flags[2].description} — {conclusion}"


def add_recommendation(doc: Document, score_result: ScoreResult) -> None:
    """
    Add final recommendation section with verdict, loan terms, and decision narrative.
    
    Args:
        doc: Document object
        score_result: Scoring results
    """
    doc.add_page_break()
    doc.add_heading('FINAL RECOMMENDATION', level=1)
    
    # Verdict
    verdict_para = doc.add_paragraph()
    verdict_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    verdict_run = verdict_para.add_run(f'RECOMMENDATION: {score_result.verdict.value}')
    verdict_run.font.size = Pt(14)
    verdict_run.font.bold = True
    
    # Color code
    if score_result.verdict.value == "APPROVE":
        verdict_run.font.color.rgb = RGBColor(0, 128, 0)
    elif score_result.verdict.value == "CONDITIONAL":
        verdict_run.font.color.rgb = RGBColor(255, 140, 0)
    else:
        verdict_run.font.color.rgb = RGBColor(255, 0, 0)
    
    doc.add_paragraph()
    
    # Loan terms
    doc.add_heading('Loan Terms', level=2)
    
    terms_rows = [
        ["Approved Loan Amount", format_currency_inr(score_result.loan_amount)],
        ["Interest Rate", score_result.interest_rate if score_result.interest_rate else "N/A"],
        ["Total Credit Score", f"{score_result.final_score:.1f}/100"]
    ]
    
    format_table(doc, ["Term", "Value"], terms_rows)
    
    # Decision narrative
    doc.add_heading('Decision Rationale', level=2)
    
    if score_result.decision_narrative:
        doc.add_paragraph(score_result.decision_narrative)
    else:
        # Generate narrative if not already present
        narrative = generate_decision_narrative(score_result.flags, score_result.verdict.value)
        doc.add_paragraph(narrative)
    
    # Reasoning
    if score_result.reasoning:
        doc.add_paragraph()
        doc.add_heading('Detailed Reasoning', level=2)
        doc.add_paragraph(score_result.reasoning)
    
    # Conditions (if CONDITIONAL approval)
    if score_result.verdict.value == "CONDITIONAL":
        doc.add_paragraph()
        doc.add_heading('Conditions for Approval', level=2)
        doc.add_paragraph("The following conditions must be met before loan disbursement:")
        doc.add_paragraph("1. Enhanced collateral coverage to minimum 1.5x", style='List Bullet')
        doc.add_paragraph("2. Personal guarantee from promoters", style='List Bullet')
        doc.add_paragraph("3. Quarterly financial reporting", style='List Bullet')
        doc.add_paragraph("4. Restriction on dividend distribution", style='List Bullet')


# ============================================================================
# TASK 12.5: MASTER GENERATE FUNCTION
# ============================================================================

def generate_cam_word(
    company_data: CompanyData,
    score_result: ScoreResult,
    output_path: str
) -> str:
    """
    Generate complete CAM Word document.
    
    Args:
        company_data: Complete company data
        score_result: Scoring results
        output_path: Path to save the document
        
    Returns:
        str: Path to generated document
    """
    # Create Document object
    doc = Document()
    
    # Set document properties
    doc.core_properties.title = f"Credit Assessment Memorandum - {company_data.company_name}"
    doc.core_properties.author = "Intelli-Credit Engine"
    doc.core_properties.subject = "Credit Assessment"
    
    # Add title page
    title = doc.add_heading('CREDIT ASSESSMENT MEMORANDUM', level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    company_title = doc.add_paragraph()
    company_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    company_run = company_title.add_run(company_data.company_name)
    company_run.font.size = Pt(18)
    company_run.font.bold = True
    
    doc.add_paragraph()
    cin_para = doc.add_paragraph()
    cin_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cin_para.add_run(f"CIN: {company_data.cin}")
    
    doc.add_paragraph()
    date_para = doc.add_paragraph()
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    date_para.add_run(f"Generated: {company_data.processing_timestamp[:10]}")
    
    # Add all sections in order
    add_executive_summary(doc, company_data, score_result)
    add_company_overview(doc, company_data)
    add_financial_analysis(doc, company_data.financials)
    add_five_cs_breakdown(doc, score_result)
    add_gst_analysis(doc, score_result)
    add_research_findings(doc, company_data.research)
    
    if company_data.officer_notes:
        add_officer_notes(doc, company_data.officer_notes)
    
    add_recommendation(doc, score_result)
    
    # Apply consistent styling
    # Set default font for all paragraphs
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            if run.font.size is None:
                run.font.size = Pt(11)
            if run.font.name is None:
                run.font.name = 'Calibri'
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Save document
    doc.save(output_path)
    
    return output_path


# ============================================================================
# HELPER FUNCTION FOR TESTING
# ============================================================================

def test_report_generator():
    """
    Test the report generator with IL&FS data from scorer.py
    """
    from data_models import FinancialData, ResearchResult, CompanyData, NewsItem, StockData
    from scorer import calculate_five_cs
    
    # IL&FS test data (from scorer.py)
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
    
    ilfs_research = ResearchResult(
        sector="Infrastructure Finance",
        sector_outlook="DISTRESSED",
        sector_npa_rate=18.4,
        news_items=[
            NewsItem(
                title="IL&FS Crisis: NCLT admits insolvency proceedings",
                source="Economic Times",
                date="2023-09-15",
                url="https://example.com/news1"
            ),
            NewsItem(
                title="IL&FS defaults on debt obligations",
                source="Business Standard",
                date="2023-08-20",
                url="https://example.com/news2"
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
    
    ilfs_data = CompanyData(
        cin="U65990MH1987PLC042230",
        company_name="IL&FS",
        promoter_name="Ravi Parthasarathy",
        financials=ilfs_financials,
        research=ilfs_research,
        demo_mode=True
    )
    
    # Calculate score
    print("Calculating Five Cs score...")
    score_result = calculate_five_cs(ilfs_data)
    
    # Generate decision narrative
    score_result.decision_narrative = generate_decision_narrative(
        score_result.flags,
        score_result.verdict.value
    )
    
    # Generate CAM document
    output_path = "test_cam_ilfs.docx"
    print(f"Generating CAM document: {output_path}")
    
    generated_path = generate_cam_word(ilfs_data, score_result, output_path)
    
    print(f"\n✅ CAM document generated successfully!")
    print(f"📄 Document saved to: {generated_path}")
    print(f"\nDocument contains:")
    print(f"  - Executive Summary with {score_result.verdict.value} verdict")
    print(f"  - Company Overview")
    print(f"  - Financial Analysis")
    print(f"  - Five Cs Breakdown with {len(score_result.flags)} flags")
    print(f"  - GST Analysis")
    print(f"  - Research Findings with {len(ilfs_research.news_items)} news items")
    print(f"  - Final Recommendation")
    print(f"\nTotal Score: {score_result.final_score:.1f}/100")
    print(f"Verdict: {score_result.verdict.value}")
    
    return generated_path


if __name__ == "__main__":
    # Run test when script is executed directly
    test_report_generator()
