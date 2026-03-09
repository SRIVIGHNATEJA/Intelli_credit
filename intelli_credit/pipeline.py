"""
Pipeline Orchestrator - Coordinates all components for credit assessment
Implements demo mode support and real-mode document processing

CRITICAL SAFEGUARDS:
1. Defensive orchestration: Top-level try/except in process_application()
2. Missing document tolerance: Graceful handling in extract_all_documents()
3. Demo cache fallback: FileNotFoundError handling in load_demo_cache()
"""

import os
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

from groq import Groq

from data_models import (
    CompanyData, FinancialData, ResearchResult,
    EarlyWarning, FlagItem
)
from parser import extract_from_pdf
from analyser import cross_check_gst_bank
from researcher import research_company
from detector import scan_for_warnings
from dummy_data import load_demo_cache as load_demo_cache_from_registry


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# DEMO MODE SUPPORT (Task 16.1)
# ============================================================================

def load_demo_cache(company_name: str, cache_dir: str = "demo_cache") -> Optional[tuple]:
    """
    Load demo cache from JSON file.
    
    SAFEGUARD 3: Demo cache fallback - handles FileNotFoundError gracefully,
    returns None to fall back to real mode.
    
    Args:
        company_name: Name of demo company (e.g., "IL&FS", "TCS", "Byju's")
        cache_dir: Directory containing cache files
        
    Returns:
        tuple: (CompanyData, ScoreResult) or None if cache doesn't exist
    """
    try:
        # SAFEGUARD 3: Use the registry function which already has FileNotFoundError handling
        result = load_demo_cache_from_registry(company_name, cache_dir)
        
        if result:
            logger.info(f"✓ Demo cache loaded for {company_name}")
            return result
        else:
            logger.warning(f"Demo cache not found for {company_name}, falling back to real mode")
            return None
            
    except FileNotFoundError as e:
        logger.warning(f"Demo cache file not found: {e}")
        logger.info("Falling back to real-mode execution")
        return None
    except Exception as e:
        logger.error(f"Error loading demo cache: {e}")
        return None


# ============================================================================
# REAL MODE DOCUMENT EXTRACTION (Task 16.2)
# ============================================================================

def extract_all_documents(
    uploaded_files: Dict[str, str],
    groq_client: Optional[Groq] = None
) -> FinancialData:
    """
    Extract data from all uploaded PDFs and build FinancialData object.
    
    SAFEGUARD 2: Missing document tolerance - if a document fails to parse,
    leave corresponding fields as None/default values and continue.
    
    Args:
        uploaded_files: Dict mapping document_type to file_path
        groq_client: Optional Groq client instance
        
    Returns:
        FinancialData object with extracted data (never None)
    """
    logger.info("Starting document extraction...")
    
    # Initialize empty FinancialData
    financials = FinancialData()
    
    # Initialize Groq client if not provided
    if groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            groq_client = Groq(api_key=api_key)
    
    # Extract each document type
    for doc_type, file_path in uploaded_files.items():
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"Skipping {doc_type}: file not found")
            continue
        
        try:
            logger.info(f"Extracting {doc_type}...")
            extracted = extract_from_pdf(file_path, doc_type, groq_client)
            
            if not extracted:
                logger.warning(f"No data extracted from {doc_type}")
                continue
            
            # Map extracted data to FinancialData fields
            _map_extracted_to_financials(financials, doc_type, extracted)
            
        except Exception as e:
            # SAFEGUARD 2: Handle extraction failures gracefully
            logger.error(f"Error extracting {doc_type}: {e}")
            logger.info(f"Continuing with remaining documents...")
            continue
    
    logger.info("Document extraction complete")
    return financials


def _map_extracted_to_financials(
    financials: FinancialData,
    doc_type: str,
    extracted: Dict[str, Any]
) -> None:
    """
    Map extracted data from a document to FinancialData fields.
    
    Args:
        financials: FinancialData object to populate
        doc_type: Type of document (balance_sheet, profit_loss, etc.)
        extracted: Extracted data dictionary
    """
    try:
        if doc_type == "balance_sheet":
            # Balance sheet data
            if "net_worth_history" in extracted:
                financials.net_worth_history = extracted["net_worth_history"]
            if "total_debt" in extracted:
                financials.total_debt = extracted["total_debt"]
            if "current_ratio" in extracted:
                financials.current_ratio = extracted["current_ratio"]
            if "debt_equity_ratio" in extracted:
                financials.debt_equity_ratio = extracted["debt_equity_ratio"]
        
        elif doc_type == "profit_loss":
            # P&L data
            if "revenue_history" in extracted:
                financials.revenue_history = extracted["revenue_history"]
            if "net_profit_history" in extracted:
                financials.net_profit_history = extracted["net_profit_history"]
            if "ebitda" in extracted:
                financials.ebitda = extracted["ebitda"]
            if "interest_coverage" in extracted:
                financials.interest_coverage = extracted["interest_coverage"]
        
        elif doc_type == "bank_statements":
            # Bank statement data
            if "bank_credits_annual" in extracted:
                financials.bank_credits_annual = extracted["bank_credits_annual"]
            if "cheque_bounces_12m" in extracted:
                financials.cheque_bounces_12m = extracted["cheque_bounces_12m"]
            if "od_utilization_pct" in extracted:
                financials.od_utilization_pct = extracted["od_utilization_pct"]
        
        elif doc_type == "gst_returns":
            # GST data
            if "gst_turnover" in extracted:
                financials.gst_turnover = extracted["gst_turnover"]
            if "gstr_3b_itc" in extracted:
                financials.gstr_3b_itc = extracted["gstr_3b_itc"]
            if "gstr_2a_itc" in extracted:
                financials.gstr_2a_itc = extracted["gstr_2a_itc"]
        
        elif doc_type == "itr":
            # ITR data (may overlap with P&L)
            if "revenue_history" in extracted and not financials.revenue_history:
                financials.revenue_history = extracted["revenue_history"]
            if "net_profit_history" in extracted and not financials.net_profit_history:
                financials.net_profit_history = extracted["net_profit_history"]
        
        elif doc_type == "sanction_letter":
            # Sanction letter data
            if "loan_requested" in extracted:
                financials.loan_requested = extracted["loan_requested"]
            if "collateral_value" in extracted:
                financials.collateral_value = extracted["collateral_value"]
            if "collateral_type" in extracted:
                financials.collateral_type = extracted["collateral_type"]
            if "guarantee_type" in extracted:
                financials.guarantee_type = extracted["guarantee_type"]
            if "dscr" in extracted:
                financials.dscr = extracted["dscr"]
        
        # Common fields that may appear in multiple documents
        if "audit_opinion" in extracted:
            financials.audit_opinion = extracted["audit_opinion"]
        if "going_concern_flag" in extracted:
            financials.going_concern_flag = extracted["going_concern_flag"]
        if "nclt_cases" in extracted:
            financials.nclt_cases = extracted["nclt_cases"]
        if "drt_cases" in extracted:
            financials.drt_cases = extracted["drt_cases"]
        if "criminal_cases" in extracted:
            financials.criminal_cases = extracted["criminal_cases"]
        if "promoter_contribution_pct" in extracted:
            financials.promoter_contribution_pct = extracted["promoter_contribution_pct"]
        if "promoter_pledge_pct" in extracted:
            financials.promoter_pledge_pct = extracted["promoter_pledge_pct"]
        
    except Exception as e:
        logger.error(f"Error mapping {doc_type} data: {e}")


# ============================================================================
# ANALYSIS PIPELINE (Task 16.3)
# ============================================================================

def run_analysis_pipeline(
    company_data: CompanyData,
    gst_data: Optional[Dict[str, Any]] = None,
    bank_data: Optional[Dict[str, Any]] = None,
    all_extracted_text: Optional[Dict[str, str]] = None
) -> CompanyData:
    """
    Run analysis pipeline: GST cross-check, research, early warning detection.
    
    Args:
        company_data: CompanyData object with financials
        gst_data: Optional detailed GST data
        bank_data: Optional detailed bank data
        all_extracted_text: Optional dict of document_name -> text for warning detection
        
    Returns:
        Updated CompanyData object with research and warnings
    """
    logger.info("Starting analysis pipeline...")
    
    # 1. GST-Bank cross-check (if data available)
    if company_data.financials:
        try:
            logger.info("Running GST-Bank cross-check...")
            gst_flags = cross_check_gst_bank(
                financials=company_data.financials,
                gst_data=gst_data,
                bank_data=bank_data
            )
            
            if gst_flags:
                logger.info(f"Found {len(gst_flags)} GST fraud flags")
                # GST flags will be picked up by scorer from financials
            else:
                logger.info("No GST fraud flags detected")
                
        except Exception as e:
            logger.error(f"GST analysis error: {e}")
            logger.info("Continuing with neutral GST assessment...")
    
    # 2. Web research
    try:
        logger.info("Researching company...")
        research_result = research_company(
            cin=company_data.cin,
            company_name=company_data.company_name,
            description=""
        )
        company_data.research = research_result
        logger.info("Research complete")
        
    except Exception as e:
        logger.error(f"Research error: {e}")
        logger.info("Continuing with neutral research data...")
        company_data.research = ResearchResult()
    
    # 3. Early warning detection
    if all_extracted_text:
        try:
            logger.info("Scanning for early warnings...")
            all_warnings: List[EarlyWarning] = []
            
            for doc_name, text in all_extracted_text.items():
                if text:
                    warnings = scan_for_warnings(text, doc_name)
                    all_warnings.extend(warnings)
            
            company_data.early_warnings = all_warnings
            
            if all_warnings:
                logger.info(f"Found {len(all_warnings)} early warning signals")
            else:
                logger.info("No early warnings detected")
                
        except Exception as e:
            logger.error(f"Early warning detection error: {e}")
            logger.info("Continuing without early warnings...")
            company_data.early_warnings = []
    
    logger.info("Analysis pipeline complete")
    return company_data


# ============================================================================
# MASTER PROCESS FUNCTION (Task 16.4)
# ============================================================================

def process_application(
    cin: str,
    company_name: str,
    promoter_name: Optional[str] = None,
    uploaded_files: Optional[Dict[str, str]] = None,
    demo_mode: bool = False,
    demo_company_key: Optional[str] = None
) -> CompanyData:
    """
    Master function to process a credit application.
    
    SAFEGUARD 1: Defensive orchestration - wraps main logic in top-level try/except.
    Returns partial CompanyData instead of crashing on fatal errors.
    
    Args:
        cin: Corporate Identification Number
        company_name: Name of the company
        promoter_name: Optional promoter name
        uploaded_files: Dict mapping document_type to file_path (for real mode)
        demo_mode: If True, load from demo cache
        demo_company_key: Demo company key (e.g., "IL&FS", "TCS", "Byju's")
        
    Returns:
        CompanyData object (never None, may be partial on errors)
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing Application")
    logger.info(f"{'='*60}")
    logger.info(f"CIN: {cin}")
    logger.info(f"Company: {company_name}")
    logger.info(f"Mode: {'DEMO' if demo_mode else 'REAL'}")
    logger.info(f"{'='*60}\n")
    
    # SAFEGUARD 1: Wrap entire logic in try/except
    try:
        # Check demo mode first
        if demo_mode and demo_company_key:
            logger.info(f"Loading demo cache for {demo_company_key}...")
            cache_result = load_demo_cache(demo_company_key)
            
            if cache_result:
                company_data, score_result = cache_result
                logger.info("✓ Demo cache loaded successfully")
                logger.info(f"Verdict: {score_result.verdict.value}")
                logger.info(f"Total Score: {score_result.total_score:.1f}")
                return company_data
            else:
                logger.warning("Demo cache not found, falling back to real mode...")
                # Fall through to real mode
        
        # Real mode processing
        logger.info("Starting real-mode processing...")
        
        # Initialize CompanyData
        company_data = CompanyData(
            cin=cin,
            company_name=company_name,
            promoter_name=promoter_name,
            demo_mode=False
        )
        
        # Validate uploaded files
        if not uploaded_files:
            logger.warning("No files uploaded, creating minimal CompanyData")
            company_data.financials = FinancialData()
            return company_data
        
        # Extract all documents
        financials = extract_all_documents(uploaded_files)
        company_data.financials = financials
        
        # Run analysis pipeline
        company_data = run_analysis_pipeline(
            company_data=company_data,
            gst_data=None,  # Could be passed if available
            bank_data=None,  # Could be passed if available
            all_extracted_text=None  # Could extract text during parsing
        )
        
        logger.info(f"\n{'='*60}")
        logger.info("Processing complete")
        logger.info(f"{'='*60}\n")
        
        return company_data
        
    except Exception as e:
        # SAFEGUARD 1: Fatal error handling - return partial CompanyData
        logger.error(f"FATAL ERROR in process_application: {e}")
        logger.error("Returning partial CompanyData to prevent crash")
        
        import traceback
        traceback.print_exc()
        
        # Return minimal CompanyData
        return CompanyData(
            cin=cin,
            company_name=company_name,
            promoter_name=promoter_name,
            financials=FinancialData(),
            demo_mode=demo_mode
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_uploaded_files(uploaded_files: Dict[str, str]) -> tuple[bool, List[str]]:
    """
    Validate that uploaded files exist and are accessible.
    
    Args:
        uploaded_files: Dict mapping document_type to file_path
        
    Returns:
        tuple: (all_valid, list_of_errors)
    """
    errors = []
    
    for doc_type, file_path in uploaded_files.items():
        if not file_path:
            errors.append(f"{doc_type}: No file provided")
            continue
        
        if not os.path.exists(file_path):
            errors.append(f"{doc_type}: File not found - {file_path}")
            continue
        
        if not os.path.isfile(file_path):
            errors.append(f"{doc_type}: Not a file - {file_path}")
            continue
    
    return (len(errors) == 0, errors)


def get_processing_summary(company_data: CompanyData) -> Dict[str, Any]:
    """
    Generate summary of processing results.
    
    Args:
        company_data: CompanyData object
        
    Returns:
        Dictionary with summary statistics
    """
    summary = {
        "cin": company_data.cin,
        "company_name": company_data.company_name,
        "demo_mode": company_data.demo_mode,
        "has_financials": company_data.financials is not None,
        "has_research": company_data.research is not None,
        "officer_notes_count": len(company_data.officer_notes),
        "early_warnings_count": len(company_data.early_warnings),
    }
    
    if company_data.financials:
        summary["revenue_years"] = len(company_data.financials.revenue_history)
        summary["has_gst_data"] = company_data.financials.gst_turnover is not None
        summary["has_bank_data"] = company_data.financials.bank_credits_annual is not None
    
    if company_data.research:
        summary["news_items_count"] = len(company_data.research.news_items)
        summary["sector"] = company_data.research.sector
        summary["mca_status"] = company_data.research.mca_status
    
    return summary


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    """Test pipeline with demo mode"""
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n" + "="*70)
    print(" "*20 + "PIPELINE TEST - DEMO MODE")
    print("="*70 + "\n")
    
    # Test demo mode
    company_data = process_application(
        cin="L65990MH1987PLC044571",
        company_name="Infrastructure Leasing and Financial Services Limited",
        demo_mode=True,
        demo_company_key="IL&FS"
    )
    
    print("\n" + "="*70)
    print("PROCESSING SUMMARY")
    print("="*70)
    
    summary = get_processing_summary(company_data)
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    print("\n" + "="*70)
    print("Pipeline test complete")
    print("="*70 + "\n")
