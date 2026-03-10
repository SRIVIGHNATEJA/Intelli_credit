"""
Data Models - Core dataclasses for Intelli-Credit system
All data structures used throughout the application
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class Severity(str, Enum):
    """Flag severity levels"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    GREEN = "GREEN"  # Positive flag


class Verdict(str, Enum):
    """Credit decision verdicts"""
    APPROVE = "APPROVE"
    CONDITIONAL = "CONDITIONAL"
    REJECT = "REJECT"


class FlagCategory(str, Enum):
    """Categories for flags"""
    CHARACTER = "CHARACTER"
    CAPACITY = "CAPACITY"
    CAPITAL = "CAPITAL"
    COLLATERAL = "COLLATERAL"
    CONDITIONS = "CONDITIONS"
    GST_FRAUD = "GST_FRAUD"
    EARLY_WARNING = "EARLY_WARNING"


# ============================================================================
# FLAG AND WARNING MODELS
# ============================================================================

@dataclass
class FlagItem:
    """
    Individual flag/deduction in credit scoring.
    Every flag must have a source for auditability.
    """
    category: FlagCategory
    severity: Severity
    description: str
    source: str  # e.g., "GST Filing 2023", "Bank Statement Q4", "MCA Portal"
    impact_score: float  # Numerical impact on score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "description": self.description,
            "source": self.source,
            "impact_score": self.impact_score
        }


@dataclass
class EarlyWarning:
    """
    Early warning signal detected in documents.
    """
    signal_type: str  # e.g., "NCLT", "GOING_CONCERN", "PAYMENT_DEFAULT"
    matched_text: str  # Actual text that triggered the warning
    severity: Severity
    source_document: str  # Which document contained the signal
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "signal_type": self.signal_type,
            "matched_text": self.matched_text,
            "severity": self.severity.value,
            "source_document": self.source_document
        }


# ============================================================================
# FINANCIAL DATA MODELS
# ============================================================================

@dataclass
class FinancialData:
    """
    Complete financial data extracted from documents.
    All monetary values in ₹ Crores unless specified.
    """
    # Revenue and profitability
    revenue: List[float] = field(default_factory=list)  # Last 3 years [current, -1, -2]
    net_profit: List[float] = field(default_factory=list)
    ebitda: Optional[float] = None
    finance_cost: Optional[float] = None
    
    # Debt servicing
    dscr: Optional[float] = None  # Debt Service Coverage Ratio
    interest_coverage: Optional[float] = None
    total_debt: Optional[float] = None
    long_term_debt: Optional[float] = None
    short_term_borrowings: Optional[float] = None
    
    # Balance sheet
    net_worth: List[float] = field(default_factory=list)  # Last 3 years
    current_ratio: Optional[float] = None
    debt_equity_ratio: Optional[float] = None
    
    # Promoter details
    promoter_contribution_pct: Optional[float] = None  # % of equity
    promoter_pledge_pct: Optional[float] = None  # % of shares pledged
    
    # Banking conduct
    cheque_bounces_count: int = 0
    od_utilization_percent: Optional[float] = None  # Overdraft utilization %
    bank_credits_annual: Optional[float] = None  # Annual bank inflows
    
    # GST data
    gst_turnover_annual: Optional[float] = None
    gstr_3b_itc: Optional[float] = None  # Input Tax Credit claimed
    gstr_2a_itc: Optional[float] = None  # ITC available
    gst_bank_gap_percent: Optional[float] = None
    
    # Period information
    period_months: Optional[int] = None
    
    # Collateral
    collateral_value: Optional[float] = None
    collateral_type: Optional[str] = None  # "Property", "Machinery", "Inventory", "Receivables"
    guarantee_type: Optional[str] = None  # "Corporate", "Personal", None
    
    # Loan request
    loan_requested: Optional[float] = None
    
    # Audit and compliance
    audit_opinion: Optional[str] = None  # "Clean", "Qualified", "Adverse", "Disclaimer"
    going_concern_flag: bool = False
    
    # Legal cases
    nclt_cases: int = 0
    drt_cases: int = 0
    criminal_cases: int = 0
    sebi_actions: int = 0
    ed_actions: int = 0
    
    # MCA status
    mca_status: Optional[str] = None  # "Active", "Strike Off", etc.
    din_deactivated: bool = False
    
    # Rating
    credit_rating: Optional[str] = None
    rating_downgrade_months: Optional[int] = None  # Months since last downgrade
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "revenue": self.revenue,
            "net_profit": self.net_profit,
            "ebitda": self.ebitda,
            "finance_cost": self.finance_cost,
            "dscr": self.dscr,
            "interest_coverage": self.interest_coverage,
            "total_debt": self.total_debt,
            "long_term_debt": self.long_term_debt,
            "short_term_borrowings": self.short_term_borrowings,
            "net_worth": self.net_worth,
            "current_ratio": self.current_ratio,
            "debt_equity_ratio": self.debt_equity_ratio,
            "promoter_contribution_pct": self.promoter_contribution_pct,
            "promoter_pledge_pct": self.promoter_pledge_pct,
            "cheque_bounces_count": self.cheque_bounces_count,
            "od_utilization_percent": self.od_utilization_percent,
            "bank_credits_annual": self.bank_credits_annual,
            "gst_turnover_annual": self.gst_turnover_annual,
            "gstr_3b_itc": self.gstr_3b_itc,
            "gstr_2a_itc": self.gstr_2a_itc,
            "gst_bank_gap_percent": self.gst_bank_gap_percent,
            "period_months": self.period_months,
            "collateral_value": self.collateral_value,
            "collateral_type": self.collateral_type,
            "guarantee_type": self.guarantee_type,
            "loan_requested": self.loan_requested,
            "audit_opinion": self.audit_opinion,
            "going_concern_flag": self.going_concern_flag,
            "nclt_cases": self.nclt_cases,
            "drt_cases": self.drt_cases,
            "criminal_cases": self.criminal_cases,
            "sebi_actions": self.sebi_actions,
            "ed_actions": self.ed_actions,
            "mca_status": self.mca_status,
            "din_deactivated": self.din_deactivated,
            "credit_rating": self.credit_rating,
            "rating_downgrade_months": self.rating_downgrade_months
        }


# ============================================================================
# RESEARCH MODELS
# ============================================================================

@dataclass
class NewsItem:
    """Single news article about the company"""
    title: str
    source: str
    date: str
    url: str
    snippet: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "title": self.title,
            "source": self.source,
            "date": self.date,
            "url": self.url,
            "snippet": self.snippet
        }


@dataclass
class StockData:
    """Stock market data for listed companies"""
    ticker: Optional[str] = None
    current_price: Optional[float] = None
    market_cap: Optional[float] = None  # In ₹ Crores
    is_listed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "ticker": self.ticker,
            "current_price": self.current_price,
            "market_cap": self.market_cap,
            "is_listed": self.is_listed
        }


@dataclass
class ResearchResult:
    """
    Web research results for a company.
    """
    sector: Optional[str] = None  # e.g., "IT Services", "Infrastructure Finance"
    sector_outlook: Optional[str] = None  # "GROWING", "STABLE", "DECLINING", "DISTRESSED"
    sector_npa_rate: Optional[float] = None  # % NPA rate for sector
    
    news_items: List[NewsItem] = field(default_factory=list)
    mca_status: Optional[str] = None
    stock_data: Optional[StockData] = None
    
    validation_status: str = "POTENTIAL_MATCH"  # Requires manual validation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "sector": self.sector,
            "sector_outlook": self.sector_outlook,
            "sector_npa_rate": self.sector_npa_rate,
            "news_items": [item.to_dict() for item in self.news_items],
            "mca_status": self.mca_status,
            "stock_data": self.stock_data.to_dict() if self.stock_data else None,
            "validation_status": self.validation_status
        }


# ============================================================================
# OFFICER PORTAL MODELS
# ============================================================================

@dataclass
class OfficerNote:
    """
    Qualitative note from credit officer.
    Can adjust scores within bounded limits.
    """
    note_text: str
    affected_c: FlagCategory  # Which C this note affects
    adjustment: float  # Score adjustment (-25 to +10)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "note_text": self.note_text,
            "affected_c": self.affected_c.value,
            "adjustment": self.adjustment,
            "timestamp": self.timestamp
        }


# ============================================================================
# SCORING MODELS
# ============================================================================

@dataclass
class ScoreResult:
    """
    Complete Five Cs scoring result.
    """
    # Individual C scores (10-100 each)
    character_score: float
    capacity_score: float
    capital_score: float
    collateral_score: float
    conditions_score: float
    
    # Weighted total score (10-100)
    final_score: float
    
    # Verdict
    verdict: Verdict
    loan_amount: Optional[float] = None  # Approved loan amount in ₹ Crores
    interest_rate: Optional[str] = None  # e.g., "12.50% p.a."
    
    # All flags generated during scoring
    flags: List[FlagItem] = field(default_factory=list)
    
    # Human-readable reasoning
    reasoning: str = ""
    
    # Decision narrative (one-sentence summary from top 3 flags)
    decision_narrative: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "character_score": self.character_score,
            "capacity_score": self.capacity_score,
            "capital_score": self.capital_score,
            "collateral_score": self.collateral_score,
            "conditions_score": self.conditions_score,
            "final_score": self.final_score,
            "verdict": self.verdict.value,
            "loan_amount": self.loan_amount,
            "interest_rate": self.interest_rate,
            "flags": [flag.to_dict() for flag in self.flags],
            "reasoning": self.reasoning,
            "decision_narrative": self.decision_narrative
        }


# ============================================================================
# COMPANY DATA MODEL (TOP-LEVEL)
# ============================================================================

@dataclass
class CompanyData:
    """
    Complete company data aggregating all information.
    This is the main data structure passed through the pipeline.
    """
    cin: str
    company_name: str
    promoter_name: Optional[str] = None
    
    financials: Optional[FinancialData] = None
    research: Optional[ResearchResult] = None
    
    officer_notes: List[OfficerNote] = field(default_factory=list)
    early_warnings: List[EarlyWarning] = field(default_factory=list)
    
    # Processing metadata
    processing_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    demo_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "cin": self.cin,
            "company_name": self.company_name,
            "promoter_name": self.promoter_name,
            "financials": self.financials.to_dict() if self.financials else None,
            "research": self.research.to_dict() if self.research else None,
            "officer_notes": [note.to_dict() for note in self.officer_notes],
            "early_warnings": [warning.to_dict() for warning in self.early_warnings],
            "processing_timestamp": self.processing_timestamp,
            "demo_mode": self.demo_mode
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompanyData':
        """Create CompanyData from dictionary (for loading from JSON)"""
        # Reconstruct nested objects
        financials = None
        if data.get("financials"):
            financials = FinancialData(**data["financials"])
        
        research = None
        if data.get("research"):
            research_data = data["research"].copy()
            # Reconstruct news items
            if "news_items" in research_data:
                research_data["news_items"] = [
                    NewsItem(**item) for item in research_data["news_items"]
                ]
            # Reconstruct stock data
            if research_data.get("stock_data"):
                research_data["stock_data"] = StockData(**research_data["stock_data"])
            research = ResearchResult(**research_data)
        
        # Reconstruct officer notes
        officer_notes = []
        if data.get("officer_notes"):
            officer_notes = [
                OfficerNote(
                    note_text=note["note_text"],
                    affected_c=FlagCategory(note["affected_c"]),
                    adjustment=note["adjustment"],
                    timestamp=note["timestamp"]
                )
                for note in data["officer_notes"]
            ]
        
        # Reconstruct early warnings
        early_warnings = []
        if data.get("early_warnings"):
            early_warnings = [
                EarlyWarning(
                    signal_type=warning["signal_type"],
                    matched_text=warning["matched_text"],
                    severity=Severity(warning["severity"]),
                    source_document=warning["source_document"]
                )
                for warning in data["early_warnings"]
            ]
        
        return cls(
            cin=data["cin"],
            company_name=data["company_name"],
            promoter_name=data.get("promoter_name"),
            financials=financials,
            research=research,
            officer_notes=officer_notes,
            early_warnings=early_warnings,
            processing_timestamp=data.get("processing_timestamp", datetime.now().isoformat()),
            demo_mode=data.get("demo_mode", False)
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_flag(
    category: FlagCategory,
    severity: Severity,
    description: str,
    source: str,
    impact: float
) -> FlagItem:
    """Helper function to create a flag with consistent formatting"""
    return FlagItem(
        category=category,
        severity=severity,
        description=description,
        source=source,
        impact_score=impact
    )


def create_early_warning(
    signal_type: str,
    matched_text: str,
    severity: Severity,
    source_document: str
) -> EarlyWarning:
    """Helper function to create an early warning"""
    return EarlyWarning(
        signal_type=signal_type,
        matched_text=matched_text,
        severity=severity,
        source_document=source_document
    )
