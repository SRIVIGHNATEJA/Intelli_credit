"""
MCA Setup Script - Download and filter Indian companies dataset
Downloads MCA data from Kaggle and filters for demo companies
"""

import re
import pandas as pd
import kagglehub
from pathlib import Path


# Demo company CINs (corrected)
DEMO_CINS = [
    "L65990MH1987PLC044571",  # IL&FS
    "L22210MH1995PLC084781",  # TCS
    "U80903KA2011PTC061427",  # Byju's
]


def validate_cin_format(cin: str) -> bool:
    """
    Validate CIN format using regex pattern.
    
    CIN Format: [U/L][5-digit industry code][2-letter state][4-digit year][PLC/PTC][6-digit registration]
    Example: L65990MH1987PLC044571
    
    Args:
        cin: Corporate Identification Number
        
    Returns:
        bool: True if valid format, False otherwise
    """
    if not cin or not isinstance(cin, str):
        return False
    
    # CIN pattern: [U/L][5 digits][2 letters][4 digits][PLC/PTC][6 digits]
    pattern = r'^[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$'
    return bool(re.match(pattern, cin))


def download_mca_dataset() -> Path:
    """
    Download MCA dataset from Kaggle using kagglehub.
    
    Returns:
        Path: Path to downloaded dataset directory
    """
    print("Downloading MCA dataset from Kaggle...")
    print("Dataset: rowhitswami/all-indian-companies-registration-data-1900-2019")
    
    try:
        # Download latest version
        path = kagglehub.dataset_download(
            "rowhitswami/all-indian-companies-registration-data-1900-2019"
        )
        print(f"✓ Dataset downloaded to: {path}")
        return Path(path)
    except Exception as e:
        print(f"✗ Error downloading dataset: {e}")
        print("Note: You may need to configure Kaggle API credentials")
        print("Run: kaggle config set -n username -v YOUR_USERNAME")
        raise


def find_csv_file(dataset_path: Path) -> Path:
    """
    Find the CSV file in the downloaded dataset directory.
    
    Args:
        dataset_path: Path to dataset directory
        
    Returns:
        Path: Path to CSV file
    """
    csv_files = list(dataset_path.glob("*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {dataset_path}")
    
    if len(csv_files) > 1:
        print(f"Warning: Multiple CSV files found, using first: {csv_files[0].name}")
    
    return csv_files[0]


def filter_kaggle_csv(input_csv: Path, output_csv: Path, cin_list: list) -> int:
    """
    Filter Kaggle MCA CSV for specific CINs and save to output file.
    
    Args:
        input_csv: Path to input CSV file
        output_csv: Path to output CSV file
        cin_list: List of CINs to filter
        
    Returns:
        int: Number of companies found
    """
    print(f"\nFiltering CSV for {len(cin_list)} demo companies...")
    
    # Validate all CINs
    for cin in cin_list:
        if not validate_cin_format(cin):
            print(f"Warning: Invalid CIN format: {cin}")
    
    try:
        # Read CSV (try different encodings)
        try:
            df = pd.read_csv(input_csv, low_memory=False)
        except UnicodeDecodeError:
            df = pd.read_csv(input_csv, encoding='latin-1', low_memory=False)
        
        print(f"✓ Loaded dataset: {len(df)} total companies")
        
        # Find CIN column (case-insensitive)
        cin_column = None
        possible_names = ['CORPORATE_IDENTIFICATION_NUMBER', 'CIN', 'Corporate Identification Number']
        
        for col in df.columns:
            if col in possible_names or 'corporate' in col.lower() and 'identification' in col.lower():
                cin_column = col
                break
        
        if not cin_column:
            raise ValueError(f"No CIN column found. Available columns: {list(df.columns)}")
        
        print(f"✓ Using CIN column: '{cin_column}'")
        
        # Filter for demo companies
        filtered_df = df[df[cin_column].isin(cin_list)]
        
        if filtered_df.empty:
            print("✗ No matching companies found in dataset")
            print(f"Searched for CINs: {cin_list}")
            return 0
        
        # Save filtered data
        filtered_df.to_csv(output_csv, index=False)
        print(f"✓ Saved {len(filtered_df)} companies to: {output_csv}")
        
        # Show found companies
        print("\nFound companies:")
        for _, row in filtered_df.iterrows():
            cin = row[cin_column]
            company_name = row.get('COMPANY_NAME', row.get('Company Name', 'Unknown'))
            print(f"  - {cin}: {company_name}")
        
        return len(filtered_df)
        
    except Exception as e:
        print(f"✗ Error filtering CSV: {e}")
        raise


def main():
    """Main execution function."""
    print("=" * 60)
    print("MCA Setup Script - Demo Company Data Extraction")
    print("=" * 60)
    
    try:
        # Step 1: Download dataset
        dataset_path = download_mca_dataset()
        
        # Step 2: Find CSV file
        input_csv = find_csv_file(dataset_path)
        print(f"✓ Found CSV file: {input_csv.name}")
        
        # Step 3: Filter for demo companies
        output_csv = Path("mca_demo_companies.csv")
        count = filter_kaggle_csv(input_csv, output_csv, DEMO_CINS)
        
        # Summary
        print("\n" + "=" * 60)
        if count == len(DEMO_CINS):
            print(f"✓ SUCCESS: All {count} demo companies found and saved")
        elif count > 0:
            print(f"⚠ PARTIAL: {count}/{len(DEMO_CINS)} demo companies found")
        else:
            print("✗ FAILED: No demo companies found")
        print("=" * 60)
        
        return count
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ FAILED: {e}")
        print("=" * 60)
        print("\nNote: If CSV not available, demo_cache JSONs will be used as fallback")
        return 0


if __name__ == "__main__":
    main()
