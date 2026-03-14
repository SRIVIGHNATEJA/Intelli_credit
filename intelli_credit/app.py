"""
Intelli-Credit - Enterprise Fintech Dashboard
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
from officer_portal import collect_officer_notes, apply_officer_adjustments

load_dotenv()


# ============================================================================
# CUSTOM CSS - ENTERPRISE FINTECH STYLING
# ============================================================================

def inject_custom_css():
    """Inject advanced CSS for professional fintech dashboard"""
    st.markdown("""
    <style>
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* Main container */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 1600px;
        }
        
        /* Hero header with gradient */
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
        }
        
        .hero-chips {
            margin-top: 1rem;
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        
        .chip {
            background: rgba(255, 255, 255, 0.2);
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            backdrop-filter: blur(10px);
        }
        
        /* Decision banners with gradients */
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
        
        /* Upload tiles */
        .upload-tile {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            border: 2px dashed #d1d5db;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .upload-tile:hover {
            border-color: #667eea;
            border-style: solid;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
            transform: translateY(-2px);
        }
        
        /* Metric cards */
        .metric-card {
            background: white;
            padding: 1.8rem;
            border-radius: 14px;
            border-left: 5px solid #667eea;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            transition: transform 0.2s ease;
            height: 100%;
        }
        
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
        }
        
        .metric-icon {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: #1f2937;
            margin: 0.5rem 0;
            line-height: 1;
        }
        
        .metric-label {
            font-size: 0.85rem;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
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
        
        /* Card container */
        .card-container {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            margin-bottom: 1rem;
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
        
        /* Button styling */
        .stButton > button {
            border-radius: 10px;
            font-weight: 700;
            padding: 0.9rem 2.5rem;
            font-size: 1.1rem;
            transition: all 0.3s ease;
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
            background-color: white;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #667eea !important;
            color: white !important;
        }
        
        /* Status indicators */
        .status-active { color: #10b981; font-weight: 600; }
        .status-inactive { color: #ef4444; font-weight: 600; }
        .status-optional { color: #f59e0b; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# SESSION STATE
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


def reset_session_state():
    """Reset all processing state for new application"""
    st.session_state.company_data = None
    st.session_state.score_result = None
    st.session_state.processing_complete = False
    st.session_state.demo_mode = False
    st.session_state.cam_document_path = None
    st.session_state.uploaded_file_paths = {}
    st.session_state.current_page = "Application Intake"
    
    # Clear officer notes if they exist
    if 'officer_notes' in st.session_state:
        st.session_state.officer_notes = []



# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_five_cs_bar_chart(score_result: ScoreResult):
    """Create Five Cs bar chart with color coding"""
    categories = ['CHARACTER', 'CAPACITY', 'CAPITAL', 'COLLATERAL', 'CONDITIONS']
    scores = [
        score_result.character_score,
        score_result.capacity_score,
        score_result.capital_score,
        score_result.collateral_score,
        score_result.conditions_score
    ]
    
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
            textfont=dict(size=14, color='#1f2937'),
            hovertemplate='<b>%{x}</b><br>Score: %{y:.1f}/100<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='Five Cs Score Distribution',
        xaxis_title='',
        yaxis_title='Score',
        yaxis_range=[0, 110],
        height=400,
        template='plotly_white',
        showlegend=False,
        margin=dict(t=60, b=40, l=40, r=40)
    )
    
    return fig


def create_radar_chart(score_result: ScoreResult):
    """Create radar chart for Five Cs visualization"""
    categories = ['CHARACTER', 'CAPACITY', 'CAPITAL', 'COLLATERAL', 'CONDITIONS']
    scores = [
        score_result.character_score,
        score_result.capacity_score,
        score_result.capital_score,
        score_result.collateral_score,
        score_result.conditions_score
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        fillcolor='rgba(102, 126, 234, 0.3)',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8, color='#667eea'),
        name='Credit Profile'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10),
                gridcolor='#e5e7eb'
            ),
            angularaxis=dict(
                tickfont=dict(size=12)
            )
        ),
        showlegend=False,
        height=400,
        margin=dict(t=40, b=40, l=60, r=60)
    )
    
    return fig



def create_risk_gauge(score: float):
    """Create risk gauge speedometer"""
    # Determine risk level
    if score >= 70:
        risk_level = "LOW RISK"
        color = "#10b981"
    elif score >= 50:
        risk_level = "MODERATE RISK"
        color = "#f59e0b"
    else:
        risk_level = "HIGH RISK"
        color = "#ef4444"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': risk_level, 'font': {'size': 20}},
        number={'suffix': "/100", 'font': {'size': 40}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#e5e7eb",
            'steps': [
                {'range': [0, 50], 'color': '#fee2e2'},
                {'range': [50, 70], 'color': '#fef3c7'},
                {'range': [70, 100], 'color': '#d1fae5'}
            ],
            'threshold': {
                'line': {'color': "#1f2937", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(t=40, b=20, l=20, r=20)
    )
    
    return fig


def render_metric_card(label: str, value: str, icon: str, border_color: str = "#667eea"):
    """Render metric card"""
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: {border_color};">
        <div class="metric-icon">{icon}</div>
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def render_decision_banner(verdict: str, score: float, interest_rate: str, flags_count: int):
    """Render decision banner"""
    config = {
        "APPROVE": {"class": "decision-approve", "emoji": "✅", "title": "APPROVED"},
        "REJECT": {"class": "decision-reject", "emoji": "❌", "title": "REJECTED"},
        "CONDITIONAL": {"class": "decision-conditional", "emoji": "⚠️", "title": "CONDITIONAL"}
    }
    
    c = config.get(verdict, config["REJECT"])
    
    st.markdown(f"""
    <div class="{c['class']}">
        <div class="decision-verdict">{c['emoji']} {c['title']}</div>
        <div class="decision-score">Credit Score: {score:.1f}/100</div>
        <div class="decision-meta">Interest Rate: {interest_rate} | Risk Flags: {flags_count}</div>
    </div>
    """, unsafe_allow_html=True)



# ============================================================================
# PAGE: APPLICATION INTAKE
# ============================================================================

def page_application_intake():
    """Application intake with professional layout - SAFEGUARD 1: Heavy pipeline only executes on button click"""
    
    # Hero header with chips
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">🏦 Intelli-Credit</div>
        <div class="hero-subtitle">AI-Powered Credit Risk Assessment using the Five Cs Framework</div>
        <div class="hero-chips">
            <span class="chip">🎯 Five Cs Framework</span>
            <span class="chip">🔍 Fraud Detection</span>
            <span class="chip">🤖 Document AI</span>
            <span class="chip">📊 Real-time Scoring</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">📂 Application Intake</div>', unsafe_allow_html=True)
    
    # Two-column layout
    col_left, col_right = st.columns([1.3, 1], gap="large")
    
    # LEFT: Document uploads
    with col_left:
        st.markdown("#### 📁 Financial Documents")
        
        uploaded_files = {}
        
        docs = [
            ("balance_sheet", "📊", "Balance Sheet"),
            ("profit_loss", "📈", "Profit & Loss Statement"),
            ("bank_statements", "🏦", "Bank Statements"),
            ("gst_returns", "📋", "GST Returns"),
            ("itr", "💼", "Income Tax Returns"),
            ("sanction_letter", "📄", "Sanction Letter")
        ]
        
        for doc_key, icon, label in docs:
            with st.container():
                st.markdown('<div class="upload-tile">', unsafe_allow_html=True)
                uploaded_file = st.file_uploader(
                    f"{icon} {label}",
                    type=['pdf'],
                    key=doc_key,
                    help=f"Upload {label} (PDF, max 8MB)",
                    label_visibility="visible"
                )
                if uploaded_file:
                    upload_path = Path("uploads") / uploaded_file.name
                    upload_path.parent.mkdir(exist_ok=True)
                    with open(upload_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    uploaded_files[doc_key] = str(upload_path)
                    st.success(f"✓ {uploaded_file.name}")
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.session_state.uploaded_file_paths = uploaded_files
    
    # RIGHT: Demo & company details
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
            "CIN",
            value=demo_info['cin'] if demo_info else "",
            placeholder="L12345MH2020PLC123456"
        )
        
        # FIX: Add CIN validation with visual feedback
        if cin_input and not demo_info:
            import re
            cin_pattern = r'^[LUF]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$'
            if re.match(cin_pattern, cin_input):
                st.success("✅ Valid CIN format")
            else:
                st.warning("⚠️ Invalid CIN format. Should be 21 characters: L12345MH2020PLC123456")
        
        company_name_input = st.text_input(
            "Company Name",
            value=demo_info['company_name'] if demo_info else "",
            placeholder="Enter legal company name"
        )
        
        # FIX: Add company name validation
        if company_name_input and not demo_info:
            if len(company_name_input) < 3:
                st.warning("⚠️ Company name seems too short")
            else:
                st.success("✅ Company name provided")
        
        promoter_name_input = st.text_input(
            "Promoter Name",
            placeholder="Primary promoter/director"
        )
        
        st.markdown("")
        
        # SAFEGUARD 5: Compliance UI block with CIBIL CMR rank
        st.markdown("#### 🔒 System Audit & Compliance")
        
        with st.container():
            st.markdown('<div class="card-container">', unsafe_allow_html=True)
            cibil_score = st.number_input(
                "CIBIL Commercial CMR Rank (1-10)",
                min_value=1,
                max_value=10,
                value=3,
                help="1 = Lowest risk (best), 10 = Highest risk (worst)"
            )
            
            if cibil_score > 6:
                st.warning("⚠️ High Risk CMR detected - Auto-routing to Senior Credit Committee")
            else:
                st.success("✓ CMR acceptable")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Process button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        process_button = st.button(
            "🚀 Process Application",
            type="primary"
        )
    
    if process_button:
        if not cin_input or not company_name_input:
            st.error("❌ Please provide CIN and Company Name")
            return
        
        is_demo = selected_demo != "None (Real Mode)"
        
        if not is_demo and not st.session_state.uploaded_file_paths:
            st.error("❌ Please upload documents or select demo")
            return
        
        try:
            # SAFEGUARD 2: Enhanced progress tracking with visual feedback
            with st.status("🔄 Processing Credit Application...", expanded=True) as status:
                progress_bar = st.progress(0)
                
                st.write("📤 Step 1/6: Validating documents...")
                progress_bar.progress(10)
                
                st.write("🤖 Step 2/6: AI extraction from PDFs...")
                progress_bar.progress(20)
                
                company_data = process_application(
                    cin=cin_input,
                    company_name=company_name_input,
                    promoter_name=promoter_name_input if promoter_name_input else None,
                    uploaded_files=st.session_state.uploaded_file_paths if not is_demo else None,
                    demo_mode=is_demo,
                    demo_company_key=selected_demo if is_demo else None,
                    cibil_cmr=int(cibil_score)
                )
                
                progress_bar.progress(50)
                st.write("🔍 Step 3/6: Fraud detection & GST analysis...")
                progress_bar.progress(65)
                
                st.write("🌐 Step 4/6: Company research & intelligence...")
                progress_bar.progress(75)
                
                st.write("📊 Step 5/6: Calculating Five Cs score...")
                progress_bar.progress(85)
                
                score_result = calculate_five_cs(company_data)
                
                from report_generator import generate_decision_narrative
                score_result.decision_narrative = generate_decision_narrative(
                    score_result.flags,
                    score_result.verdict.value
                )
                
                st.write("📄 Step 6/6: Generating CAM document...")
                progress_bar.progress(95)
                
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                output_path = output_dir / f"CAM_{cin_input}_{company_name_input.replace(' ', '_')}.docx"
                
                cam_path = generate_cam_word(company_data, score_result, str(output_path))
                
                progress_bar.progress(100)
                status.update(label="✅ Processing Complete!", state="complete", expanded=False)
            
            st.session_state.company_data = company_data
            st.session_state.score_result = score_result
            st.session_state.cam_document_path = cam_path
            st.session_state.processing_complete = True
            st.session_state.demo_mode = is_demo
            st.session_state.current_page = "Credit Analysis"
            
            # FIX: Cleanup uploaded files after processing (only in real mode)
            if not is_demo and st.session_state.uploaded_file_paths:
                import time
                time.sleep(1)  # Give time for processing to complete
                for file_path in st.session_state.uploaded_file_paths.values():
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            print(f"Cleaned up: {file_path}")
                    except Exception as e:
                        print(f"Cleanup warning: {e}")
            
            st.toast("✅ CAM report generated successfully!", icon="✅")
            st.rerun()
        
        except Exception as e:
            # SAFEGUARD 3: Enhanced error UI with actionable options
            st.error("❌ Processing Failed")
            
            with st.expander("🔍 Error Details", expanded=True):
                st.code(str(e), language="python")
                
                # Show helpful context
                st.markdown("**Possible causes:**")
                error_str = str(e).lower()
                if "api" in error_str or "key" in error_str:
                    st.markdown("- Missing or invalid API key (check .env file)")
                    st.markdown("- API rate limit exceeded")
                elif "pdf" in error_str or "file" in error_str:
                    st.markdown("- Corrupted or invalid PDF file")
                    st.markdown("- File size or page limit exceeded")
                elif "json" in error_str:
                    st.markdown("- LLM returned invalid JSON format")
                    st.markdown("- Data extraction failed")
                else:
                    st.markdown("- Unknown error - check logs for details")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Retry"):
                    st.rerun()
            with col2:
                if st.button("🏠 Start Over"):
                    reset_session_state()
                    st.rerun()
            with col3:
                if st.button("📋 Copy Error"):
                    st.toast("Error copied to clipboard", icon="📋")



# ============================================================================
# PAGE: CREDIT ANALYSIS
# ============================================================================

def page_credit_analysis():
    """Main credit analysis dashboard - SAFEGUARD 4: Session persistence, tabs don't re-trigger pipeline"""
    
    company_data = st.session_state.company_data
    score_result = st.session_state.score_result
    
    if not company_data or not score_result:
        st.error("No results available")
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
        score=score_result.final_score,
        interest_rate=score_result.interest_rate if score_result.interest_rate else "N/A",
        flags_count=len(score_result.flags)
    )
    
    st.markdown("")
    
    # KPI Metric cards
    st.markdown('<div class="section-header">📊 Key Performance Indicators</div>', unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4, gap="medium")
    
    with m1:
        render_metric_card("Credit Score", f"{score_result.final_score:.1f}", "🎯", "#667eea")
    
    with m2:
        render_metric_card("Interest Rate", score_result.interest_rate if score_result.interest_rate else "N/A", "💰", "#10b981")
    
    with m3:
        render_metric_card("Risk Flags", str(len(score_result.flags)), "🚩", "#ef4444")
    
    with m4:
        # FIX: Check for None explicitly, not falsy (0.0 is valid)
        loan_amt = f"₹{score_result.loan_amount:,.0f} Cr" if score_result.loan_amount is not None else "REJECTED"
        border = "#10b981" if score_result.loan_amount is not None else "#ef4444"
        render_metric_card("Approved Amount", loan_amt, "✅" if score_result.loan_amount is not None else "❌", border)
    
    st.markdown("")
    
    # Charts section
    st.markdown('<div class="section-header">📈 Credit Profile Visualization</div>', unsafe_allow_html=True)
    
    chart_col1, chart_col2 = st.columns(2, gap="large")
    
    with chart_col1:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; 
                    border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
            <div style="color: #1f2937; font-size: 0.85rem; font-weight: 700; 
                        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 1rem;">
                📊 Five Cs Score Distribution
            </div>
        """, unsafe_allow_html=True)
        fig_bar = create_five_cs_bar_chart(score_result)
        st.plotly_chart(fig_bar)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with chart_col2:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; 
                    border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
            <div style="color: #1f2937; font-size: 0.85rem; font-weight: 700; 
                        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 1rem;">
                🎯 Credit Risk Radar
            </div>
        """, unsafe_allow_html=True)
        fig_radar = create_radar_chart(score_result)
        st.plotly_chart(fig_radar)
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("")
    
    # Risk gauge
    st.markdown('<div class="section-header">⚡ Overall Risk Assessment</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: white; padding: 2rem; border-radius: 12px; 
                border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
    """, unsafe_allow_html=True)
    
    gauge_col1, gauge_col2, gauge_col3 = st.columns([1, 2, 1])
    with gauge_col2:
        fig_gauge = create_risk_gauge(score_result.final_score)
        st.plotly_chart(fig_gauge)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("")
    
    # Detailed tabs
    st.markdown('<div class="section-header">📑 Detailed Analysis</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Executive Summary", "📊 Five Cs Details", "👨‍💼 Officer Portal", "🔍 Additional Insights"])
    
    with tab1:
        if score_result.decision_narrative:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%); 
                        padding: 1.5rem; border-radius: 12px; border-left: 5px solid #667eea;
                        margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
                <div style="color: #667eea; font-size: 0.85rem; font-weight: 700; 
                            text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.8rem;">
                    📋 Decision Rationale
                </div>
                <div style="color: #1f2937; font-size: 1.05rem; line-height: 1.6;">
            """, unsafe_allow_html=True)
            st.markdown(score_result.decision_narrative)
            st.markdown("</div></div>", unsafe_allow_html=True)
        
        if score_result.reasoning:
            st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 12px; 
                        border: 1px solid #e5e7eb; margin-bottom: 1.5rem;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
                <div style="color: #1f2937; font-size: 0.85rem; font-weight: 700; 
                            text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.8rem;">
                    🔍 Detailed Analysis
                </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background: #f8fafc; padding: 1.2rem; border-radius: 8px;
                        border: 1px solid #e2e8f0; font-family: 'Courier New', monospace;
                        font-size: 0.85rem; line-height: 1.7; color: #334155;
                        max-height: 300px; overflow-y: auto; white-space: pre-wrap;">{score_result.reasoning}</div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; 
                    border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
            <div style="color: #1f2937; font-size: 0.85rem; font-weight: 700; 
                        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.8rem;">
                📊 Score Breakdown
            </div>
        """, unsafe_allow_html=True)
        summary_df = pd.DataFrame({
            "Category": ["CHARACTER", "CAPACITY", "CAPITAL", "COLLATERAL", "CONDITIONS", "TOTAL"],
            "Raw": [f"{score_result.character_score:.1f}", f"{score_result.capacity_score:.1f}", 
                    f"{score_result.capital_score:.1f}", f"{score_result.collateral_score:.1f}", 
                    f"{score_result.conditions_score:.1f}", "-"],
            "Weight": ["25%", "30%", "20%", "15%", "10%", "100%"],
            "Weighted": [f"{score_result.character_score * 0.25:.1f}", f"{score_result.capacity_score * 0.30:.1f}",
                        f"{score_result.capital_score * 0.20:.1f}", f"{score_result.collateral_score * 0.15:.1f}",
                        f"{score_result.conditions_score * 0.10:.1f}", f"{score_result.final_score:.1f}"]
        })
        st.dataframe(summary_df, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("""
        <div style="color: #6b7280; font-size: 0.95rem; margin-bottom: 1.5rem;">
            Detailed breakdown of each credit assessment category with associated risk flags and scoring rationale.
        </div>
        """, unsafe_allow_html=True)
        
        categories = [
            ("👤 CHARACTER", score_result.character_score, 0.25, "CHARACTER", "#667eea"),
            ("💼 CAPACITY", score_result.capacity_score, 0.30, "CAPACITY", "#10b981"),
            ("💰 CAPITAL", score_result.capital_score, 0.20, "CAPITAL", "#f59e0b"),
            ("🏠 COLLATERAL", score_result.collateral_score, 0.15, "COLLATERAL", "#8b5cf6"),
            ("🌍 CONDITIONS", score_result.conditions_score, 0.10, "CONDITIONS", "#06b6d4")
        ]
        
        for label, score, weight, cat_name, color in categories:
            # Determine score color
            if score >= 70:
                score_color = "#10b981"
                score_bg = "#d1fae5"
            elif score >= 50:
                score_color = "#f59e0b"
                score_bg = "#fef3c7"
            else:
                score_color = "#ef4444"
                score_bg = "#fee2e2"
            
            with st.expander(f"{label} ({int(weight*100)}% weight)", expanded=False):
                st.markdown(f"""
                <div style="background: {score_bg}; padding: 1rem; border-radius: 10px; 
                            border-left: 5px solid {score_color}; margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase; 
                                        letter-spacing: 1px; font-weight: 600;">Raw Score</div>
                            <div style="color: {score_color}; font-size: 2rem; font-weight: 800;">
                                {score:.1f}<span style="font-size: 1.2rem; opacity: 0.7;">/100</span>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase; 
                                        letter-spacing: 1px; font-weight: 600;">Weighted</div>
                            <div style="color: #1f2937; font-size: 1.5rem; font-weight: 700;">
                                {score * weight:.1f}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Include related flag categories (GST_FRAUD affects CAPACITY, EARLY_WARNING affects CHARACTER)
                related_categories = {
                    "CAPACITY": ["CAPACITY", "GST_FRAUD"],
                    "CHARACTER": ["CHARACTER", "EARLY_WARNING"],
                }
                match_cats = related_categories.get(cat_name, [cat_name])
                cat_flags = [f for f in score_result.flags if f.category.value in match_cats]
                if cat_flags:
                    st.markdown(f"""
                    <div style="color: #1f2937; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">
                        🚩 Risk Flags: {len(cat_flags)}
                    </div>
                    """, unsafe_allow_html=True)
                    for flag in cat_flags:
                        flag_color = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#3b82f6"}.get(flag.severity.value, "#6b7280")
                        st.markdown(f"""
                        <div style="background: #f9fafb; padding: 0.8rem; border-radius: 8px; 
                                    margin-bottom: 0.5rem; border-left: 3px solid {flag_color};">
                            <div style="color: #1f2937; font-size: 0.9rem;">{flag.description}</div>
                            <div style="color: #6b7280; font-size: 0.8rem; margin-top: 0.3rem;">
                                Impact: {flag.impact_score:+.1f} points
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: #d1fae5; padding: 1rem; border-radius: 8px; 
                                border-left: 3px solid #10b981; text-align: center;">
                        <span style="color: #10b981; font-size: 1.2rem;">✓</span>
                        <span style="color: #059669; font-weight: 600; margin-left: 0.5rem;">No flags detected</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show score computation trail if available
                if hasattr(score_result, 'score_trails') and score_result.score_trails and cat_name in score_result.score_trails:
                    trail = score_result.score_trails[cat_name]
                    st.markdown("""
                    <div style="margin-top: 1rem; color: #1f2937; font-size: 0.85rem; font-weight: 600;">
                        📐 Score Computation
                    </div>
                    """, unsafe_allow_html=True)
                    trail_html = ""
                    for line in trail:
                        if line.startswith("Base:"):
                            trail_html += f'<div style="color: #059669; font-weight: 600;">{line}</div>'
                        elif line.startswith("→"):
                            trail_html += f'<div style="color: #1f2937; font-weight: 700; border-top: 1px solid #e5e7eb; padding-top: 0.3rem; margin-top: 0.3rem;">{line}</div>'
                        elif line.startswith("-"):
                            trail_html += f'<div style="color: #ef4444;">{line}</div>'
                        elif line.startswith("+"):
                            trail_html += f'<div style="color: #10b981;">{line}</div>'
                        else:
                            trail_html += f'<div style="color: #6b7280;">{line}</div>'
                    st.markdown(f"""
                    <div style="background: #f9fafb; padding: 0.8rem; border-radius: 8px; 
                                font-family: 'Courier New', monospace; font-size: 0.85rem;
                                border: 1px solid #e5e7eb; margin-top: 0.5rem;">
                        {trail_html}
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab3:
        st.markdown("""
        <div style="color: #6b7280; font-size: 0.95rem; margin-bottom: 1.5rem;">
            Credit officers can add qualitative assessments to adjust scores based on management meetings, 
            site visits, and other subjective factors not captured in quantitative analysis.
        </div>
        """, unsafe_allow_html=True)
        
        # Officer Portal Integration
        if company_data:
            officer_notes = collect_officer_notes(company_data.company_name)
            
            if officer_notes:
                st.markdown("---")
                st.markdown("### 📊 Impact on Credit Scores")
                
                # Calculate base scores (without officer adjustments)
                base_scores = {
                    "CHARACTER": score_result.character_score,
                    "CAPACITY": score_result.capacity_score,
                    "CAPITAL": score_result.capital_score,
                    "COLLATERAL": score_result.collateral_score,
                    "CONDITIONS": score_result.conditions_score
                }
                
                # Apply officer adjustments
                adjusted_scores = apply_officer_adjustments(base_scores, officer_notes)
                
                # Show before/after comparison
                comparison_df = pd.DataFrame({
                    "Category": ["CHARACTER", "CAPACITY", "CAPITAL", "COLLATERAL", "CONDITIONS"],
                    "Base Score": [f"{base_scores[c]:.1f}" for c in ["CHARACTER", "CAPACITY", "CAPITAL", "COLLATERAL", "CONDITIONS"]],
                    "Officer Adj": [f"{adjusted_scores[c] - base_scores[c]:+.1f}" for c in ["CHARACTER", "CAPACITY", "CAPITAL", "COLLATERAL", "CONDITIONS"]],
                    "Final Score": [f"{adjusted_scores[c]:.1f}" for c in ["CHARACTER", "CAPACITY", "CAPITAL", "COLLATERAL", "CONDITIONS"]]
                })
                
                st.dataframe(comparison_df, hide_index=True)
                
                # Recalculate total with adjustments
                adjusted_total = (
                    adjusted_scores["CHARACTER"] * 0.25 +
                    adjusted_scores["CAPACITY"] * 0.30 +
                    adjusted_scores["CAPITAL"] * 0.20 +
                    adjusted_scores["COLLATERAL"] * 0.15 +
                    adjusted_scores["CONDITIONS"] * 0.10
                )
                
                total_change = adjusted_total - score_result.final_score
                
                if abs(total_change) > 0.1:
                    change_color = "#10b981" if total_change > 0 else "#ef4444"
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); 
                                padding: 1.2rem; border-radius: 12px; border-left: 5px solid {change_color};
                                margin-top: 1rem;">
                        <div style="color: {change_color}; font-size: 1.1rem; font-weight: 700;">
                            📊 Adjusted Total Score: {adjusted_total:.1f}/100 ({total_change:+.1f})
                        </div>
                        <div style="color: #6b7280; font-size: 0.9rem; margin-top: 0.3rem;">
                            Officer adjustments {'increased' if total_change > 0 else 'decreased'} the credit score
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Persist officer notes and adjusted scores to session state
                st.session_state.company_data.officer_notes = officer_notes
                st.session_state.score_result.character_score = adjusted_scores["CHARACTER"]
                st.session_state.score_result.capacity_score = adjusted_scores["CAPACITY"]
                st.session_state.score_result.capital_score = adjusted_scores["CAPITAL"]
                st.session_state.score_result.collateral_score = adjusted_scores["COLLATERAL"]
                st.session_state.score_result.conditions_score = adjusted_scores["CONDITIONS"]
                st.session_state.score_result.final_score = round(adjusted_total, 1)
        else:
            st.warning("Company data not available for officer assessment")
    
    with tab4:
        if company_data.officer_notes:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                        padding: 1.2rem; border-radius: 12px; border-left: 5px solid #f59e0b;
                        margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(245,158,11,0.15);">
                <div style="color: #92400e; font-size: 0.85rem; font-weight: 700; 
                            text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.8rem;">
                    📝 Officer Notes & Adjustments
                </div>
            """, unsafe_allow_html=True)
            for i, note in enumerate(company_data.officer_notes, 1):
                adj_color = "#10b981" if note.adjustment > 0 else "#ef4444"
                st.markdown(f"""
                <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.8rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="color: #1f2937; font-weight: 700; font-size: 1rem;">
                            {i}. {note.affected_c.value}
                        </span>
                        <span style="color: {adj_color}; font-weight: 800; font-size: 1.2rem;">
                            {note.adjustment:+.1f}
                        </span>
                    </div>
                    <div style="color: #6b7280; font-size: 0.9rem; line-height: 1.5;">
                        {note.note_text}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        if company_data.research:
            # FIX: Use f-string properly to render variables
            sector_value = company_data.research.sector or 'N/A'
            outlook_value = company_data.research.sector_outlook or 'N/A'
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); 
                        padding: 1.2rem; border-radius: 12px; border-left: 5px solid #3b82f6;
                        box-shadow: 0 2px 8px rgba(59,130,246,0.15);">
                <div style="color: #1e40af; font-size: 0.85rem; font-weight: 700; 
                            text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.8rem;">
                    🏭 Sector Intelligence
                </div>
                <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
                    <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase; 
                                letter-spacing: 1px; font-weight: 600;">Sector</div>
                    <div style="color: #1f2937; font-size: 1.1rem; font-weight: 700; margin-top: 0.3rem;">
                        {sector_value}
                    </div>
                </div>
                <div style="background: white; padding: 1rem; border-radius: 8px;">
                    <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase; 
                                letter-spacing: 1px; font-weight: 600;">Outlook</div>
                    <div style="color: #1f2937; font-size: 1.1rem; font-weight: 700; margin-top: 0.3rem;">
                        {outlook_value}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)



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
    
    st.markdown('<div class="section-header">🚨 Risk Flags & Warnings</div>', unsafe_allow_html=True)
    
    if not score_result.flags:
        st.success("✅ No risk flags detected - Clean credit profile")
        return
    
    # Summary
    high = len([f for f in score_result.flags if f.severity.value == "HIGH"])
    medium = len([f for f in score_result.flags if f.severity.value == "MEDIUM"])
    low = len([f for f in score_result.flags if f.severity.value == "LOW"])
    
    st.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 12px; 
                border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                margin-bottom: 2rem;">
    """, unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase; 
                        letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">Total Flags</div>
            <div style="color: #1f2937; font-size: 2.5rem; font-weight: 800;">
                {len(score_result.flags)}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase; 
                        letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">🔴 High</div>
            <div style="color: #ef4444; font-size: 2.5rem; font-weight: 800;">
                {high}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase; 
                        letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">🟡 Medium</div>
            <div style="color: #f59e0b; font-size: 2.5rem; font-weight: 800;">
                {medium}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase; 
                        letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">🔵 Low</div>
            <div style="color: #3b82f6; font-size: 2.5rem; font-weight: 800;">
                {low}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("")
    
    # Display flags
    high_flags = [f for f in score_result.flags if f.severity.value == "HIGH"]
    medium_flags = [f for f in score_result.flags if f.severity.value == "MEDIUM"]
    low_flags = [f for f in score_result.flags if f.severity.value == "LOW"]
    green_flags = [f for f in score_result.flags if f.severity.value == "GREEN"]
    
    if high_flags:
        st.markdown("### 🔴 HIGH Severity")
        for flag in high_flags:
            st.markdown(f"""
            <div class="flag-card-high">
                <strong style="font-size: 1.1rem;">{flag.category.value}</strong><br>
                <span style="font-size: 1rem;">{flag.description}</span><br>
                <small style="opacity: 0.8;">Source: {flag.source} | Impact: {flag.impact_score:.1f}</small>
            </div>
            """, unsafe_allow_html=True)
    
    if medium_flags:
        st.markdown("### 🟡 MEDIUM Severity")
        for flag in medium_flags:
            st.markdown(f"""
            <div class="flag-card-medium">
                <strong style="font-size: 1.1rem;">{flag.category.value}</strong><br>
                <span style="font-size: 1rem;">{flag.description}</span><br>
                <small style="opacity: 0.8;">Source: {flag.source} | Impact: {flag.impact_score:.1f}</small>
            </div>
            """, unsafe_allow_html=True)
    
    if low_flags:
        st.markdown("### 🔵 LOW Severity")
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
    
    st.markdown('<div class="section-header">📰 Research & Intelligence</div>', unsafe_allow_html=True)
    
    # Sector
    st.markdown("### 🏭 Sector Analysis")
    
    st.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 12px; 
                border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                margin-bottom: 1.5rem;">
    """, unsafe_allow_html=True)
    
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase; 
                        letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">Sector</div>
            <div style="color: #1f2937; font-size: 1.3rem; font-weight: 700;">
                {research.sector or "N/A"}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with s2:
        outlook_emoji = {"GROWING": "📈", "STABLE": "➡️", "DECLINING": "📉", "DISTRESSED": "🚨"}.get(research.sector_outlook, "➡️")
        outlook_color = {"POSITIVE": "#10b981", "NEUTRAL": "#f59e0b", "DISTRESSED": "#ef4444"}.get(research.sector_outlook, "#6b7280")
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase; 
                        letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">Outlook</div>
            <div style="color: {outlook_color}; font-size: 1.3rem; font-weight: 700;">
                {outlook_emoji} {research.sector_outlook or "N/A"}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with s3:
        npa_color = "#ef4444" if (research.sector_npa_rate and research.sector_npa_rate > 10) else "#10b981"
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase; 
                        letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">Sector NPA</div>
            <div style="color: {npa_color}; font-size: 1.3rem; font-weight: 700;">
                {f"{research.sector_npa_rate:.1f}%" if research.sector_npa_rate else "N/A"}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("")
    
    # MCA
    st.markdown("### 📋 MCA Status")
    mca = research.mca_status or "N/A"
    mca_color = "#10b981" if "Active" in mca else "#f59e0b"
    mca_bg = "#d1fae5" if "Active" in mca else "#fef3c7"
    mca_icon = "✅" if "Active" in mca else "⚠️"
    
    st.markdown(f"""
    <div style="background: {mca_bg}; padding: 1.5rem; border-radius: 12px; 
                border-left: 5px solid {mca_color}; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <span style="font-size: 2rem;">{mca_icon}</span>
            <div>
                <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase; 
                            letter-spacing: 1px; font-weight: 600;">MCA Registration Status</div>
                <div style="color: {mca_color}; font-size: 1.3rem; font-weight: 700; margin-top: 0.3rem;">
                    {mca}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if hasattr(research, 'mca_data') and research.mca_data:
        d = research.mca_data
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; 
                    border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                    margin-bottom: 1.5rem;">
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                <div>
                    <div style="color: #6b7280; font-size: 0.7rem; text-transform: uppercase; font-weight: 600;">Authorized Capital</div>
                    <div style="color: #1f2937; font-weight: 600;">₹{d.get('authorized_capital', 0):.2f} Cr</div>
                </div>
                <div>
                    <div style="color: #6b7280; font-size: 0.7rem; text-transform: uppercase; font-weight: 600;">Paid-up Capital</div>
                    <div style="color: #1f2937; font-weight: 600;">₹{d.get('paidup_capital', 0):.2f} Cr</div>
                </div>
                <div>
                    <div style="color: #6b7280; font-size: 0.7rem; text-transform: uppercase; font-weight: 600;">Registration Date</div>
                    <div style="color: #1f2937; font-weight: 600;">{d.get('date_of_registration', 'N/A')}</div>
                </div>
                <div>
                    <div style="color: #6b7280; font-size: 0.7rem; text-transform: uppercase; font-weight: 600;">Company Class</div>
                    <div style="color: #1f2937; font-weight: 600;">{d.get('company_class', 'N/A')}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Stock
    if research.stock_data and research.stock_data.is_listed:
        st.markdown("### 📈 Stock Market Data")
        
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; 
                    border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                    margin-bottom: 1.5rem;">
        """, unsafe_allow_html=True)
        
        st1, st2, st3, st4 = st.columns(4)
        with st1:
            st.markdown(f"""
            <div style="text-align: center; padding: 0.8rem;">
                <div style="color: #6b7280; font-size: 0.7rem; text-transform: uppercase; 
                            letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">Ticker</div>
                <div style="color: #667eea; font-size: 1.2rem; font-weight: 800;">
                    {research.stock_data.ticker or "N/A"}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with st2:
            st.markdown(f"""
            <div style="text-align: center; padding: 0.8rem;">
                <div style="color: #6b7280; font-size: 0.7rem; text-transform: uppercase; 
                            letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">Price</div>
                <div style="color: #1f2937; font-size: 1.2rem; font-weight: 800;">
                    {"₹{:,.2f}".format(research.stock_data.current_price) if research.stock_data.current_price else "N/A"}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with st3:
            st.markdown(f"""
            <div style="text-align: center; padding: 0.8rem;">
                <div style="color: #6b7280; font-size: 0.7rem; text-transform: uppercase; 
                            letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">Market Cap</div>
                <div style="color: #1f2937; font-size: 1.2rem; font-weight: 800;">
                    {"₹{:,.0f}Cr".format(research.stock_data.market_cap) if research.stock_data.market_cap else "N/A"}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with st4:
            st.markdown(f"""
            <div style="text-align: center; padding: 0.8rem;">
                <div style="color: #6b7280; font-size: 0.7rem; text-transform: uppercase; 
                            letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">52W High</div>
                <div style="color: #10b981; font-size: 1.2rem; font-weight: 800;">
                    {"₹{:,.2f}".format(research.stock_data.fifty_two_week_high) if getattr(research.stock_data, 'fifty_two_week_high', None) else "N/A"}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # News
    if hasattr(research, 'news_items') and research.news_items:
        st.markdown("### 📰 Recent News")
        
        # Display AI News Synthesis if available
        if hasattr(research, 'news_summary') and research.news_summary:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); 
                        padding: 1.5rem; border-radius: 12px; border-left: 4px solid #0ea5e9;
                        border-right: 1px solid #e0f2fe; border-top: 1px solid #e0f2fe; border-bottom: 1px solid #e0f2fe;
                        margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                <div style="display: flex; align-items: center; gap: 0.7rem; margin-bottom: 0.8rem;">
                    <span style="font-size: 1.5rem;">🧠</span>
                    <span style="color: #0369a1; font-weight: 700; font-size: 1.1rem; letter-spacing: 0.5px;">
                        AI Credit Risk Synthesis
                    </span>
                </div>
                <div style="color: #0f172a; font-size: 0.95rem; line-height: 1.6;">
                    {research.news_summary}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Just use the items directly since researcher.py handles relevance filtering now
        filtered_news = research.news_items
        
        if not filtered_news:
            st.info("No relevant credit-related news found for this company.")
        else:
            for i, news in enumerate(filtered_news, 1):
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 12px; 
                            border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                            margin-bottom: 1rem; transition: all 0.3s ease;">
                    <div style="display: flex; align-items: start; gap: 1rem;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                    color: white; font-size: 1.2rem; font-weight: 800; 
                                    width: 40px; height: 40px; border-radius: 10px; 
                                    display: flex; align-items: center; justify-content: center;
                                    flex-shrink: 0;">
                            {i}
                        </div>
                        <div style="flex: 1;">
                            <h4 style="margin: 0 0 0.8rem 0; color: #1f2937; font-size: 1.1rem; line-height: 1.4;">
                                {news.title}
                            </h4>
                            <div style="display: flex; gap: 1.5rem; margin-bottom: 0.8rem; font-size: 0.85rem; color: #6b7280;">
                                <span><strong>Source:</strong> {news.source}</span>
                                <span><strong>Date:</strong> {news.date}</span>
                            </div>
                            <p style="margin: 0.8rem 0; color: #4b5563; line-height: 1.6; font-size: 0.95rem;">
                                {news.snippet if news.snippet else ''}
                            </p>
                            <a href="{news.url}" target="_blank" 
                               style="color: #667eea; font-weight: 600; text-decoration: none; 
                                      font-size: 0.9rem; display: inline-flex; align-items: center; gap: 0.3rem;">
                                Read full article →
                            </a>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No news data available for this company.")



# ============================================================================
# PAGE: CAM REPORT
# ============================================================================

def page_cam_report():
    """CAM report download page"""
    
    st.markdown('<div class="section-header">📄 CAM Report</div>', unsafe_allow_html=True)
    
    if st.session_state.cam_document_path and Path(st.session_state.cam_document_path).exists():
        
        # Success banner
        st.markdown("""
        <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
                    padding: 1.5rem; border-radius: 12px; border-left: 5px solid #10b981;
                    margin-bottom: 2rem; box-shadow: 0 4px 12px rgba(16,185,129,0.2);">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <span style="font-size: 2.5rem;">✅</span>
                <div>
                    <div style="color: #065f46; font-size: 1.3rem; font-weight: 800;">
                        CAM Document Generated Successfully
                    </div>
                    <div style="color: #047857; font-size: 0.95rem; margin-top: 0.3rem;">
                        Professional credit assessment memorandum ready for download
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Download section with premium styling
        st.markdown("""
        <div style="background: white; padding: 2rem; border-radius: 12px; 
                    border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                    margin-bottom: 2rem;">
            <div style="color: #1f2937; font-size: 1.2rem; font-weight: 700; margin-bottom: 1.5rem;">
                📥 Download Options
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with open(st.session_state.cam_document_path, 'rb') as f:
                st.download_button(
                    label="📥 Download CAM Document (.docx)",
                    data=f.read(),
                    file_name=Path(st.session_state.cam_document_path).name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        
        with col2:
            if st.button("🔄 New Application"):
                st.session_state.company_data = None
                st.session_state.score_result = None
                st.session_state.processing_complete = False
                st.session_state.cam_document_path = None
                st.session_state.uploaded_file_paths = {}
                st.session_state.current_page = "Application Intake"
                st.toast("Ready for new application", icon="🔄")
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Document contents with premium card
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); 
                    padding: 1.5rem; border-radius: 12px; border-left: 5px solid #667eea;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
            <div style="color: #667eea; font-size: 0.85rem; font-weight: 700; 
                        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 1rem;">
                📋 Document Contents
            </div>
            <div style="color: #1f2937; font-size: 0.95rem; line-height: 2;">
                ✓ Executive Summary with credit decision<br>
                ✓ Company Overview (CIN, Sector, MCA Status)<br>
                ✓ Financial Analysis (Revenue, Ratios, Banking)<br>
                ✓ Five Cs Breakdown with all flags<br>
                ✓ GST Analysis<br>
                ✓ Research Findings<br>
                ✓ Officer Notes<br>
                ✓ Final Recommendation
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("CAM document not available")



# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application with navigation"""
    
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
        st.caption("Credit Risk Console")
        st.markdown("---")
        
        # Navigation menu
        if st.session_state.processing_complete:
            menu_options = ["Application Intake", "Credit Analysis", "Risk Flags", "Research Insights", "CAM Report"]
            menu_icons = ["📂", "📊", "🚨", "📰", "📄"]
        else:
            menu_options = ["Application Intake"]
            menu_icons = ["📂"]
        
        selected = option_menu(
            menu_title=None,
            options=menu_options,
            icons=menu_icons,
            default_index=menu_options.index(st.session_state.current_page) if st.session_state.current_page in menu_options else 0,
            styles={
                "container": {"padding": "0"},
                "nav-link": {"font-size": "0.95rem", "text-align": "left", "margin": "0.2rem", "border-radius": "8px"},
                "nav-link-selected": {"background-color": "#667eea"}
            }
        )
        
        # Fix: Only update and rerun if selection changed
        if selected != st.session_state.current_page:
            st.session_state.current_page = selected
            st.rerun()
        
        st.markdown("---")
        
        # Five Cs info with premium card styling
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.2rem; border-radius: 12px; margin-bottom: 1rem;
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);">
            <div style="color: white; font-size: 1rem; font-weight: 700; margin-bottom: 0.8rem;">
                🎯 Five Cs Framework
            </div>
            <div style="color: rgba(255,255,255,0.95); font-size: 0.85rem; line-height: 2;">
                <div style="display: flex; justify-content: space-between; padding: 0.3rem 0;">
                    <span>👤 CHARACTER</span><span style="font-weight: 600;">25%</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 0.3rem 0;">
                    <span>💼 CAPACITY</span><span style="font-weight: 600;">30%</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 0.3rem 0;">
                    <span>💰 CAPITAL</span><span style="font-weight: 600;">20%</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 0.3rem 0;">
                    <span>🏠 COLLATERAL</span><span style="font-weight: 600;">15%</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 0.3rem 0;">
                    <span>🌍 CONDITIONS</span><span style="font-weight: 600;">10%</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # System status with premium card styling
        groq = os.getenv("GROQ_API_KEY")
        serper = os.getenv("SERPER_API_KEY")
        news = os.getenv("NEWSAPI_KEY")
        
        st.markdown(f"""
        <div style="background: white; padding: 1.2rem; border-radius: 12px; 
                    border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
            <div style="color: #1f2937; font-size: 1rem; font-weight: 700; margin-bottom: 0.8rem;">
                🔌 System Status
            </div>
            <div style="font-size: 0.9rem; line-height: 2.2;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.2rem;">{'🟢' if groq else '🔴'}</span>
                    <span style="color: {'#10b981' if groq else '#ef4444'}; font-weight: 600;">Groq AI</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.2rem;">{'🟢' if serper else '🟡'}</span>
                    <span style="color: {'#10b981' if serper else '#f59e0b'}; font-weight: 600;">Serper API</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.2rem;">{'🟢' if news else '🟡'}</span>
                    <span style="color: {'#10b981' if news else '#f59e0b'}; font-weight: 600;">News API</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Quick stats if processing complete
        if st.session_state.processing_complete and st.session_state.score_result:
            score = st.session_state.score_result.final_score
            verdict = st.session_state.score_result.verdict.value
            
            verdict_color = {"APPROVE": "#10b981", "REJECT": "#ef4444", "CONDITIONAL": "#f59e0b"}.get(verdict, "#6b7280")
            verdict_emoji = {"APPROVE": "✅", "REJECT": "❌", "CONDITIONAL": "⚠️"}.get(verdict, "")
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {verdict_color} 0%, {verdict_color}dd 100%); 
                        padding: 1rem; border-radius: 12px; text-align: center;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                <div style="color: white; font-size: 1.8rem; font-weight: 800; margin-bottom: 0.3rem;">
                    {verdict_emoji} {verdict}
                </div>
                <div style="color: rgba(255,255,255,0.95); font-size: 1.3rem; font-weight: 600;">
                    {score:.1f}/100
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # FIX: Add reset button below verdict card
            st.markdown("")
            if st.button("🔄 New Application", help="Clear all data and start fresh"):
                reset_session_state()
                st.rerun()
    
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


# ============================================================================
# BACKWARD COMPATIBILITY ALIASES FOR TESTS
# ============================================================================

# Aliases for test compatibility
page_upload = page_application_intake
page_results = page_credit_analysis
