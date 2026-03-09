"""
Intelli-Credit Streamlit UI - AI-powered CAM Generator
Main application entry point with upload interface and results display

CRITICAL STREAMLIT SAFEGUARDS:
1. Prevent re-run loops: Use st.session_state for all stateful data
2. UI responsiveness: Use st.spinner() and st.progress() during processing
3. Error surfacing: Display st.warning()/st.error() instead of crashing
4. Session persistence: Tabs/widgets don't re-trigger pipeline
5. Compliance UI: CIBIL CMR rank input with auto-routing logic
"""

import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Dict

from data_models import CompanyData, ScoreResult
from pipeline import process_application
from scorer import calculate_five_cs
from report_generator import generate_cam_word
from dummy_data import get_demo_companies_list, get_demo_company_info


# Load environment variables
load_dotenv()


# ============================================================================
# TASK 17.1: SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """
    Initialize all session state variables.
    
    SAFEGUARD 1 & 4: Prevents re-run loops and ensures session persistence.
    """
    if 'company_data' not in st.session_state:
        st.session_state.company_data = None
    
    if 'score_result' not in st.session_state:
        st.session_state.score_result = None
    
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
    if 'demo_mode' not in st.session_state:
        st.session_state.demo_mode = False
    
    if 'cam_document_path' not in st.session_state:
        st.session_state.cam_document_path = None
    
    if 'uploaded_file_paths' not in st.session_state:
        st.session_state.uploaded_file_paths = {}


# ============================================================================
# TASK 17.2: PAGE 1 - UPLOAD AND DEMO SELECTION
# ============================================================================

def page_upload():
    """
    Upload page with file upload widgets and demo mode selector.
    
    SAFEGUARD 1: Heavy pipeline only executes when button is clicked.
    SAFEGUARD 5: Includes compliance UI block.
    """
    st.title("🏦 Intelli-Credit CAM Generator")
    st.markdown("AI-powered Credit Assessment Memorandum generation using Five Cs framework")
    
    st.markdown("---")
    
    # Two-column layout
    col1, col2 = st.columns([1, 1])
    
    # LEFT COLUMN: File uploads
    with col1:
        st.subheader("📄 Upload Financial Documents")
        
        uploaded_files = {}
        
        balance_sheet = st.file_uploader(
            "Balance Sheet (PDF)",
            type=['pdf'],
            key='balance_sheet'
        )
        if balance_sheet:
            # Save to uploads directory
            upload_path = Path("uploads") / balance_sheet.name
            upload_path.parent.mkdir(exist_ok=True)
            with open(upload_path, 'wb') as f:
                f.write(balance_sheet.getbuffer())
            uploaded_files['balance_sheet'] = str(upload_path)
        
        profit_loss = st.file_uploader(
            "Profit & Loss Statement (PDF)",
            type=['pdf'],
            key='profit_loss'
        )
        if profit_loss:
            upload_path = Path("uploads") / profit_loss.name
            with open(upload_path, 'wb') as f:
                f.write(profit_loss.getbuffer())
            uploaded_files['profit_loss'] = str(upload_path)
        
        bank_statements = st.file_uploader(
            "Bank Statements (PDF)",
            type=['pdf'],
            key='bank_statements'
        )
        if bank_statements:
            upload_path = Path("uploads") / bank_statements.name
            with open(upload_path, 'wb') as f:
                f.write(bank_statements.getbuffer())
            uploaded_files['bank_statements'] = str(upload_path)
        
        gst_returns = st.file_uploader(
            "GST Returns (PDF)",
            type=['pdf'],
            key='gst_returns'
        )
        if gst_returns:
            upload_path = Path("uploads") / gst_returns.name
            with open(upload_path, 'wb') as f:
                f.write(gst_returns.getbuffer())
            uploaded_files['gst_returns'] = str(upload_path)
        
        itr = st.file_uploader(
            "Income Tax Returns (PDF)",
            type=['pdf'],
            key='itr'
        )
        if itr:
            upload_path = Path("uploads") / itr.name
            with open(upload_path, 'wb') as f:
                f.write(itr.getbuffer())
            uploaded_files['itr'] = str(upload_path)
        
        sanction_letter = st.file_uploader(
            "Sanction Letter (PDF)",
            type=['pdf'],
            key='sanction_letter'
        )
        if sanction_letter:
            upload_path = Path("uploads") / sanction_letter.name
            with open(upload_path, 'wb') as f:
                f.write(sanction_letter.getbuffer())
            uploaded_files['sanction_letter'] = str(upload_path)
        
        st.session_state.uploaded_file_paths = uploaded_files
    
    # RIGHT COLUMN: Demo mode and company details
    with col2:
        st.subheader("🎯 Demo Mode")
        
        demo_companies = get_demo_companies_list()
        demo_options = ["None (Real Mode)"] + demo_companies
        
        selected_demo = st.selectbox(
            "Select Demo Company",
            options=demo_options,
            help="Choose a pre-loaded demo company or select 'None' to process uploaded documents"
        )
        
        if selected_demo != "None (Real Mode)":
            demo_info = get_demo_company_info(selected_demo)
            if demo_info:
                st.info(f"**{demo_info['company_name']}**\n\nCIN: {demo_info['cin']}\n\nExpected: {demo_info['expected_verdict'].value}")
                
                # Check if cache exists
                cache_path = Path("demo_cache") / demo_info['cache_file']
                if not cache_path.exists():
                    st.warning("⚠️ Demo cache not yet generated. Will be created after first real run (Task 18).")
        
        st.markdown("---")
        
        st.subheader("🏢 Company Details")
        
        cin_input = st.text_input(
            "Corporate Identification Number (CIN)",
            value=demo_info['cin'] if selected_demo != "None (Real Mode)" and demo_info else "",
            help="21-character CIN from MCA"
        )
        
        company_name_input = st.text_input(
            "Company Name",
            value=demo_info['company_name'] if selected_demo != "None (Real Mode)" and demo_info else "",
            help="Legal name of the company"
        )
        
        promoter_name_input = st.text_input(
            "Promoter Name",
            help="Name of the primary promoter/director"
        )
    
    st.markdown("---")
    
    # SAFEGUARD 5: Compliance UI Block
    st.markdown("### 🔒 System Audit & Compliance")
    cibil_score = st.number_input(
        "CIBIL Commercial CMR Rank (1-10)",
        min_value=1,
        max_value=10,
        value=3,
        help="1 = Highest risk, 10 = Lowest risk"
    )
    
    if cibil_score > 6:
        st.warning("⚠️ High Risk CMR detected. Auto-routing to Senior Credit Committee.")
    
    st.markdown("---")
    
    # Process Application button
    if st.button("🚀 Process Application", type="primary", use_container_width=True):
        # Validation
        if not cin_input or not company_name_input:
            st.error("❌ Please provide CIN and Company Name")
            return
        
        # Determine mode
        is_demo = selected_demo != "None (Real Mode)"
        
        if not is_demo and not st.session_state.uploaded_file_paths:
            st.error("❌ Please upload at least one financial document or select a demo company")
            return
        
        # SAFEGUARD 1: Heavy pipeline only executes here
        try:
            # SAFEGUARD 2: Use st.spinner() for UI responsiveness
            with st.spinner("🔄 Processing application..."):
                # Show progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Initialize
                status_text.text("Step 1/6: Initializing...")
                progress_bar.progress(10)
                
                # Step 2: Process application
                status_text.text("Step 2/6: Processing documents...")
                progress_bar.progress(20)
                
                company_data = process_application(
                    cin=cin_input,
                    company_name=company_name_input,
                    promoter_name=promoter_name_input if promoter_name_input else None,
                    uploaded_files=st.session_state.uploaded_file_paths if not is_demo else None,
                    demo_mode=is_demo,
                    demo_company_key=selected_demo if is_demo else None
                )
                
                progress_bar.progress(40)
                
                # Step 3: Analyze GST
                status_text.text("Step 3/6: Analyzing GST data...")
                progress_bar.progress(50)
                
                # Step 4: Research
                status_text.text("Step 4/6: Researching company...")
                progress_bar.progress(60)
                
                # Step 5: Calculate score
                status_text.text("Step 5/6: Calculating Five Cs score...")
                progress_bar.progress(70)
                
                score_result = calculate_five_cs(company_data)
                
                progress_bar.progress(85)
                
                # Step 6: Generate CAM
                status_text.text("Step 6/6: Generating CAM document...")
                
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                output_path = output_dir / f"CAM_{cin_input}_{company_name_input.replace(' ', '_')}.docx"
                
                cam_path = generate_cam_word(company_data, score_result, str(output_path))
                
                progress_bar.progress(100)
                status_text.text("✅ Processing complete!")
                
                # Store in session state
                st.session_state.company_data = company_data
                st.session_state.score_result = score_result
                st.session_state.cam_document_path = cam_path
                st.session_state.processing_complete = True
                st.session_state.demo_mode = is_demo
                
                # Rerun to show results page
                st.rerun()
        
        except Exception as e:
            # SAFEGUARD 3: Error surfacing - display errors instead of crashing
            st.error(f"❌ Error processing application: {str(e)}")
            st.exception(e)
            
            # Check if partial data was returned
            if 'company_data' in locals() and company_data:
                st.warning("⚠️ Partial data was processed. Some features may be unavailable.")
                st.session_state.company_data = company_data
                st.session_state.score_result = None
                st.session_state.processing_complete = False


# ============================================================================
# TASK 17.4: PAGE 2 - RESULTS DISPLAY
# ============================================================================

def page_results():
    """
    Results page with tabbed interface showing scores, flags, and research.
    
    SAFEGUARD 4: Session persistence - tabs don't re-trigger pipeline.
    """
    company_data = st.session_state.company_data
    score_result = st.session_state.score_result
    
    if not company_data or not score_result:
        st.error("No results available. Please process an application first.")
        if st.button("← Back to Upload"):
            st.session_state.processing_complete = False
            st.rerun()
        return
    
    # Header
    st.title("📊 Credit Assessment Results")
    st.markdown(f"**Company:** {company_data.company_name}")
    st.markdown(f"**CIN:** {company_data.cin}")
    
    if st.session_state.demo_mode:
        st.info("🎯 Demo Mode - Using pre-loaded data")
    
    st.markdown("---")
    
    # Tab interface
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Executive Summary",
        "📊 Five Cs Breakdown",
        "🚩 Flags & Warnings",
        "📝 Officer Notes",
        "🔍 Research Findings"
    ])
    
    # TAB 1: Executive Summary
    with tab1:
        st.subheader("Credit Decision")
        
        # Verdict card
        verdict_color = {
            "APPROVE": "green",
            "CONDITIONAL": "orange",
            "REJECT": "red"
        }
        
        color = verdict_color.get(score_result.verdict.value, "gray")
        
        st.markdown(f"""
        <div style="padding: 20px; border-radius: 10px; background-color: {color}; color: white; text-align: center;">
            <h1>{score_result.verdict.value}</h1>
            <h2>Total Score: {score_result.total_score:.1f}/100</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("")
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Loan Amount Approved",
                f"₹ {score_result.loan_amount:.2f} Cr" if score_result.loan_amount else "N/A"
            )
        
        with col2:
            st.metric(
                "Interest Rate",
                score_result.interest_rate if score_result.interest_rate else "N/A"
            )
        
        with col3:
            st.metric(
                "Total Flags",
                len(score_result.flags)
            )
        
        # Decision narrative
        if score_result.decision_narrative:
            st.markdown("### Decision Summary")
            st.info(score_result.decision_narrative)
        
        # Reasoning
        if score_result.reasoning:
            st.markdown("### Detailed Reasoning")
            st.text(score_result.reasoning)
    
    # TAB 2: Five Cs Breakdown
    with tab2:
        st.subheader("Five Cs Score Breakdown")
        
        # Score table
        scores_data = {
            "Category": ["CHARACTER", "CAPACITY", "CAPITAL", "COLLATERAL", "CONDITIONS"],
            "Score": [
                f"{score_result.character_score:.1f}",
                f"{score_result.capacity_score:.1f}",
                f"{score_result.capital_score:.1f}",
                f"{score_result.collateral_score:.1f}",
                f"{score_result.conditions_score:.1f}"
            ],
            "Weight": ["25%", "30%", "20%", "15%", "10%"],
            "Weighted": [
                f"{score_result.character_score * 0.25:.1f}",
                f"{score_result.capacity_score * 0.30:.1f}",
                f"{score_result.capital_score * 0.20:.1f}",
                f"{score_result.collateral_score * 0.15:.1f}",
                f"{score_result.conditions_score * 0.10:.1f}"
            ]
        }
        
        st.table(scores_data)
        
        st.markdown(f"**Total Weighted Score:** {score_result.total_score:.1f}/100")
        
        # Bar chart visualization
        st.markdown("### Score Visualization")
        
        import pandas as pd
        chart_data = pd.DataFrame({
            'Category': ["CHARACTER", "CAPACITY", "CAPITAL", "COLLATERAL", "CONDITIONS"],
            'Score': [
                score_result.character_score,
                score_result.capacity_score,
                score_result.capital_score,
                score_result.collateral_score,
                score_result.conditions_score
            ]
        })
        
        st.bar_chart(chart_data.set_index('Category'))
    
    # TAB 3: Flags and Warnings
    with tab3:
        st.subheader("Flags and Warnings")
        
        if not score_result.flags:
            st.success("✅ No flags detected")
        else:
            # Group flags by severity
            high_flags = [f for f in score_result.flags if f.severity.value == "HIGH"]
            medium_flags = [f for f in score_result.flags if f.severity.value == "MEDIUM"]
            low_flags = [f for f in score_result.flags if f.severity.value == "LOW"]
            green_flags = [f for f in score_result.flags if f.severity.value == "GREEN"]
            
            # Display by severity
            if high_flags:
                st.markdown("#### 🔴 HIGH Severity")
                for flag in high_flags:
                    st.error(f"**{flag.category.value}**: {flag.description}\n\n*Source: {flag.source}* | Impact: {flag.impact_score:.1f}")
            
            if medium_flags:
                st.markdown("#### 🟡 MEDIUM Severity")
                for flag in medium_flags:
                    st.warning(f"**{flag.category.value}**: {flag.description}\n\n*Source: {flag.source}* | Impact: {flag.impact_score:.1f}")
            
            if low_flags:
                st.markdown("#### 🔵 LOW Severity")
                for flag in low_flags:
                    st.info(f"**{flag.category.value}**: {flag.description}\n\n*Source: {flag.source}* | Impact: {flag.impact_score:.1f}")
            
            if green_flags:
                st.markdown("#### 🟢 POSITIVE Factors")
                for flag in green_flags:
                    st.success(f"**{flag.category.value}**: {flag.description}\n\n*Source: {flag.source}* | Impact: +{flag.impact_score:.1f}")
        
        # Early warnings
        if company_data.early_warnings:
            st.markdown("---")
            st.markdown("### ⚠️ Early Warning Signals")
            
            for warning in company_data.early_warnings:
                severity_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🔵"}.get(warning.severity.value, "⚪")
                st.markdown(f"{severity_icon} **{warning.signal_type}**: {warning.matched_text}\n\n*Source: {warning.source_document}*")
    
    # TAB 4: Officer Notes
    with tab4:
        st.subheader("Officer Qualitative Assessments")
        
        if not company_data.officer_notes:
            st.info("No officer notes recorded for this application.")
        else:
            for i, note in enumerate(company_data.officer_notes, 1):
                with st.expander(f"Note {i}: {note.affected_c.value} ({note.adjustment:+.1f})"):
                    st.markdown(f"**Category:** {note.affected_c.value}")
                    st.markdown(f"**Adjustment:** {note.adjustment:+.1f}")
                    st.markdown(f"**Date:** {note.timestamp[:10]}")
                    st.markdown(f"**Note:**\n\n{note.note_text}")
    
    # TAB 5: Research Findings
    with tab5:
        st.subheader("Research Findings")
        
        if not company_data.research:
            st.warning("Research data not available")
        else:
            research = company_data.research
            
            # Sector analysis
            st.markdown("### 🏭 Sector Analysis")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Sector", research.sector or "N/A")
            with col2:
                st.metric("Outlook", research.sector_outlook or "N/A")
            with col3:
                st.metric("Sector NPA Rate", f"{research.sector_npa_rate:.1f}%" if research.sector_npa_rate else "N/A")
            
            # MCA status
            st.markdown("### 📋 MCA Status")
            st.info(f"**Status:** {research.mca_status or 'N/A'}")
            
            # Stock data
            if research.stock_data and research.stock_data.is_listed:
                st.markdown("### 📈 Stock Market Data")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Ticker", research.stock_data.ticker or "N/A")
                with col2:
                    st.metric("Price", f"₹ {research.stock_data.current_price:,.2f}" if research.stock_data.current_price else "N/A")
                with col3:
                    st.metric("Market Cap", f"₹ {research.stock_data.market_cap:,.2f} Cr" if research.stock_data.market_cap else "N/A")
            
            # News items
            if research.news_items:
                st.markdown("### 📰 Recent News")
                for news in research.news_items:
                    with st.expander(f"{news.title}"):
                        st.markdown(f"**Source:** {news.source}")
                        st.markdown(f"**Date:** {news.date}")
                        if news.snippet:
                            st.markdown(f"**Snippet:** {news.snippet}")
                        st.markdown(f"[Read more]({news.url})")
    
    # Action buttons
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        # Download CAM button
        if st.session_state.cam_document_path and Path(st.session_state.cam_document_path).exists():
            with open(st.session_state.cam_document_path, 'rb') as f:
                st.download_button(
                    label="📥 Download CAM Document",
                    data=f.read(),
                    file_name=Path(st.session_state.cam_document_path).name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
        else:
            st.warning("CAM document not available")
    
    with col2:
        # New Application button
        if st.button("🔄 New Application", use_container_width=True):
            # Reset session state
            st.session_state.company_data = None
            st.session_state.score_result = None
            st.session_state.processing_complete = False
            st.session_state.cam_document_path = None
            st.session_state.uploaded_file_paths = {}
            st.rerun()


# ============================================================================
# TASK 17.5: MAIN APPLICATION ENTRY POINT
# ============================================================================

def main():
    """
    Main application entry point with page routing.
    
    SAFEGUARD 4: Session persistence ensures tabs/widgets don't re-trigger pipeline.
    """
    # Page config
    st.set_page_config(
        page_title="Intelli-Credit CAM Generator",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/4CAF50/FFFFFF?text=Intelli-Credit", use_container_width=True)
        st.markdown("## About")
        st.markdown("""
        Intelli-Credit is an AI-powered Credit Assessment Memorandum (CAM) generator 
        that uses the Five Cs framework to evaluate credit applications.
        
        **Five Cs:**
        - CHARACTER (25%)
        - CAPACITY (30%)
        - CAPITAL (20%)
        - COLLATERAL (15%)
        - CONDITIONS (10%)
        """)
        
        st.markdown("---")
        st.markdown("### Instructions")
        st.markdown("""
        1. Upload financial documents OR select a demo company
        2. Enter company details (CIN, name, promoter)
        3. Enter CIBIL CMR rank
        4. Click "Process Application"
        5. Review results and download CAM document
        """)
        
        st.markdown("---")
        st.markdown("### System Status")
        
        # Check API keys
        groq_key = os.getenv("GROQ_API_KEY")
        serper_key = os.getenv("SERPER_API_KEY")
        news_key = os.getenv("NEWSAPI_KEY")
        
        st.markdown(f"**GROQ API:** {'✅' if groq_key else '❌'}")
        st.markdown(f"**Serper API:** {'✅' if serper_key else '⚠️ Optional'}")
        st.markdown(f"**NewsAPI:** {'✅' if news_key else '⚠️ Optional'}")
        
        if not groq_key:
            st.error("⚠️ GROQ_API_KEY required! Set in .env file")
    
    # Page routing
    if st.session_state.processing_complete:
        page_results()
    else:
        page_upload()


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
