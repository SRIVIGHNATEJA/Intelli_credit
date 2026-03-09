"""
Intelli-Credit - Professional Fintech Dashboard
AI-powered Credit Assessment Memorandum Generator

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
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

from data_models import CompanyData, ScoreResult
from pipeline import process_application
from scorer import calculate_five_cs
from report_generator import generate_cam_word
from dummy_data import get_demo_companies_list, get_demo_company_info

load_dotenv()


# ============================================================================
# CUSTOM CSS - ADVANCED FINTECH STYLING
# ============================================================================

def inject_custom_css():
    """Inject advanced custom CSS for professional fintech dashboard"""
    st.markdown("""
    <style>
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Main container */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 1600px;
        }
        
        /* Hero header gradient */
        .hero-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2.5rem 2rem;
            border-radius: 16px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }
        
        .hero-title {
            font-size: 3rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: -1px;
        }
        
        .hero-subtitle {
            font-size: 1.2rem;
            opacity: 0.95;
            margin-top: 0.5rem;
            font-weight: 400;
        }
        
        /* Decision banners */
        .decision-approve {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            padding: 3rem 2rem;
            border-radius: 20px;
            color: white;
            text-align: center;
            margin: 2rem 0;
            box-shadow: 0 20px 40px rgba(16, 185, 129, 0.3);
            animation: slideIn 0.5s ease-out;
        }
        
        .decision-reject {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            padding: 3rem 2rem;
            border-radius: 20px;
            color: white;
            text-align: center;
            margin: 2rem 0;
            box-shadow: 0 20px 40px rgba(239, 68, 68, 0.3);
            animation: slideIn 0.5s ease-out;
        }
        
        .decision-conditional {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            padding: 3rem 2rem;
            border-radius: 20px;
            color: white;
            text-align: center;
            margin: 2rem 0;
            box-shadow: 0 20px 40px rgba(245, 158, 11, 0.3);
            animation: slideIn 0.5s ease-out;
        }
        
        .decision-verdict {
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 1rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .decision-score {
            font-size: 2.2rem;
            font-weight: 600;
            opacity: 0.95;
        }
        
        .decision-meta {
            margin-top: 1.5rem;
            font-size: 1.3rem;
            opacity: 0.9;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Upload card panels */
        .upload-panel {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            border: 2px solid #e5e7eb;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        
        .upload-panel:hover {
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
        }
        
        /* Metric cards */
        .metric-card {
            background: white;
            padding: 1.8rem;
            border-radius: 14px;
            border-left: 5px solid #667eea;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            transition: transform 0.2s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: #1f2937;
            margin: 0.8rem 0;
            line-height: 1;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        .metric-icon {
            font-size: 2rem;
            opacity: 0.8;
        }
        
        /* Risk flag cards */
        .flag-card-high {
            background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
            border-left: 5px solid #dc2626;
            padding: 1.2rem;
            border-radius: 10px;
            margin-bottom: 0.8rem;
            box-shadow: 0 2px 6px rgba(220, 38, 38, 0.15);
        }
        
        .flag-card-medium {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-left: 5px solid #f59e0b;
            padding: 1.2rem;
            border-radius: 10px;
            margin-bottom: 0.8rem;
            box-shadow: 0 2px 6px rgba(245, 158, 11, 0.15);
        }
        
        .flag-card-low {
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            border-left: 5px solid #3b82f6;
            padding: 1.2rem;
            border-radius: 10px;
            margin-bottom: 0.8rem;
            box-shadow: 0 2px 6px rgba(59, 130, 246, 0.15);
        }
        
        .flag-card-green {
            background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
            border-left: 5px solid #10b981;
            padding: 1.2rem;
            border-radius: 10px;
            margin-bottom: 0.8rem;
            box-shadow: 0 2px 6px rgba(16, 185, 129, 0.15);
        }
        
        /* Button styling */
        .stButton > button {
            border-radius: 10px;
            font-weight: 700;
            padding: 0.9rem 2.5rem;
            font-size: 1.1rem;
            transition: all 0.3s ease;
            border: none;
        }
        
        .stButton > button:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            background-color: #f9fafb;
            padding: 0.5rem;
            border-radius: 12px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            padding: 14px 28px;
            font-weight: 700;
            font-size: 1rem;
            background-color: white;
            border: 2px solid transparent;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background-color: #f3f4f6;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #667eea !important;
            color: white !important;
            border-color: #667eea !important;
        }
        
        /* Section headers */
        .section-header {
            font-size: 1.8rem;
            font-weight: 700;
            color: #1f2937;
            margin: 2rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #667eea;
        }
        
        /* Status indicators */
        .status-active {
            color: #10b981;
            font-weight: 600;
        }
        
        .status-inactive {
            color: #ef4444;
            font-weight: 600;
        }
        
        .status-optional {
            color: #f59e0b;
            font-weight: 600;
        }
        
        /* Reduce whitespace */
        .element-container {
            margin-bottom: 0.5rem;
        }
        
        /* Card container */
        .card-container {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)



# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize session state - SAFEGUARD 1 & 4"""
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
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Application Intake"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def render_metric_card(label: str, value: str, icon: str, border_color: str = "#667eea"):
    """Render professional metric card with icon"""
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: {border_color};">
        <div class="metric-icon">{icon}</div>
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def render_decision_banner(verdict: str, score: float, interest_rate: str, flags_count: int):
    """Render credit decision banner with gradient"""
    verdict_config = {
        "APPROVE": {
            "class": "decision-approve",
            "emoji": "✅",
            "title": "APPROVED"
        },
        "REJECT": {
            "class": "decision-reject",
            "emoji": "❌",
            "title": "REJECTED"
        },
        "CONDITIONAL": {
            "class": "decision-conditional",
            "emoji": "⚠️",
            "title": "CONDITIONAL APPROVAL"
        }
    }
    
    config = verdict_config.get(verdict, verdict_config["REJECT"])
    
    st.markdown(f"""
    <div class="{config['class']}">
        <div class="decision-verdict">{config['emoji']} {config['title']}</div>
        <div class="decision-score">Credit Score: {score:.1f}/100</div>
        <div class="decision-meta">
            Interest Rate: {interest_rate} | Risk Flags: {flags_count}
        </div>
    </div>
    """, unsafe_allow_html=True)


def create_five_cs_plotly_chart(score_result: ScoreResult):
    """Create interactive Five Cs bar chart"""
    categories = ['CHARACTER', 'CAPACITY', 'CAPITAL', 'COLLATERAL', 'CONDITIONS']
    scores = [
        score_result.character_score,
        score_result.capacity_score,
        score_result.capital_score,
        score_result.collateral_score,
        score_result.conditions_score
    ]
    weights = [25, 30, 20, 15, 10]
    
    colors = []
    for score in scores:
        if score >= 70:
            colors.append('#10b981')
        elif score >= 50:
            colors.append('#f59e0b')
        else:
            colors.append('#ef4444')
    
    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=scores,
            marker_color=colors,
            marker_line_color='rgba(0,0,0,0.1)',
            marker_line_width=2,
            text=[f'{s:.1f}' for s in scores],
            textposition='outside',
            textfont=dict(size=14, color='#1f2937', family='sans-serif'),
            hovertemplate='<b>%{x}</b><br>Score: %{y:.1f}/100<br>Weight: %{customdata}%<extra></extra>',
            customdata=weights
        )
    ])
    
    fig.update_layout(
        title={
            'text': 'Five Cs Credit Assessment Framework',
            'font': {'size': 20, 'color': '#1f2937', 'family': 'sans-serif'}
        },
        xaxis_title='Credit Factor',
        yaxis_title='Score (out of 100)',
        yaxis_range=[0, 110],
        height=450,
        template='plotly_white',
        font=dict(size=13, family='sans-serif'),
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=80, b=60, l=60, r=40)
    )
    
    fig.update_xaxes(showgrid=False, showline=True, linewidth=2, linecolor='#e5e7eb')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f3f4f6')
    
    return fig


# ============================================================================
# PAGE: APPLICATION INTAKE
# ============================================================================

def page_application_intake():
    """Application intake page with professional layout"""
    
    # Hero header
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">🏦 Intelli-Credit</div>
        <div class="hero-subtitle">AI-Powered Credit Risk Assessment using the Five Cs Framework</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">📋 Application Intake</div>', unsafe_allow_html=True)
    st.markdown("Upload financial documents or select a demo company to begin credit assessment")
    st.markdown("")
    
    # Two-column layout
    col_left, col_right = st.columns([1.3, 1], gap="large")
    
    # ========== LEFT: DOCUMENT UPLOADS ==========
    with col_left:
        st.markdown("#### 📁 Financial Document Upload")
        
        uploaded_files = {}
        
        # Upload panels with card styling
        docs = [
            ("balance_sheet", "📊 Balance Sheet", "Upload company balance sheet"),
            ("profit_loss", "📈 Profit & Loss Statement", "Upload P&L statement"),
            ("bank_statements", "🏦 Bank Statements", "Upload bank statements (last 12 months)"),
            ("gst_returns", "📋 GST Returns", "Upload GST returns"),
            ("itr", "💼 Income Tax Returns", "Upload ITR"),
            ("sanction_letter", "📄 Sanction Letter", "Upload loan sanction letter")
        ]
        
        for doc_key, doc_label, doc_help in docs:
            with st.container():
                st.markdown('<div class="upload-panel">', unsafe_allow_html=True)
                uploaded_file = st.file_uploader(
                    doc_label,
                    type=['pdf'],
                    key=doc_key,
                    help=f"{doc_help} (PDF format, max 8MB)"
                )
                if uploaded_file:
                    upload_path = Path("uploads") / uploaded_file.name
                    upload_path.parent.mkdir(exist_ok=True)
                    with open(upload_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    uploaded_files[doc_key] = str(upload_path)
                    st.success(f"✓ {uploaded_file.name} uploaded")
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.session_state.uploaded_file_paths = uploaded_files
    
    # ========== RIGHT: DEMO & COMPANY DETAILS ==========
    with col_right:
        st.markdown("#### 🎯 Demo Mode")
        
        demo_companies = get_demo_companies_list()
        demo_options = ["None (Real Mode)"] + demo_companies
        
        selected_demo = st.selectbox(
            "Select Demo Company",
            options=demo_options,
            help="Choose pre-loaded demo or process uploaded documents"
        )
        
        demo_info = None
        if selected_demo != "None (Real Mode)":
            demo_info = get_demo_company_info(selected_demo)
            if demo_info:
                st.info(f"**{demo_info['company_name']}**\n\nCIN: {demo_info['cin']}\n\nExpected: {demo_info['expected_verdict'].value}")
                
                cache_path = Path("demo_cache") / demo_info['cache_file']
                if not cache_path.exists():
                    st.warning("⚠️ Demo cache not generated yet")
        
        st.markdown("")
        st.markdown("#### 🏢 Company Information")
        
        cin_input = st.text_input(
            "Corporate Identification Number (CIN)",
            value=demo_info['cin'] if demo_info else "",
            help="21-character CIN from MCA"
        )
        
        company_name_input = st.text_input(
            "Company Name",
            value=demo_info['company_name'] if demo_info else "",
            help="Legal name of the company"
        )
        
        promoter_name_input = st.text_input(
            "Promoter Name",
            help="Primary promoter/director name"
        )
        
        st.markdown("")
        st.markdown("#### 🔒 Compliance Check")
        
        with st.container():
            st.markdown('<div class="card-container">', unsafe_allow_html=True)
            cibil_score = st.number_input(
                "CIBIL Commercial CMR Rank (1-10)",
                min_value=1,
                max_value=10,
                value=3,
                help="1 = Highest risk, 10 = Lowest risk"
            )
            
            if cibil_score > 6:
                st.warning("⚠️ High Risk CMR - Auto-routing to Senior Credit Committee")
            else:
                st.success("✓ CMR within acceptable range")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Process button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        process_button = st.button(
            "🚀 Process Credit Application",
            type="primary",
            use_container_width=True
        )
    
    if process_button:
        if not cin_input or not company_name_input:
            st.error("❌ Please provide CIN and Company Name")
            return
        
        is_demo = selected_demo != "None (Real Mode)"
        
        if not is_demo and not st.session_state.uploaded_file_paths:
            st.error("❌ Please upload at least one document or select demo")
            return
        
        try:
            # SAFEGUARD 2: Skeleton loading with st.status
            with st.status("🔄 Processing Credit Application...", expanded=True) as status:
                st.write("📤 Step 1/6: Uploading documents...")
                
                st.write("🤖 Step 2/6: AI extraction from PDFs...")
                
                company_data = process_application(
                    cin=cin_input,
                    company_name=company_name_input,
                    promoter_name=promoter_name_input if promoter_name_input else None,
                    uploaded_files=st.session_state.uploaded_file_paths if not is_demo else None,
                    demo_mode=is_demo,
                    demo_company_key=selected_demo if is_demo else None
                )
                
                st.write("🔍 Step 3/6: Fraud detection & GST analysis...")
                
                st.write("🌐 Step 4/6: Company research & intelligence...")
                
                st.write("📊 Step 5/6: Calculating Five Cs score...")
                
                score_result = calculate_five_cs(company_data)
                
                st.write("📄 Step 6/6: Generating CAM document...")
                
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                output_path = output_dir / f"CAM_{cin_input}_{company_name_input.replace(' ', '_')}.docx"
                
                cam_path = generate_cam_word(company_data, score_result, str(output_path))
                
                status.update(label="✅ Processing Complete!", state="complete", expanded=False)
            
            # Store in session state
            st.session_state.company_data = company_data
            st.session_state.score_result = score_result
            st.session_state.cam_document_path = cam_path
            st.session_state.processing_complete = True
            st.session_state.demo_mode = is_demo
            st.session_state.current_page = "Credit Analysis"
            
            st.toast("✅ CAM report generated successfully!", icon="✅")
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.exception(e)
            
            if 'company_data' in locals() and company_data:
                st.warning("⚠️ Partial data processed")
                st.session_state.company_data = company_data
                st.session_state.score_result = None
                st.session_state.processing_complete = False



# ============================================================================
# PAGE: CREDIT ANALYSIS DASHBOARD
# ============================================================================

def page_credit_analysis():
    """Main credit analysis dashboard - SAFEGUARD 4"""
    
    company_data = st.session_state.company_data
    score_result = st.session_state.score_result
    
    if not company_data or not score_result:
        st.error("No results available")
        if st.button("← Back"):
            st.session_state.processing_complete = False
            st.session_state.current_page = "Application Intake"
            st.rerun()
        return
    
    # Header
    st.markdown(f"""
    <div class="hero-header">
        <div class="hero-title">📊 Credit Assessment Report</div>
        <div class="hero-subtitle">{company_data.company_name} | CIN: {company_data.cin}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.demo_mode:
        st.info("🎯 Demo Mode Active")
    
    # Decision banner
    render_decision_banner(
        verdict=score_result.verdict.value,
        score=score_result.total_score,
        interest_rate=score_result.interest_rate if score_result.interest_rate else "N/A",
        flags_count=len(score_result.flags)
    )
    
    st.markdown("")
    
    # Metric cards
    st.markdown('<div class="section-header">📊 Key Performance Indicators</div>', unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4, gap="medium")
    
    with m1:
        render_metric_card(
            "Credit Score",
            f"{score_result.total_score:.1f}",
            "🎯",
            "#667eea"
        )
    
    with m2:
        render_metric_card(
            "Interest Rate",
            score_result.interest_rate if score_result.interest_rate else "N/A",
            "💰",
            "#10b981"
        )
    
    with m3:
        render_metric_card(
            "Risk Flags",
            str(len(score_result.flags)),
            "🚩",
            "#ef4444"
        )
    
    with m4:
        loan_amt = f"₹{score_result.loan_amount:.1f}Cr" if score_result.loan_amount else "REJECTED"
        border = "#10b981" if score_result.loan_amount else "#ef4444"
        render_metric_card(
            "Approved Amount",
            loan_amt,
            "✅" if score_result.loan_amount else "❌",
            border
        )
    
    st.markdown("")
    
    # Five Cs chart
    st.markdown('<div class="section-header">📈 Five Cs Breakdown</div>', unsafe_allow_html=True)
    fig = create_five_cs_plotly_chart(score_result)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("")
    
    # Detailed tabs
    st.markdown('<div class="section-header">📑 Detailed Analysis</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs([
        "📋 Executive Summary",
        "📊 Five Cs Details",
        "🔍 Additional Insights"
    ])
    
    with tab1:
        if score_result.decision_narrative:
            st.markdown("**Decision Rationale:**")
            st.info(score_result.decision_narrative)
        
        if score_result.reasoning:
            st.markdown("**Detailed Analysis:**")
            st.text_area("", value=score_result.reasoning, height=200, disabled=True, label_visibility="collapsed")
        
        st.markdown("**Score Breakdown:**")
        summary_df = pd.DataFrame({
            "Category": ["CHARACTER", "CAPACITY", "CAPITAL", "COLLATERAL", "CONDITIONS", "TOTAL"],
            "Raw Score": [
                f"{score_result.character_score:.1f}",
                f"{score_result.capacity_score:.1f}",
                f"{score_result.capital_score:.1f}",
                f"{score_result.collateral_score:.1f}",
                f"{score_result.conditions_score:.1f}",
                "-"
            ],
            "Weight": ["25%", "30%", "20%", "15%", "10%", "100%"],
            "Weighted": [
                f"{score_result.character_score * 0.25:.1f}",
                f"{score_result.capacity_score * 0.30:.1f}",
                f"{score_result.capital_score * 0.20:.1f}",
                f"{score_result.collateral_score * 0.15:.1f}",
                f"{score_result.conditions_score * 0.10:.1f}",
                f"{score_result.total_score:.1f}"
            ]
        })
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    with tab2:
        categories = [
            ("👤 CHARACTER", score_result.character_score, 0.25, "CHARACTER"),
            ("💼 CAPACITY", score_result.capacity_score, 0.30, "CAPACITY"),
            ("💰 CAPITAL", score_result.capital_score, 0.20, "CAPITAL"),
            ("🏠 COLLATERAL", score_result.collateral_score, 0.15, "COLLATERAL"),
            ("🌍 CONDITIONS", score_result.conditions_score, 0.10, "CONDITIONS")
        ]
        
        for label, score, weight, cat_name in categories:
            with st.expander(f"{label} ({int(weight*100)}% weight)", expanded=False):
                st.markdown(f"**Score:** {score:.1f}/100")
                st.markdown(f"**Weighted Contribution:** {score * weight:.1f}")
                
                cat_flags = [f for f in score_result.flags if f.category.value == cat_name]
                if cat_flags:
                    st.markdown(f"**Flags Detected:** {len(cat_flags)}")
                    for flag in cat_flags:
                        st.markdown(f"- {flag.description} ({flag.impact_score:+.1f})")
                else:
                    st.success("✓ No flags in this category")
    
    with tab3:
        if company_data.officer_notes:
            st.markdown("**Officer Notes:**")
            for i, note in enumerate(company_data.officer_notes, 1):
                st.markdown(f"**{i}. {note.affected_c.value}** ({note.adjustment:+.1f})")
                st.caption(note.note_text)
                st.caption(f"Date: {note.timestamp[:10]}")
                st.markdown("")
        
        if company_data.research:
            st.markdown("**Research Summary:**")
            st.markdown(f"- Sector: {company_data.research.sector or 'N/A'}")
            st.markdown(f"- Outlook: {company_data.research.sector_outlook or 'N/A'}")
            st.markdown(f"- MCA Status: {company_data.research.mca_status or 'N/A'}")



# ============================================================================
# PAGE: RISK FLAGS
# ============================================================================

def page_risk_flags():
    """Risk flags detailed view"""
    
    score_result = st.session_state.score_result
    company_data = st.session_state.company_data
    
    if not score_result:
        st.error("No data available")
        return
    
    st.markdown('<div class="section-header">🚩 Risk Flags & Warnings</div>', unsafe_allow_html=True)
    
    if not score_result.flags:
        st.success("✅ No risk flags detected - Clean credit profile")
        return
    
    # Summary metrics
    high_count = len([f for f in score_result.flags if f.severity.value == "HIGH"])
    medium_count = len([f for f in score_result.flags if f.severity.value == "MEDIUM"])
    low_count = len([f for f in score_result.flags if f.severity.value == "LOW"])
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Flags", len(score_result.flags))
    with c2:
        st.metric("🔴 High", high_count)
    with c3:
        st.metric("🟡 Medium", medium_count)
    with c4:
        st.metric("🔵 Low", low_count)
    
    st.markdown("")
    
    # Flags by severity
    high_flags = [f for f in score_result.flags if f.severity.value == "HIGH"]
    medium_flags = [f for f in score_result.flags if f.severity.value == "MEDIUM"]
    low_flags = [f for f in score_result.flags if f.severity.value == "LOW"]
    green_flags = [f for f in score_result.flags if f.severity.value == "GREEN"]
    
    if high_flags:
        st.markdown("### 🔴 HIGH Severity Flags")
        for flag in high_flags:
            st.markdown(f"""
            <div class="flag-card-high">
                <strong style="font-size: 1.1rem;">{flag.category.value}</strong><br>
                <span style="font-size: 1rem;">{flag.description}</span><br>
                <small style="opacity: 0.8;">Source: {flag.source} | Impact: {flag.impact_score:.1f}</small>
            </div>
            """, unsafe_allow_html=True)
    
    if medium_flags:
        st.markdown("### 🟡 MEDIUM Severity Flags")
        for flag in medium_flags:
            st.markdown(f"""
            <div class="flag-card-medium">
                <strong style="font-size: 1.1rem;">{flag.category.value}</strong><br>
                <span style="font-size: 1rem;">{flag.description}</span><br>
                <small style="opacity: 0.8;">Source: {flag.source} | Impact: {flag.impact_score:.1f}</small>
            </div>
            """, unsafe_allow_html=True)
    
    if low_flags:
        st.markdown("### 🔵 LOW Severity Flags")
        for flag in low_flags:
            st.markdown(f"""
            <div class="flag-card-low">
                <strong style="font-size: 1.1rem;">{flag.category.value}</strong><br>
                <span style="font-size: 1rem;">{flag.description}</span><br>
                <small style="opacity: 0.8;">Source: {flag.source} | Impact: {flag.impact_score:.1f}</small>
            </div>
            """, unsafe_allow_html=True)
    
    if green_flags:
        st.markdown("### 🟢 POSITIVE Factors")
        for flag in green_flags:
            st.markdown(f"""
            <div class="flag-card-green">
                <strong style="font-size: 1.1rem;">{flag.category.value}</strong><br>
                <span style="font-size: 1rem;">{flag.description}</span><br>
                <small style="opacity: 0.8;">Source: {flag.source} | Impact: +{flag.impact_score:.1f}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Early warnings
    if company_data.early_warnings:
        st.markdown("---")
        st.markdown("### ⚠️ Early Warning Signals")
        
        for warning in company_data.early_warnings:
            severity_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🔵"}.get(warning.severity.value, "⚪")
            st.markdown(f"""
            <div class="card-container">
                {severity_icon} <strong>{warning.signal_type}</strong><br>
                {warning.matched_text}<br>
                <small>Source: {warning.source_document}</small>
            </div>
            """, unsafe_allow_html=True)


# ============================================================================
# PAGE: RESEARCH INSIGHTS
# ============================================================================

def page_research():
    """Research insights page"""
    
    company_data = st.session_state.company_data
    
    if not company_data or not company_data.research:
        st.warning("Research data not available")
        return
    
    research = company_data.research
    
    st.markdown('<div class="section-header">🔍 Research & Intelligence</div>', unsafe_allow_html=True)
    
    # Sector analysis
    st.markdown("### 🏭 Sector Analysis")
    
    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Sector", research.sector or "N/A")
    with s2:
        outlook_emoji = {"POSITIVE": "📈", "NEUTRAL": "➡️", "DISTRESSED": "📉"}.get(research.sector_outlook, "")
        st.metric("Outlook", f"{outlook_emoji} {research.sector_outlook or 'N/A'}")
    with s3:
        st.metric("Sector NPA", f"{research.sector_npa_rate:.1f}%" if research.sector_npa_rate else "N/A")
    
    st.markdown("")
    
    # MCA status
    st.markdown("### 📋 MCA Compliance")
    mca_status = research.mca_status or "N/A"
    if "Active" in mca_status:
        st.success(f"✅ {mca_status}")
    else:
        st.warning(f"⚠️ {mca_status}")
    
    st.markdown("")
    
    # Stock data
    if research.stock_data and research.stock_data.is_listed:
        st.markdown("### 📈 Stock Market Data")
        
        st1, st2, st3, st4 = st.columns(4)
        with st1:
            st.metric("Ticker", research.stock_data.ticker or "N/A")
        with st2:
            st.metric("Price", f"₹{research.stock_data.current_price:,.2f}" if research.stock_data.current_price else "N/A")
        with st3:
            st.metric("Market Cap", f"₹{research.stock_data.market_cap:,.0f}Cr" if research.stock_data.market_cap else "N/A")
        with st4:
            st.metric("52W High", f"₹{research.stock_data.week_52_high:,.2f}" if research.stock_data.week_52_high else "N/A")
        
        st.markdown("")
    
    # News
    if research.news_items:
        st.markdown("### 📰 Recent News Coverage")
        
        for news in research.news_items:
            st.markdown(f"""
            <div class="card-container">
                <h4 style="margin: 0 0 0.5rem 0;">{news.title}</h4>
                <p style="margin: 0.5rem 0; color: #6b7280;">
                    <strong>Source:</strong> {news.source} | <strong>Date:</strong> {news.date}
                </p>
                <p style="margin: 0.5rem 0;">{news.snippet if news.snippet else ''}</p>
                <a href="{news.url}" target="_blank" style="color: #667eea; text-decoration: none; font-weight: 600;">
                    Read full article →
                </a>
            </div>
            """, unsafe_allow_html=True)



# ============================================================================
# PAGE: CAM REPORT
# ============================================================================

def page_cam_report():
    """CAM report download page"""
    
    st.markdown('<div class="section-header">📄 CAM Report</div>', unsafe_allow_html=True)
    
    if st.session_state.cam_document_path and Path(st.session_state.cam_document_path).exists():
        st.success("✅ CAM document generated successfully")
        
        st.markdown("### Download Options")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with open(st.session_state.cam_document_path, 'rb') as f:
                st.download_button(
                    label="📥 Download CAM Document (.docx)",
                    data=f.read(),
                    file_name=Path(st.session_state.cam_document_path).name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
        
        with col2:
            if st.button("🔄 New Application", use_container_width=True):
                st.session_state.company_data = None
                st.session_state.score_result = None
                st.session_state.processing_complete = False
                st.session_state.cam_document_path = None
                st.session_state.uploaded_file_paths = {}
                st.session_state.current_page = "Application Intake"
                st.toast("Ready for new application", icon="🔄")
                st.rerun()
        
        st.markdown("")
        st.markdown("### Document Contents")
        st.info("""
        The CAM document includes:
        - Executive Summary with credit decision
        - Company Overview (CIN, Sector, MCA Status)
        - Financial Analysis (Revenue, Ratios, Banking Conduct)
        - Five Cs Breakdown with all flags
        - GST Analysis
        - Research Findings
        - Officer Notes
        - Final Recommendation
        """)
    else:
        st.warning("CAM document not available")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application with navigation - SAFEGUARD 4"""
    
    st.set_page_config(
        page_title="Intelli-Credit | Credit Risk Console",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    inject_custom_css()
    initialize_session_state()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("# 🏦 Intelli-Credit")
        st.markdown("**Credit Risk Console**")
        st.markdown("---")
        
        # Navigation menu
        if st.session_state.processing_complete:
            menu_options = [
                "Application Intake",
                "Credit Analysis",
                "Risk Flags",
                "Research Insights",
                "CAM Report"
            ]
            menu_icons = ["📋", "📊", "🚩", "🔍", "📄"]
        else:
            menu_options = ["Application Intake"]
            menu_icons = ["📋"]
        
        selected = option_menu(
            menu_title=None,
            options=menu_options,
            icons=menu_icons,
            default_index=menu_options.index(st.session_state.current_page) if st.session_state.current_page in menu_options else 0,
            styles={
                "container": {"padding": "0"},
                "nav-link": {
                    "font-size": "0.95rem",
                    "text-align": "left",
                    "margin": "0.2rem",
                    "border-radius": "8px"
                },
                "nav-link-selected": {"background-color": "#667eea"}
            }
        )
        
        st.session_state.current_page = selected
        
        st.markdown("---")
        
        # Five Cs info
        st.markdown("### Five Cs Framework")
        st.markdown("""
        <div style="font-size: 0.85rem; line-height: 1.6;">
        • <strong>CHARACTER</strong> (25%)<br>
        • <strong>CAPACITY</strong> (30%)<br>
        • <strong>CAPITAL</strong> (20%)<br>
        • <strong>COLLATERAL</strong> (15%)<br>
        • <strong>CONDITIONS</strong> (10%)
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # System status
        st.markdown("### System Status")
        
        groq_key = os.getenv("GROQ_API_KEY")
        serper_key = os.getenv("SERPER_API_KEY")
        news_key = os.getenv("NEWSAPI_KEY")
        
        st.markdown(f"""
        <div style="font-size: 0.9rem;">
        <span class="status-{'active' if groq_key else 'inactive'}">● Groq API</span><br>
        <span class="status-{'active' if serper_key else 'optional'}">● Serper API</span><br>
        <span class="status-{'active' if news_key else 'optional'}">● News API</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Page routing
    if st.session_state.current_page == "Application Intake":
        page_application_intake()
    elif st.session_state.current_page == "Credit Analysis":
        page_credit_analysis()
    elif st.session_state.current_page == "Risk Flags":
        page_risk_flags()
    elif st.session_state.current_page == "Research Insights":
        page_research()
    elif st.session_state.current_page == "CAM Report":
        page_cam_report()


if __name__ == "__main__":
    main()
