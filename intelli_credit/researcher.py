"""
Web Researcher - External data gathering for credit assessment
Implements news search, MCA lookup, stock data, and sector classification
"""

import os
import requests
import pandas as pd
import yfinance as yf
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
from groq import Groq

from data_models import ResearchResult, NewsItem, StockData
from prompts import get_sector_classification_prompt, get_sector_outlook_prompt


# Constants
MAX_NEWS_ITEMS = 5
API_TIMEOUT = 5  # seconds


# ============================================================================
# NEWS SEARCH - FALLBACK CHAIN
# ============================================================================

def search_news_serper(company_name: str, promoter_name: str = "") -> List[Dict[str, str]]:
    """
    Primary news search using Serper API with 7 targeted query categories.
    GOLD STANDARD: Comprehensive credit-relevant search across all risk categories.
    
    Args:
        company_name: Name of the company to search
        promoter_name: Name of promoter/founder (optional, for criminal case searches)
        
    Returns:
        List of news dicts with title, source, date, url, category, snippet
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        print("⚠ Serper API key not found")
        return []
    
    try:
        url = "https://google.serper.dev/news"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        
        # GOLD STANDARD: 7 COMPREHENSIVE QUERY CATEGORIES
        # Each category targets specific credit risk indicators
        queries = [
            # Category 1: Fraud & Regulatory Enforcement
            {
                "query": f'"{company_name}" fraud SEBI ED CBI default enforcement penalty action',
                "category": "Fraud_Regulatory",
                "description": "Fraud cases, regulatory enforcement, penalties"
            },
            
            # Category 2: Insolvency & Legal Proceedings  
            {
                "query": f'"{company_name}" NCLT insolvency winding up liquidation bankruptcy proceedings',
                "category": "Insolvency_Legal", 
                "description": "NCLT cases, insolvency, bankruptcy proceedings"
            },
            
            # Category 3: Criminal Cases & Investigations
            {
                "query": f'"{promoter_name or company_name}" criminal arrest investigation EOW FIR charges police' if promoter_name else f'"{company_name}" criminal case investigation EOW',
                "category": "Criminal_Cases",
                "description": "Criminal cases, arrests, investigations"
            },
            
            # Category 4: Banking & Credit Issues
            {
                "query": f'"{company_name}" NPA default bank debt restructuring loan recall moratorium',
                "category": "Banking_Credit",
                "description": "NPA classification, loan defaults, debt issues"
            },
            
            # Category 5: Recent News & Developments
            {
                "query": f'"{company_name}" news 2024 2025 latest developments announcement',
                "category": "Recent_News",
                "description": "Latest news and corporate developments"
            },
            
            # Category 6: Financial Performance & Results
            {
                "query": f'"{company_name}" financial results earnings revenue profit loss quarterly annual performance',
                "category": "Financial_Performance", 
                "description": "Financial results, earnings, performance"
            },
            
            # Category 7: Ratings & Credit Assessment
            {
                "query": f'"{company_name}" rating downgrade upgrade credit assessment CRISIL ICRA CARE Moody Fitch',
                "category": "Credit_Ratings",
                "description": "Credit ratings, downgrades, upgrades"
            }
        ]
        
        all_news = []
        seen_urls = set()
        
        for i, query_info in enumerate(queries, 1):
            query = query_info["query"]
            category = query_info["category"]
            description = query_info["description"]
            
            print(f"🔍 Category {i} ({category}): {description}")
            print(f"   Query: {query[:80]}...")
            
            payload = {
                "q": query,
                "num": 3,  # 3 results per category = 21 total max
                "gl": "in",  # India region
                "hl": "en",  # English language
                "tbm": "nws",  # News search
                "tbs": "qdr:y2"  # Last 2 years for relevance
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=API_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            category_count = 0
            
            for item in data.get("news", []):
                url_link = item.get("link", "")
                
                # Skip duplicates
                if url_link in seen_urls:
                    continue
                seen_urls.add(url_link)
                
                # Extract and validate news item
                news_item = {
                    "title": item.get("title", "").strip(),
                    "source": item.get("source", "Unknown").strip(),
                    "date": item.get("date", "").strip(),
                    "url": url_link.strip(),
                    "category": category,
                    "snippet": item.get("snippet", "").strip()[:300],  # First 300 chars
                    "search_rank": len(all_news) + 1  # Track search order
                }
                
                # Validate required fields
                if news_item["title"] and news_item["source"] and len(news_item["title"]) > 10:
                    all_news.append(news_item)
                    category_count += 1
                    print(f"   ✓ Found: {news_item['title'][:70]}...")
                    
                    if category_count >= 3:  # Max 3 per category
                        break
            
            if category_count == 0:
                print(f"   ⚠ No results found for {category}")
            
            # Small delay between queries to avoid rate limiting
            time.sleep(0.3)
        
        # Sort by relevance (fraud/legal issues first, then by search rank)
        priority_categories = ["Fraud_Regulatory", "Criminal_Cases", "Insolvency_Legal", "Banking_Credit"]
        
        def sort_key(item):
            category_priority = 0 if item["category"] in priority_categories else 1
            return (category_priority, item["search_rank"])
        
        all_news.sort(key=sort_key)
        
        print(f"✓ Serper search complete: {len(all_news)} articles found across 7 categories")
        print(f"  Categories covered: {len(set(item['category'] for item in all_news))}/7")
        
        return all_news[:MAX_NEWS_ITEMS]  # Return top results
        
    except Exception as e:
        print(f"⚠ Serper API error: {e}")
        return []


def search_news_gdelt(company_name: str) -> List[Dict[str, str]]:
    """
    Backup 1: News search using GDELT API (free, no auth).
    Uses COMPREHENSIVE queries covering all 7 credit risk categories.

    Args:
        company_name: Name of the company to search

    Returns:
        List of news dicts with title, source, date, url
    """
    try:
        # GDELT DOC 2.0 API endpoint
        url = "https://api.gdeltproject.org/api/v2/doc/doc"

        # ENHANCED: Comprehensive query covering all 7 categories
        # Fraud & Regulatory + Insolvency + Banking + Criminal + Financial + Ratings + Recent
        query = f'"{company_name}" (fraud OR SEBI OR ED OR CBI OR default OR enforcement OR penalty OR NCLT OR insolvency OR winding OR liquidation OR bankruptcy OR criminal OR arrest OR investigation OR NPA OR debt OR restructuring OR loan OR recall OR financial OR earnings OR revenue OR profit OR rating OR downgrade OR upgrade OR CRISIL OR ICRA OR CARE OR Moody OR Fitch OR news OR latest OR developments)'

        params = {
            "query": query,
            "mode": "artlist",
            "maxrecords": MAX_NEWS_ITEMS,
            "format": "json",
            "timespan": "2y"  # Last 2 years for relevance
        }

        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()

        data = response.json()
        news_items = []

        for item in data.get("articles", [])[:MAX_NEWS_ITEMS]:
            news_items.append({
                "title": item.get("title", ""),
                "source": item.get("domain", "Unknown"),
                "date": item.get("seendate", ""),
                "url": item.get("url", ""),
                "snippet": item.get("socialimage", ""),
                "category": "Mixed"  # GDELT doesn't categorize, so mark as mixed
            })

        print(f"✓ GDELT enhanced search: {len(news_items)} articles found")
        return news_items

    except Exception as e:
        print(f"GDELT API error: {e}")
        return []


def search_news_newsapi(company_name: str) -> List[Dict[str, str]]:
    """
    Backup 2: News search using NewsAPI.
    Uses COMPREHENSIVE queries covering all 7 credit risk categories.

    Args:
        company_name: Name of the company to search

    Returns:
        List of news dicts with title, source, date, url
    """
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        return []

    try:
        url = "https://newsapi.org/v2/everything"

        # ENHANCED: Comprehensive query covering all 7 categories
        # Fraud & Regulatory + Insolvency + Banking + Criminal + Financial + Ratings + Recent
        query = f'"{company_name}" AND (fraud OR SEBI OR ED OR CBI OR default OR enforcement OR penalty OR NCLT OR insolvency OR winding OR liquidation OR bankruptcy OR criminal OR arrest OR investigation OR NPA OR debt OR restructuring OR loan OR recall OR financial OR earnings OR revenue OR profit OR rating OR downgrade OR upgrade OR CRISIL OR ICRA OR CARE OR Moody OR Fitch OR news OR latest OR developments)'

        params = {
            "q": query,
            "apiKey": api_key,
            "pageSize": MAX_NEWS_ITEMS,
            "language": "en",
            "sortBy": "relevancy",
            "from": "2023-01-01"  # Last 2+ years for relevance
        }

        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()

        data = response.json()
        news_items = []

        for item in data.get("articles", [])[:MAX_NEWS_ITEMS]:
            news_items.append({
                "title": item.get("title", ""),
                "source": item.get("source", {}).get("name", "Unknown"),
                "date": item.get("publishedAt", ""),
                "url": item.get("url", ""),
                "snippet": item.get("description", ""),
                "category": "Mixed"  # NewsAPI doesn't categorize, so mark as mixed
            })

        print(f"✓ NewsAPI enhanced search: {len(news_items)} articles found")
        return news_items

    except Exception as e:
        print(f"NewsAPI error: {e}")
        return []


# ============================================================================
# MCA AND STOCK DATA LOOKUP
# ============================================================================

def lookup_mca_status(cin: str) -> Optional[str]:
    """
    Query MCA demo companies CSV for company status.
    
    Args:
        cin: Corporate Identification Number
        
    Returns:
        Company status string (Active, Strike Off, etc.) or None
    """
    csv_path = Path("mca_demo_companies.csv")
    
    if not csv_path.exists():
        print(f"MCA CSV not found: {csv_path}")
        return None
    
    try:
        df = pd.read_csv(csv_path)
        
        # Find CIN column (case-insensitive)
        cin_column = None
        for col in df.columns:
            if 'corporate' in col.lower() and 'identification' in col.lower():
                cin_column = col
                break
            elif col.upper() == 'CIN':
                cin_column = col
                break
        
        if not cin_column:
            print("No CIN column found in MCA CSV")
            return None
        
        # Find matching row
        matching_rows = df[df[cin_column] == cin]
        
        if matching_rows.empty:
            print(f"No MCA record found for CIN: {cin}")
            return None
        
        # Look for status column
        status_column = None
        for col in df.columns:
            if 'status' in col.lower() or 'company_status' in col.lower():
                status_column = col
                break
        
        if status_column:
            return str(matching_rows.iloc[0][status_column])
        else:
            # Default to Active if no status column
            return "Active"
        
    except Exception as e:
        print(f"Error reading MCA CSV: {e}")
        return None


def get_stock_data(company_name: str) -> Optional[StockData]:
    """
    Retrieve stock market data using yfinance for listed companies.
    
    Args:
        company_name: Name of the company
        
    Returns:
        StockData object or None if not listed/error
    """
    try:
        # Common ticker mappings for demo companies
        ticker_map = {
            "tata consultancy services": "TCS.NS",
            "tcs": "TCS.NS",
            "infosys": "INFY.NS",
            "wipro": "WIPRO.NS",
            "reliance": "RELIANCE.NS"
        }
        
        # Try to find ticker
        company_lower = company_name.lower()
        ticker = None
        
        for key, value in ticker_map.items():
            if key in company_lower:
                ticker = value
                break
        
        if not ticker:
            # Try direct search with .NS suffix
            ticker = f"{company_name.upper().replace(' ', '')}.NS"
        
        # Fetch data with timeout
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Check if valid data returned
        if not info or 'currentPrice' not in info:
            return StockData(is_listed=False)
        
        # Extract data
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        market_cap = info.get('marketCap')
        
        # Convert market cap to ₹ Crores
        if market_cap:
            market_cap_crores = market_cap / 10_000_000  # Convert to Crores
        else:
            market_cap_crores = None
        
        return StockData(
            ticker=ticker,
            current_price=current_price,
            market_cap=market_cap_crores,
            is_listed=True
        )
        
    except Exception as e:
        print(f"Stock data error for {company_name}: {e}")
        return StockData(is_listed=False)


# ============================================================================
# SECTOR CLASSIFICATION
# ============================================================================

def classify_sector_with_groq(company_name: str, description: str = "") -> Optional[str]:
    """
    Classify company sector using Groq API (ONE WORD output).
    
    Args:
        company_name: Name of the company
        description: Optional company description
        
    Returns:
        Sector name (ONE WORD) or None
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY not found")
        return None
    
    try:
        client = Groq(api_key=api_key)
        
        prompt = get_sector_classification_prompt(company_name, description)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a sector classification assistant. Return ONLY ONE WORD."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0,
            max_tokens=10
        )
        
        sector = response.choices[0].message.content.strip()
        
        # Validate it's a single word
        if ' ' in sector:
            sector = sector.split()[0]
        
        return sector
        
    except Exception as e:
        print(f"Groq sector classification error: {e}")
        return None


def classify_sector_outlook_with_groq(sector: str, news_context: str) -> Optional[str]:
    """
    Classify sector outlook using Groq API (ONE WORD output).
    
    Args:
        sector: Sector name
        news_context: Recent news about the sector/company
        
    Returns:
        Outlook (GROWING/STABLE/DECLINING/DISTRESSED) or None
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY not found")
        return None
    
    try:
        client = Groq(api_key=api_key)
        
        prompt = get_sector_outlook_prompt(sector, news_context)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a sector outlook analyst. Return ONLY ONE WORD."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0,
            max_tokens=10
        )
        
        outlook = response.choices[0].message.content.strip().upper()
        
        # Validate it's one of the expected values
        valid_outlooks = ["GROWING", "STABLE", "DECLINING", "DISTRESSED"]
        if outlook not in valid_outlooks:
            # Try to extract first word
            outlook = outlook.split()[0] if outlook else "STABLE"
        
        return outlook if outlook in valid_outlooks else "STABLE"
        
    except Exception as e:
        print(f"Groq sector outlook error: {e}")
        return "STABLE"  # Neutral fallback


# ============================================================================
# MASTER RESEARCH FUNCTION
# ============================================================================

def research_company(
    cin: str,
    company_name: str,
    description: str = "",
    promoter_name: str = ""
) -> ResearchResult:
    """
    Master function to research company using all available sources.
    Implements fallback chain for news and graceful error handling.

    Args:
        cin: Corporate Identification Number
        company_name: Name of the company
        description: Optional company description
        promoter_name: Optional promoter/founder name for criminal case searches

    Returns:
        ResearchResult object with all gathered data
    """
    print(f"\n{'='*60}")
    print(f"Researching: {company_name}")
    print(f"CIN: {cin}")
    if promoter_name:
        print(f"Promoter: {promoter_name}")
    print(f"{'='*60}\n")

    # Initialize result
    result = ResearchResult(validation_status="POTENTIAL_MATCH")

    # 1. News search with fallback chain
    print("Searching news (Serper → GDELT → NewsAPI)...")
    news_data = []

    # Try Serper first (with promoter name for criminal searches)
    news_data = search_news_serper(company_name, promoter_name)
    if news_data:
        print(f"✓ Serper: Found {len(news_data)} articles")
    else:
        print("✗ Serper: No results, trying GDELT...")
        # Try GDELT
        news_data = search_news_gdelt(company_name)
        if news_data:
            print(f"✓ GDELT: Found {len(news_data)} articles")
        else:
            print("✗ GDELT: No results, trying NewsAPI...")
            # Try NewsAPI
            news_data = search_news_newsapi(company_name)
            if news_data:
                print(f"✓ NewsAPI: Found {len(news_data)} articles")
            else:
                print("✗ All news sources failed")

    # Convert to NewsItem objects
    result.news_items = [
        NewsItem(
            title=item["title"],
            source=item["source"],
            date=item["date"],
            url=item["url"],
            snippet=item.get("snippet")
        )
        for item in news_data
    ]

    # 2. MCA status lookup
    print("\nLooking up MCA status...")
    mca_status = lookup_mca_status(cin)
    if mca_status:
        print(f"✓ MCA Status: {mca_status}")
        result.mca_status = mca_status
    else:
        print("✗ MCA status not found")
        result.mca_status = None

    # 3. Stock data lookup
    print("\nFetching stock data...")
    stock_data = get_stock_data(company_name)
    if stock_data and stock_data.is_listed:
        print(f"✓ Stock: {stock_data.ticker} @ ₹{stock_data.current_price}")
        print(f"  Market Cap: ₹{stock_data.market_cap:.2f} Cr" if stock_data.market_cap else "  Market Cap: N/A")
        result.stock_data = stock_data
    else:
        print("✗ Not listed or data unavailable")
        result.stock_data = StockData(is_listed=False)

    # 4. Sector classification
    print("\nClassifying sector...")
    sector = classify_sector_with_groq(company_name, description)
    if sector:
        print(f"✓ Sector: {sector}")
        result.sector = sector
    else:
        print("✗ Sector classification failed")
        result.sector = None

    # 5. Sector outlook (if we have news and sector)
    if result.sector and result.news_items:
        print("\nAnalyzing sector outlook...")
        # Build news context from headlines
        news_context = "\n".join([
            f"- {item.title}" for item in result.news_items[:3]
        ])

        outlook = classify_sector_outlook_with_groq(result.sector, news_context)
        if outlook:
            print(f"✓ Outlook: {outlook}")
            result.sector_outlook = outlook
        else:
            print("✗ Outlook analysis failed, defaulting to STABLE")
            result.sector_outlook = "STABLE"
    else:
        print("\nSkipping sector outlook (insufficient data)")
        result.sector_outlook = "STABLE"

    # 6. Set sector NPA rate (hardcoded based on sector)
    if result.sector:
        SECTOR_NPA = {
            "Infrastructure": 18.4,
            "IT": 0.8,
            "Education": 12.3,
            "Manufacturing": 4.2,
            "FMCG": 1.8,
            "RealEstate": 9.6,
            "Telecom": 6.1,
            "Banking": 3.9,
            "NBFC": 7.2,
            "Pharma": 2.1,
            "Retail": 3.4,
            "Construction": 8.8
        }

        # Try to match sector (case-insensitive, partial match)
        sector_lower = result.sector.lower()
        for key, npa_rate in SECTOR_NPA.items():
            if key.lower() in sector_lower or sector_lower in key.lower():
                result.sector_npa_rate = npa_rate
                print(f"✓ Sector NPA Rate: {npa_rate}%")
                break

        if result.sector_npa_rate is None:
            # Default to average
            result.sector_npa_rate = 6.5
            print(f"⚠ Using average NPA rate: 6.5%")

    print(f"\n{'='*60}")
    print("Research complete")
    print(f"{'='*60}\n")

    return result


# ============================================================================
# MAIN (FOR TESTING)
# ============================================================================

if __name__ == "__main__":
    # Test with TCS
    from dotenv import load_dotenv
    load_dotenv()
    
    result = research_company(
        cin="L22210MH1995PLC084781",
        company_name="Tata Consultancy Services",
        description="Leading IT services company"
    )
    
    print("\n" + "="*60)
    print("RESEARCH RESULTS")
    print("="*60)
    print(f"Sector: {result.sector}")
    print(f"Outlook: {result.sector_outlook}")
    print(f"NPA Rate: {result.sector_npa_rate}%")
    print(f"MCA Status: {result.mca_status}")
    print(f"Stock Listed: {result.stock_data.is_listed if result.stock_data else False}")
    print(f"News Items: {len(result.news_items)}")
    print(f"Validation: {result.validation_status}")
