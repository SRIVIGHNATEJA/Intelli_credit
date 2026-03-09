"""
Early Warning Detector - Scan documents for early warning signals
Uses regex pattern matching to detect credit risk indicators
"""

import re
from typing import List, Optional
from data_models import EarlyWarning, Severity, create_early_warning


# ============================================================================
# EARLY WARNING PATTERNS
# ============================================================================

# Patterns ordered by specificity (longer/more specific patterns first)
EARLY_WARNING_PATTERNS = {
    "NCLT": r"\b(?:National Company Law Tribunal|NCLT)\b",
    "DRT": r"\b(?:Debt Recovery Tribunal|DRT)\b",
    "SEBI_ENFORCEMENT": r"\bSEBI\b.*?\b(?:enforcement|penalty|action|proceedings)\b",
    "GOING_CONCERN": r"\b(?:going concern|continue as a going concern|ability to continue as a going concern)\b",
    "CRIMINAL_CASE": r"\b(?:criminal\s*(?:case|proceedings|charges)|FIR|EOW|Economic Offences Wing)\b",
    "AUDIT_QUALIFIED": r"\b(?:qualified opinion|adverse opinion|disclaimer of opinion|qualified audit|adverse audit)\b",
    "PAYMENT_DEFAULT": r"\b(?:payment default|default in payment|defaulted on|failed to pay)\b",
    "LOAN_RECALL": r"\b(?:loan recall|recall of loan|loan recalled|facility recalled)\b",
}


# Severity mapping for each signal type
SIGNAL_SEVERITY_MAP = {
    "NCLT": Severity.HIGH,
    "DRT": Severity.MEDIUM,
    "SEBI_ENFORCEMENT": Severity.MEDIUM,
    "GOING_CONCERN": Severity.HIGH,
    "CRIMINAL_CASE": Severity.HIGH,
    "AUDIT_QUALIFIED": Severity.MEDIUM,
    "PAYMENT_DEFAULT": Severity.HIGH,
    "LOAN_RECALL": Severity.HIGH,
}


# ============================================================================
# DETECTION FUNCTIONS
# ============================================================================

def scan_for_warnings(text: str, source_document: str) -> List[EarlyWarning]:
    """
    Scan text for early warning patterns.
    
    Args:
        text: Text content to scan (from PDFs, documents, etc.)
        source_document: Name of the source document (e.g., "Balance Sheet 2023", "Bank Statement Q4")
    
    Returns:
        List of EarlyWarning objects with matched signals
    
    Requirements: 9.1, 9.2, 9.5, 9.6
    """
    warnings = []
    
    if not text or not text.strip():
        return warnings
    
    # Collect all matches with their positions first
    all_matches = []
    
    for signal_type, pattern in EARLY_WARNING_PATTERNS.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            all_matches.append({
                'signal_type': signal_type,
                'start': match.start(),
                'end': match.end(),
                'match': match
            })
    
    # Sort by start position, then by length (longer matches first)
    all_matches.sort(key=lambda x: (x['start'], -(x['end'] - x['start'])))
    
    # Filter out overlapping or nearby duplicate matches (within 100 chars)
    filtered_matches = []
    
    for match_info in all_matches:
        # Check if this is a duplicate of an existing match
        is_duplicate = False
        
        for existing in filtered_matches:
            # Same signal type and within 100 characters = likely duplicate
            if (existing['signal_type'] == match_info['signal_type'] and
                abs(existing['start'] - match_info['start']) < 100):
                is_duplicate = True
                break
        
        if not is_duplicate:
            filtered_matches.append(match_info)
    
    # Create warnings from filtered matches
    for match_info in filtered_matches:
        signal_type = match_info['signal_type']
        match = match_info['match']
        
        # Extract matched text with some context (up to 100 chars around match)
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        matched_text = text[start:end].strip()
        
        # Clean up matched text (remove extra whitespace, newlines)
        matched_text = re.sub(r'\s+', ' ', matched_text)
        
        # Truncate if too long
        if len(matched_text) > 150:
            matched_text = matched_text[:147] + "..."
        
        # Calculate severity
        severity = calculate_warning_severity(signal_type, matched_text)
        
        # Create warning
        warning = create_early_warning(
            signal_type=signal_type,
            matched_text=matched_text,
            severity=severity,
            source_document=source_document
        )
        
        warnings.append(warning)
    
    return warnings


def calculate_warning_severity(signal_type: str, context: str) -> Severity:
    """
    Determine severity based on signal type and context.
    
    Args:
        signal_type: Type of signal detected (e.g., "NCLT", "DRT")
        context: Text context around the match
    
    Returns:
        Severity level (HIGH, MEDIUM, LOW)
    
    Requirements: 9.4
    """
    # Base severity from signal type
    base_severity = SIGNAL_SEVERITY_MAP.get(signal_type, Severity.MEDIUM)
    
    # Context-based adjustments
    context_lower = context.lower()
    
    # Upgrade severity if context indicates active/recent issues
    if any(word in context_lower for word in ["pending", "ongoing", "filed", "initiated", "recent"]):
        if base_severity == Severity.MEDIUM:
            return Severity.HIGH
    
    # Downgrade severity if context indicates resolved/historical issues
    if any(word in context_lower for word in ["resolved", "closed", "dismissed", "withdrawn", "historical"]):
        if base_severity == Severity.HIGH:
            return Severity.MEDIUM
        elif base_severity == Severity.MEDIUM:
            return Severity.LOW
    
    return base_severity


def scan_multiple_documents(documents: dict) -> List[EarlyWarning]:
    """
    Scan multiple documents for early warning signals.
    
    Args:
        documents: Dictionary mapping document names to text content
                  e.g., {"Balance Sheet 2023": "...", "Bank Statement Q4": "..."}
    
    Returns:
        Aggregated list of all early warnings found across documents
    
    Requirements: 9.1, 9.6
    """
    all_warnings = []
    
    for doc_name, doc_text in documents.items():
        if doc_text:
            warnings = scan_for_warnings(doc_text, doc_name)
            all_warnings.extend(warnings)
    
    return all_warnings


def get_warning_summary(warnings: List[EarlyWarning]) -> dict:
    """
    Generate summary statistics for early warnings.
    
    Args:
        warnings: List of EarlyWarning objects
    
    Returns:
        Dictionary with summary statistics
    """
    if not warnings:
        return {
            "total_count": 0,
            "high_severity_count": 0,
            "medium_severity_count": 0,
            "low_severity_count": 0,
            "signal_types": []
        }
    
    summary = {
        "total_count": len(warnings),
        "high_severity_count": sum(1 for w in warnings if w.severity == Severity.HIGH),
        "medium_severity_count": sum(1 for w in warnings if w.severity == Severity.MEDIUM),
        "low_severity_count": sum(1 for w in warnings if w.severity == Severity.LOW),
        "signal_types": list(set(w.signal_type for w in warnings))
    }
    
    return summary


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test with sample text
    test_text = """
    The company is facing proceedings at the National Company Law Tribunal (NCLT) 
    regarding insolvency matters. Additionally, there is a pending case at the 
    Debt Recovery Tribunal (DRT) for loan default of ₹50 Crores.
    
    The auditor has expressed a qualified opinion on the financial statements 
    due to going concern doubts. SEBI has initiated enforcement action for 
    non-disclosure of related party transactions.
    """
    
    warnings = scan_for_warnings(test_text, "Test Document")
    
    print(f"Found {len(warnings)} early warning signals:\n")
    for warning in warnings:
        print(f"Signal Type: {warning.signal_type}")
        print(f"Severity: {warning.severity.value}")
        print(f"Matched Text: {warning.matched_text}")
        print(f"Source: {warning.source_document}")
        print("-" * 80)
    
    # Test summary
    summary = get_warning_summary(warnings)
    print(f"\nSummary:")
    print(f"Total warnings: {summary['total_count']}")
    print(f"High severity: {summary['high_severity_count']}")
    print(f"Medium severity: {summary['medium_severity_count']}")
    print(f"Signal types: {', '.join(summary['signal_types'])}")
