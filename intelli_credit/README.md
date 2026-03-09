# Intelli-Credit: AI-Powered CAM Generator

**Tagline:** "AI reads. Math decides. Every decision explained."

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys:
# - GROQ_API_KEY (required)
# - SERPER_API_KEY (optional, for news search)
# - NEWSAPI_KEY (optional, for news fallback)
```

### 3. Run Application

```bash
streamlit run app.py
```

## System Requirements

- Python 3.10+
- Tesseract OCR (for scanned PDFs)
  - macOS: `brew install tesseract`
  - Ubuntu: `sudo apt-get install tesseract-ocr`
  - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

## Project Structure

```
intelli_credit/
├── app.py                  # Streamlit UI
├── pipeline.py             # Orchestrator
├── parser.py               # PDF extraction
├── scorer.py               # Five Cs scoring
├── analyser.py             # GST fraud detection
├── researcher.py           # Web research
├── report_generator.py     # CAM Word document
├── officer_portal.py       # Officer notes
├── detector.py             # Early warnings
├── data_models.py          # Data structures
├── prompts.py              # LLM prompts
├── dummy_data.py           # Demo company registry
├── setup_mca.py            # MCA CSV setup
├── demo_cache/             # Cached demo data
├── uploads/                # Uploaded PDFs
└── output/                 # Generated CAMs
```

## Demo Mode

The system includes 3 pre-cached demo companies:
- **IL&FS**: Infrastructure Finance (expected: REJECT)
- **TCS**: IT Services (expected: APPROVE)
- **Byju's**: Education Technology (expected: REJECT)

Demo cache is generated after first real pipeline run.

## Features

- ✅ PDF extraction (digital + scanned)
- ✅ GST fraud detection (circular trading, ITC fraud)
- ✅ Five Cs credit scoring (pure Python math)
- ✅ Professional CAM Word documents
- ✅ Officer portal for qualitative adjustments
- ✅ Multi-source web research (3-tier fallback)
- ✅ Live stock market data (yfinance)
- ✅ Full explainability (every flag cited)

## Technology Stack

- **UI**: Streamlit
- **LLM**: Groq API (llama-3.3-70b-versatile)
- **PDF Processing**: pdfplumber, pytesseract, pdf2image
- **Document Generation**: python-docx
- **Web Research**: Serper, GDELT, NewsAPI
- **Financial Data**: yfinance
- **Data Processing**: pandas, numpy

## License

MIT License

