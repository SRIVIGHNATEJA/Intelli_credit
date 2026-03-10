"""
Prompts Manager - LLM prompt templates for Intelli-Credit
All prompts enforce strict JSON output and Indian credit context
"""

# ============================================================================
# INDIAN CREDIT CONTEXT
# ============================================================================

INDIAN_CREDIT_CONTEXT = """
You are analyzing financial documents for Indian corporate lending.

Key Indian Financial Terms:
- ₹ Crores = 10 million rupees (₹1 Cr = ₹10,000,000)
- ₹ Lakhs = 100,000 rupees (₹1 L = ₹100,000)
- DSCR = Debt Service Coverage Ratio (EBITDA / Debt Service)
- D/E Ratio = Debt to Equity Ratio
- NCLT = National Company Law Tribunal (insolvency cases)
- DRT = Debt Recovery Tribunal
- MCA = Ministry of Corporate Affairs
- CIN = Corporate Identification Number (21-character unique ID)
- GSTR-2A = GST return showing supplier invoices
- GSTR-3B = GST return showing tax liability and ITC claimed
- ITC = Input Tax Credit
- OD = Overdraft facility
- SEBI = Securities and Exchange Board of India
- ED = Enforcement Directorate
- RBI = Reserve Bank of India
- "Finance Cost" in Indian P&L = Interest Expense
(NOT a separate concept — same thing)
- GSTR-2A is AUTO-POPULATED, never filed by taxpayer
GSTR-2A data will NOT appear in a GSTR-3B document
- All values in ₹ Crores unless document states Lakhs

Document Types:
- Balance Sheet: Assets, liabilities, net worth
- P&L Statement: Revenue, expenses, profit/loss
- Bank Statements: Credits, debits, bounces, OD utilization
- GST Returns: Turnover, ITC, supplier data
- ITR: Income Tax Return
- Sanction Letter: Previous loan approvals

Always extract monetary values in ₹ Crores for consistency.
"""


# ============================================================================
# EXTRACTION PROMPTS
# ============================================================================

def get_extraction_prompt(document_type: str, text: str) -> str:
    """
    Get extraction prompt for specific document type.
    
    Args:
        document_type: One of: balance_sheet, profit_loss, bank_statements, 
                       gst_returns, itr, sanction_letter
        text: Raw text extracted from PDF
        
    Returns:
        str: Complete prompt for Groq API
    """
    
    base_instruction = f"{INDIAN_CREDIT_CONTEXT}\n\n"
    
    if document_type == "balance_sheet":
        return base_instruction + f"""
Extract financial data from this Balance Sheet and return ONLY valid JSON.

Text:
{text}

COMPREHENSIVE INDIAN ACCOUNTING SYNONYMS:

NET WORTH (look for ANY of these terms):
- "Total Equity", "Shareholders Equity", "Shareholders' Equity"
- "Shareholders Funds", "TOTAL SHAREHOLDER EQUITY"
- "Share Capital + Reserves and Surplus"
- "Net Worth", "Owners Equity", "Proprietors Fund"
- "Equity and Liabilities" minus "Total Liabilities"
- "Net Assets", "Book Value", "Tangible Net Worth"

TOTAL DEBT (look for ANY of these terms):
- "Total Borrowings", "Total Debt", "Total Loans"
- "Long Term Borrowings + Short Term Borrowings"
- "Non-Current Borrowings + Current Borrowings"
- "Term Loans + Working Capital Loans"
- "Bank Borrowings + Financial Institution Loans"
- "Secured Loans + Unsecured Loans"

CURRENT ASSETS (look for ANY of these terms):
- "Current Assets", "Liquid Assets", "Short Term Assets"
- "Cash and Cash Equivalents", "Bank Balances"
- "Trade Receivables", "Debtors", "Sundry Debtors"
- "Inventory", "Stock", "Stock in Trade"
- "Short Term Investments", "Marketable Securities"

CURRENT LIABILITIES (look for ANY of these terms):
- "Current Liabilities", "Short Term Liabilities"
- "Trade Payables", "Creditors", "Sundry Creditors"
- "Short Term Borrowings", "Bank Overdraft"
- "Current Maturities of Long Term Debt"
- "Provisions", "Accrued Expenses"

Extract these fields (use null if not found, DO NOT GUESS):
{{
  "total_assets": <float in ₹ Crores or null>,
  "total_liabilities": <float in ₹ Crores or null>,
  "net_worth": <float in ₹ Crores or null>,
  "current_assets": <float in ₹ Crores or null>,
  "current_liabilities": <float in ₹ Crores or null>,
  "long_term_debt": <float in ₹ Crores or null,
look for: Long-term Debt, Long-term Borrowings,
Term Loans, Non-current Borrowings, Debentures.
If document says zero long-term debt return 0.0.
Do NOT include lease liabilities>,
  "short_term_borrowings": <float in ₹ Crores or null,
look for: Short-term Borrowings, Current Borrowings,
Working Capital Loans, Cash Credit, OD limit>,
  "equity": <float in ₹ Crores or null, same as net_worth>,
  "zero_debt_flag": <boolean, true ONLY if document
explicitly states debt-free or zero long-term debt,
false otherwise>,
  "year": <int or null>
}}

VALIDATION RULES:
- total_assets should equal total_liabilities + net_worth (approximately)
- net_worth can be negative (distressed companies)
- All monetary values must be in ₹ Crores (divide by 10,000,000 if in rupees)

IMPORTANT: Return null for any field not explicitly found in the document. DO NOT GUESS or estimate values.
Return ONLY the JSON object, no other text.
"""
    
    elif document_type == "profit_loss":
        return base_instruction + f"""
Extract financial data from this P&L Statement and return ONLY valid JSON.

Text:
{text}

COMPREHENSIVE INDIAN ACCOUNTING SYNONYMS:

REVENUE (look for ANY of these terms):
- "Revenue from Operations", "Total Revenue", "Gross Revenue"
- "Total Income", "Turnover", "Net Sales"
- "Sales", "Income from Operations", "Operating Revenue"
- "Gross Sales", "Net Turnover", "Total Turnover"

FINANCE COST / INTEREST EXPENSE (look for ANY of these terms):
- "Finance Cost", "Finance Costs", "Financial Costs"
- "Interest Expense", "Interest on Borrowings"
- "Borrowing Costs", "Interest on Loans"
- "Financial Expenses", "Interest on Term Loans"
- "Interest on Working Capital", "Bank Interest"
- "Cost of Borrowings", "Debt Service Cost"

NET PROFIT (look for ANY of these terms):
- "Profit After Tax (PAT)", "Net Profit for the Year"
- "Profit After Tax", "Net Profit", "Bottom Line"
- "Profit Attributable to Shareholders"
- "Net Income", "Earnings After Tax"

EBITDA (look for ANY of these terms):
- "EBITDA", "Earnings Before Interest Tax Depreciation Amortization"
- "Operating Profit Before Depreciation"
- "PBIDT", "Profit Before Interest Depreciation Tax"
- "Cash Profit", "Operating Cash Flow"

DEPRECIATION (look for ANY of these terms):
- "Depreciation", "Depreciation and Amortization"
- "Amortization", "Depreciation on Fixed Assets"
- "Wear and Tear", "Asset Write-off"

Extract these fields (use null if not found, DO NOT GUESS):
{{
  "revenue": <float in ₹ Crores or null>,
  "ebit": <float in ₹ Crores or null,
look for: EBIT, Operating Profit,
Profit before Interest and Tax,
Earnings before Interest and Tax>,
  "net_profit": <float in ₹ Crores or null>,
  "ebitda": <float in ₹ Crores or null,
ONLY if explicitly labeled EBITDA.
Do not compute. Return null if not labeled>,
  "finance_cost": <float in ₹ Crores or null,
look for: Finance Cost, Finance Costs,
Interest Expense, Interest on Borrowings,
Borrowing Costs, Financial Expenses.
NOTE: "Finance Cost" IS interest expense in India>,
  "depreciation": <float in ₹ Crores or null>,
  "tax": <float in ₹ Crores or null>,
  "year": <int or null>
}}

VALIDATION RULES:
- Revenue should be positive (unless loss-making)
- Net profit can be negative (loss)
- All monetary values must be in ₹ Crores

IMPORTANT: Return null for any field not explicitly found in the document. DO NOT GUESS or estimate values.
Return ONLY the JSON object, no other text.
"""
    
    elif document_type == "bank_statements":
        return base_instruction + f"""
Extract banking data from this Bank Statement and return ONLY valid JSON.

Text:
{text}

COMPREHENSIVE INDIAN BANKING SYNONYMS:

CREDITS / INFLOWS (look for ANY of these terms):
- "Credit", "CR", "Deposit", "Credit Entry"
- "Inward Remittance", "Collection", "Receipt"
- "NEFT Credit", "RTGS Credit", "IMPS Credit"
- "Cheque Deposit", "Cash Deposit", "Transfer In"
- "Revenue Collection", "Customer Payment"

DEBITS / OUTFLOWS (look for ANY of these terms):
- "Debit", "DR", "Withdrawal", "Debit Entry"
- "Outward Remittance", "Payment", "Transfer Out"
- "NEFT Debit", "RTGS Debit", "IMPS Debit"
- "Cheque Payment", "Cash Withdrawal", "ECS Debit"
- "Salary Payment", "Vendor Payment", "EMI Debit"

CHEQUE BOUNCES (look for ANY of these terms):
- "Cheque Return", "Cheque Bounce", "Cheque Dishonour"
- "Insufficient Funds", "Payment Failed", "Return Unpaid"
- "Refer to Drawer", "Account Closed", "Stop Payment"
- "Signature Mismatch", "Post Dated", "Funds Insufficient"

OVERDRAFT (look for ANY of these terms):
- "Overdraft", "OD", "Cash Credit", "CC"
- "Drawing Power", "Sanctioned Limit", "Credit Limit"
- "Overdrawn", "Negative Balance", "Debit Balance"

Extract these fields (use null if not found, DO NOT GUESS):
{{
  "period_start": <string or null, YYYY-MM-DD>,
  "period_end": <string or null, YYYY-MM-DD>,
  "period_months": <int or null,
count months this statement covers.
Jan-Mar = 3, full year = 12, one month = 1.
This is required for annualisation>,
  "total_credits_in_period": <float in ₹ Crores or null,
CRITICAL: NEVER PERFORM ARITHMETIC. NEVER use the '+' sign. If a summary total is missing and you see multiple individual entries, return them strictly as a JSON list of floats (e.g., [100.0, 50.0]). Python will do the math.>,
  "total_debits_in_period": <float in ₹ Crores or null,
CRITICAL: NEVER PERFORM ARITHMETIC. NEVER use the '+' sign. If a summary total is missing and you see multiple individual entries, return them strictly as a JSON list of floats (e.g., [100.0, 50.0]). Python will do the math.>,
  "cheque_bounces_count": <int or null,
return 0 if explicitly stated as 0 or NIL.
return null if not mentioned at all.
do NOT infer from conduct remarks>,
  "od_limit": <float in ₹ Crores or null>,
  "od_utilized": <float in ₹ Crores or null>,
  "account_conduct": <string or null,
any explicit conduct rating mentioned>
}}

VALIDATION RULES:
- total_credits and total_debits should be similar in magnitude for operating companies
- cheque_bounces_count should be a small integer (0-10 typically)
- od_utilized should be <= od_limit

IMPORTANT: Return null for any field not explicitly found in the document. DO NOT GUESS or estimate values.
Return ONLY the JSON object, no other text.
"""
    
    elif document_type == "gst_returns":
        return base_instruction + f"""
Extract GST data from this GST Return and return ONLY valid JSON.

Text:
{text}

Extract these fields (use null if not found, DO NOT GUESS):
{{
  "return_type": <string or null,
"GSTR-3B" or "GSTR-1" or "GSTR-9" or "GSTR-2A">,
  "gstin": <string or null, 15-character GSTIN>,
  "period_months": <int or null,
GSTR-3B monthly = 1,
GSTR-9 annual = 12,
quarterly = 3>,
  "gst_turnover_period": <float in ₹ Crores or null,
CRITICAL: Identify "TOTAL SUPPLIES" or "Total Taxable Value".
Extract the sum of all outward taxable supplies (Domestic + Zero Rated)
from table 1. CRITICAL: NEVER PERFORM ARITHMETIC. NEVER use the '+' sign. If a summary total is missing and you see multiple individual entries, return them strictly as a JSON list of floats (e.g., [100.0, 50.0]). Python will do the math.>,
  "gstr_3b_itc": <float in ₹ Crores or null,
NET ITC after reversals.
Sum of IGST + CGST + SGST net ITC.
Only present in GSTR-3B documents>,
  "gstr_2a_itc": <float in ₹ Crores or null,
CRITICAL: GSTR-2A data NEVER appears in
a GSTR-3B document. They are different returns.
Set null for GSTR-3B. Only set if document
IS actually a GSTR-2A>,
  "filing_status": <string or null,
"FILED", "PENDING", or "LATE">,
  "period": <string or null, e.g., "March 2025">
}}

IMPORTANT: Return null for any field not explicitly found in the document. DO NOT GUESS or estimate values.
Return ONLY the JSON object, no other text.
"""
    
    elif document_type == "itr":
        return base_instruction + f"""
Extract income tax data from this ITR and return ONLY valid JSON.

Text:
{text}

Extract these fields (use null if not found, DO NOT GUESS):
{{
  "gross_total_income": <float in ₹ Crores or null>,
  "total_tax_paid": <float in ₹ Crores or null>,
  "assessment_year": <string or null, e.g., "2023-24">,
  "filing_date": <string or null, YYYY-MM-DD>
}}

IMPORTANT: Return null for any field not explicitly found in the document. DO NOT GUESS or estimate values.
Return ONLY the JSON object, no other text.
"""
    
    elif document_type == "sanction_letter":
        return base_instruction + f"""
Extract loan sanction details from this Sanction Letter and return ONLY valid JSON.

Text:
{text}

Extract these fields (use null if not found, DO NOT GUESS):
{{
  "sanctioned_amount": <float in ₹ Crores or null>,
  "interest_rate": <float or null, percentage>,
  "tenure_months": <int or null>,
  "sanction_date": <string or null, YYYY-MM-DD>,
  "lender_name": <string or null>
}}

IMPORTANT: Return null for any field not explicitly found in the document. DO NOT GUESS or estimate values.
Return ONLY the JSON object, no other text.
"""
    
    else:
        # Generic extraction
        return base_instruction + f"""
Extract relevant financial data from this document and return ONLY valid JSON.

Text:
{text}

Return a JSON object with any relevant financial fields you can extract.
Use null for missing values. DO NOT GUESS or estimate. Convert all monetary values to ₹ Crores.

IMPORTANT: Return null for any field not explicitly found in the document. DO NOT GUESS or estimate values.
Return ONLY the JSON object, no other text.
"""


# ============================================================================
# VALIDATION PROMPT
# ============================================================================

def get_validation_prompt(extracted_data: dict) -> str:
    """
    Get prompt to validate extracted financial data.
    
    Args:
        extracted_data: Dictionary of extracted financial data
        
    Returns:
        str: Validation prompt
    """
    return f"""{INDIAN_CREDIT_CONTEXT}

Validate this extracted financial data for consistency and reasonableness.

Data:
{extracted_data}

Check for:
1. Negative values where they shouldn't be (assets, revenue, etc.)
2. Unreasonable ratios (e.g., D/E > 50, DSCR < 0)
3. Missing critical fields
4. Inconsistent units (all should be ₹ Crores)

Return ONLY valid JSON:
{{
  "is_valid": <boolean>,
  "errors": [<list of error strings>],
  "warnings": [<list of warning strings>]
}}

Return ONLY the JSON object, no other text.
"""


# ============================================================================
# SECTOR CLASSIFICATION PROMPT
# ============================================================================

def get_sector_classification_prompt(company_name: str, description: str = "") -> str:
    """
    Get prompt to classify company sector (ONE WORD output).
    
    Args:
        company_name: Name of the company
        description: Optional company description
        
    Returns:
        str: Sector classification prompt
    """
    return f"""{INDIAN_CREDIT_CONTEXT}

Classify the sector for this company. Return ONLY ONE WORD from this list:
- Manufacturing
- IT
- NBFC
- Infrastructure
- FMCG
- RealEstate
- Telecom
- Banking
- Pharma
- Retail
- Construction
- Education

Company: {company_name}
{f"Description: {description}" if description else ""}

Return ONLY ONE WORD from the list above, nothing else.
"""


def get_sector_outlook_prompt(sector: str, news_context: str) -> str:
    """
    Get prompt to classify sector outlook (ONE WORD output).
    
    Args:
        sector: Sector name
        news_context: Recent news about the sector/company
        
    Returns:
        str: Sector outlook prompt
    """
    return f"""{INDIAN_CREDIT_CONTEXT}

Based on recent news, classify the outlook for the {sector} sector.
Return ONLY ONE WORD from this list:
- GROWING
- STABLE
- DECLINING
- DISTRESSED

News context:
{news_context}

Return ONLY ONE WORD from the list above, nothing else.
"""


# ============================================================================
# OCR CLEANUP PROMPT
# ============================================================================

def get_ocr_cleanup_prompt(ocr_text: str) -> str:
    """
    Get prompt to clean OCR artifacts and structure data.
    
    Args:
        ocr_text: Raw OCR text with potential artifacts
        
    Returns:
        str: OCR cleanup prompt
    """
    return f"""{INDIAN_CREDIT_CONTEXT}

This text was extracted using OCR and may contain artifacts (misread characters, 
formatting issues, etc.). Clean it up and extract structured financial data.

OCR Text:
{ocr_text}

Tasks:
1. Fix common OCR errors (0→O, 1→l, 5→S, etc.)
2. Identify the document type (Balance Sheet, P&L, Bank Statement, GST Return, ITR, Sanction Letter)
3. Extract key financial figures in ₹ Crores

Return ONLY valid JSON:
{{
  "document_type": <string>,
  "cleaned_text": <string, corrected text>,
  "extracted_data": {{<key financial fields as key-value pairs>}}
}}

Return ONLY the JSON object, no other text.
"""


# ============================================================================
# OFFICER NOTE PARSING PROMPT
# ============================================================================

def get_officer_note_parsing_prompt(note_text: str) -> str:
    """
    Get prompt to parse officer note into structured adjustment.
    
    Args:
        note_text: Free-text note from credit officer
        
    Returns:
        str: Officer note parsing prompt
    """
    return f"""{INDIAN_CREDIT_CONTEXT}

Parse this credit officer's note and determine:
1. Which of the Five Cs it affects (CHARACTER, CAPACITY, CAPITAL, COLLATERAL, CONDITIONS)
2. Whether it's positive or negative
3. Suggested score adjustment (-25 to +10)

Officer Note:
{note_text}

Return ONLY valid JSON:
{{
  "affected_c": <string, one of: CHARACTER, CAPACITY, CAPITAL, COLLATERAL, CONDITIONS>,
  "sentiment": <string, "positive" or "negative">,
  "adjustment": <float, between -25 and +10>,
  "reasoning": <string, brief explanation>
}}

Return ONLY the JSON object, no other text.
"""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def enforce_json_output(prompt: str) -> str:
    """
    Add strict JSON enforcement to any prompt.
    
    Args:
        prompt: Base prompt
        
    Returns:
        str: Prompt with JSON enforcement
    """
    return prompt + "\n\nIMPORTANT: Return ONLY valid JSON. No markdown, no explanations, no other text."


def get_system_message() -> str:
    """
    Get system message for Groq API calls.
    
    Returns:
        str: System message
    """
    return """You are a financial data extraction assistant for Indian corporate lending. 
You ALWAYS return valid JSON and nothing else. You understand Indian financial terminology 
and convert all monetary values to ₹ Crores for consistency."""
