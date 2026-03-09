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

Extract these fields (use null if not found, DO NOT GUESS):
{{
  "total_assets": <float in ₹ Crores or null>,
  "total_liabilities": <float in ₹ Crores or null>,
  "net_worth": <float in ₹ Crores or null>,
  "current_assets": <float in ₹ Crores or null>,
  "current_liabilities": <float in ₹ Crores or null>,
  "total_debt": <float in ₹ Crores or null>,
  "equity": <float in ₹ Crores or null>,
  "year": <int or null, e.g., 2023>
}}

IMPORTANT: Return null for any field not explicitly found in the document. DO NOT GUESS or estimate values.
Return ONLY the JSON object, no other text.
"""
    
    elif document_type == "profit_loss":
        return base_instruction + f"""
Extract financial data from this P&L Statement and return ONLY valid JSON.

Text:
{text}

Extract these fields (use null if not found, DO NOT GUESS):
{{
  "revenue": <float in ₹ Crores or null>,
  "net_profit": <float in ₹ Crores or null>,
  "ebitda": <float in ₹ Crores or null>,
  "interest_expense": <float in ₹ Crores or null>,
  "depreciation": <float in ₹ Crores or null>,
  "tax": <float in ₹ Crores or null>,
  "year": <int or null, e.g., 2023>
}}

IMPORTANT: Return null for any field not explicitly found in the document. DO NOT GUESS or estimate values.
Return ONLY the JSON object, no other text.
"""
    
    elif document_type == "bank_statements":
        return base_instruction + f"""
Extract banking data from this Bank Statement and return ONLY valid JSON.

Text:
{text}

Extract these fields (use null if not found, DO NOT GUESS):
{{
  "total_credits_annual": <float in ₹ Crores or null, sum of all credits>,
  "total_debits_annual": <float in ₹ Crores or null, sum of all debits>,
  "cheque_bounces_count": <int or null, number of bounced cheques>,
  "od_limit": <float in ₹ Crores or null, overdraft limit>,
  "od_utilized": <float in ₹ Crores or null, overdraft utilized>,
  "period_start": <string or null, YYYY-MM-DD>,
  "period_end": <string or null, YYYY-MM-DD>
}}

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
  "gst_turnover": <float in ₹ Crores or null, total turnover>,
  "gstr_3b_itc": <float in ₹ Crores or null, ITC claimed in GSTR-3B>,
  "gstr_2a_itc": <float in ₹ Crores or null, ITC available in GSTR-2A>,
  "return_type": <string or null, "GSTR-3B" or "GSTR-2A">,
  "period": <string or null, e.g., "Q4 2023">
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
