"""
Demo Company Registry - Minimal CIN storage for demo mode
Real demo cache (JSON files) will be generated after full system is built
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from data_models import CompanyData, ScoreResult, Verdict


# ============================================================================
# DEMO COMPANIES REGISTRY (CINs only)
# ============================================================================

DEMO_COMPANIES = {
    "IL&FS": {
        "cin": "L65990MH1987PLC044571",
        "company_name": "Infrastructure Leasing and Financial Services Limited",
        "expected_verdict": Verdict.REJECT,
        "cache_file": "ilfs_cache.json"
    },
    "TCS": {
        "cin": "L22210MH1995PLC084781",
        "company_name": "Tata Consultancy Services Limited",
        "expected_verdict": Verdict.APPROVE,
        "cache_file": "tcs_cache.json"
    },
    "Byju's": {
        "cin": "U80903KA2011PTC061427",
        "company_name": "Think & Learn Private Limited",
        "expected_verdict": Verdict.REJECT,
        "cache_file": "byjus_cache.json"
    }
}


# ============================================================================
# DEMO CACHE FUNCTIONS
# ============================================================================

def get_demo_companies_list() -> List[str]:
    """
    Get list of available demo company names.
    
    Returns:
        List[str]: List of demo company names (keys in DEMO_COMPANIES)
    """
    return list(DEMO_COMPANIES.keys())


def get_demo_company_info(company_key: str) -> Optional[Dict[str, Any]]:
    """
    Get basic info for a demo company.
    
    Args:
        company_key: Company key (e.g., "IL&FS", "TCS", "Byju's")
        
    Returns:
        Optional[Dict]: Company info dict or None if not found
    """
    return DEMO_COMPANIES.get(company_key)


def load_demo_cache(company_key: str, cache_dir: str = "demo_cache") -> Optional[tuple]:
    """
    Load demo cache from JSON file.
    
    Args:
        company_key: Company key (e.g., "IL&FS", "TCS", "Byju's")
        cache_dir: Directory containing cache files
        
    Returns:
        Optional[tuple]: (CompanyData, ScoreResult) or None if cache doesn't exist
    """
    company_info = DEMO_COMPANIES.get(company_key)
    if not company_info:
        print(f"Warning: Unknown demo company: {company_key}")
        return None
    
    cache_file = Path(cache_dir) / company_info["cache_file"]
    
    if not cache_file.exists():
        print(f"Warning: Demo cache not found: {cache_file}")
        print("Demo cache will be generated after first real pipeline run (Task 18)")
        return None
    
    try:
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        # Reconstruct CompanyData
        company_data = CompanyData.from_dict(data["company_data"])
        
        # Reconstruct ScoreResult
        score_data = data["score_result"]
        from data_models import FlagItem, FlagCategory, Severity
        
        flags = [
            FlagItem(
                category=FlagCategory(flag["category"]),
                severity=Severity(flag["severity"]),
                description=flag["description"],
                source=flag["source"],
                impact_score=flag["impact_score"]
            )
            for flag in score_data.get("flags", [])
        ]
        
        score_result = ScoreResult(
            character_score=score_data["character_score"],
            capacity_score=score_data["capacity_score"],
            capital_score=score_data["capital_score"],
            collateral_score=score_data["collateral_score"],
            conditions_score=score_data["conditions_score"],
            total_score=score_data["total_score"],
            verdict=Verdict(score_data["verdict"]),
            loan_amount=score_data.get("loan_amount"),
            interest_rate=score_data.get("interest_rate"),
            flags=flags,
            reasoning=score_data.get("reasoning", ""),
            decision_narrative=score_data.get("decision_narrative")
        )
        
        print(f"✓ Loaded demo cache for {company_key}: {cache_file}")
        return (company_data, score_result)
        
    except Exception as e:
        print(f"Error loading demo cache: {e}")
        return None


def save_demo_cache(
    company_key: str,
    company_data: CompanyData,
    score_result: ScoreResult,
    cache_dir: str = "demo_cache"
) -> bool:
    """
    Save demo cache to JSON file.
    
    Args:
        company_key: Company key (e.g., "IL&FS", "TCS", "Byju's")
        company_data: CompanyData object
        score_result: ScoreResult object
        cache_dir: Directory to save cache files
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    company_info = DEMO_COMPANIES.get(company_key)
    if not company_info:
        print(f"Error: Unknown demo company: {company_key}")
        return False
    
    # Create cache directory if it doesn't exist
    cache_path = Path(cache_dir)
    cache_path.mkdir(exist_ok=True)
    
    cache_file = cache_path / company_info["cache_file"]
    
    try:
        # Serialize to dict
        data = {
            "company_data": company_data.to_dict(),
            "score_result": score_result.to_dict()
        }
        
        # Save to JSON
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Saved demo cache for {company_key}: {cache_file}")
        return True
        
    except Exception as e:
        print(f"Error saving demo cache: {e}")
        return False


def validate_demo_cache(company_key: str, cache_dir: str = "demo_cache") -> bool:
    """
    Validate that demo cache exists and verdict matches expected.
    
    Args:
        company_key: Company key (e.g., "IL&FS", "TCS", "Byju's")
        cache_dir: Directory containing cache files
        
    Returns:
        bool: True if cache is valid, False otherwise
    """
    company_info = DEMO_COMPANIES.get(company_key)
    if not company_info:
        return False
    
    result = load_demo_cache(company_key, cache_dir)
    if not result:
        return False
    
    company_data, score_result = result
    expected_verdict = company_info["expected_verdict"]
    
    if score_result.verdict != expected_verdict:
        print(f"Warning: {company_key} verdict mismatch!")
        print(f"  Expected: {expected_verdict.value}")
        print(f"  Got: {score_result.verdict.value}")
        return False
    
    print(f"✓ {company_key} cache valid: {score_result.verdict.value}")
    return True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_cin_by_company_name(company_name: str) -> Optional[str]:
    """
    Get CIN by company name (case-insensitive partial match).
    
    Args:
        company_name: Company name to search
        
    Returns:
        Optional[str]: CIN if found, None otherwise
    """
    company_name_lower = company_name.lower()
    
    for key, info in DEMO_COMPANIES.items():
        if company_name_lower in info["company_name"].lower():
            return info["cin"]
    
    return None


def is_demo_company(cin: str) -> bool:
    """
    Check if CIN belongs to a demo company.
    
    Args:
        cin: Corporate Identification Number
        
    Returns:
        bool: True if demo company, False otherwise
    """
    for info in DEMO_COMPANIES.values():
        if info["cin"] == cin:
            return True
    return False


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Demo Company Registry")
    print("=" * 60)
    print()
    
    print("Available demo companies:")
    for key in get_demo_companies_list():
        info = get_demo_company_info(key)
        print(f"  {key}:")
        print(f"    CIN: {info['cin']}")
        print(f"    Name: {info['company_name']}")
        print(f"    Expected: {info['expected_verdict'].value}")
        print()
    
    print("=" * 60)
    print("Note: Demo cache JSON files will be generated in Task 18")
    print("=" * 60)
