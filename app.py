"""
app.py — Strategy Agent: AI-Powered Annual Report Analyzer

Built for Prof. Koçak's Strategic Management course (Emory Goizueta EvMBA28)
"""

import json
import os
import tempfile
import streamlit as st
from src.pdf_parser import extract_text, chunk_text
from src.strategy_engine import analyze_report
from src.pdf_export import generate_pdf
from src.visualizer import (
    generate_strategy_map_html,
    generate_swot_html,
    generate_strategy_statement_html,
    generate_financial_health_html,
)

st.set_page_config(
    page_title="Strategy Agent — Goizueta EvMBA28",
    page_icon="🎯",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Team access gate — protects your API key from public use
# Set TEAM_PASSWORD in .env or Streamlit Cloud secrets
# ---------------------------------------------------------------------------
TEAM_PASSWORD = os.getenv("TEAM_PASSWORD", "")

if TEAM_PASSWORD:
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.markdown("""
        <div style="text-align:center; padding:4rem 1rem;">
            <h1 style="color:#CFB53B; font-family:Georgia,serif;">🎯 Strategy Agent</h1>
            <p style="color:#8facc4;">Emory Goizueta EvMBA28 · Team Access Only</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            pwd = st.text_input("Team Password", type="password", placeholder="Enter team password")
            if st.button("Enter", use_container_width=True):
                if pwd == TEAM_PASSWORD:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
        st.stop()

# ---------------------------------------------------------------------------
# Emory Goizueta branding — heavy gold
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Source+Sans+3:wght@300;400;500;600&display=swap');

    /* ---------- Global ---------- */
    .stApp {
        background: linear-gradient(175deg, #0a1628 0%, #0d1f3c 50%, #0f2440 100%);
    }

    /* ---------- Header ---------- */
    .emory-header {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem 1rem;
        position: relative;
    }
    .emory-header::after {
        content: '';
        display: block;
        width: 200px;
        height: 2px;
        background: linear-gradient(90deg, transparent, #CFB53B, #E8D48B, #CFB53B, transparent);
        margin: 1.2rem auto 0 auto;
    }
    .emory-header h1 {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 2.8rem;
        font-weight: 800;
        color: #CFB53B;
        letter-spacing: 0.03em;
        margin: 0;
        text-shadow: 0 2px 12px rgba(207,181,59,0.25);
    }
    .emory-header .subtitle {
        font-family: 'Source Sans 3', sans-serif;
        font-size: 1.05rem;
        color: #E8D48B;
        margin-top: 0.6rem;
        font-weight: 300;
        letter-spacing: 0.04em;
    }
    .emory-header .course-tag {
        display: inline-block;
        margin-top: 0.8rem;
        font-family: 'Source Sans 3', sans-serif;
        font-size: 0.72rem;
        color: #CFB53B;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        border: 1px solid rgba(207,181,59,0.45);
        padding: 5px 18px;
        border-radius: 20px;
        background: rgba(207,181,59,0.1);
    }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1f3c 0%, #0a1628 100%);
        border-right: 1px solid rgba(207,181,59,0.2);
    }
    section[data-testid="stSidebar"] .stMarkdown h3 {
        font-family: 'Playfair Display', Georgia, serif;
        color: #CFB53B !important;
        font-size: 1.1rem;
        letter-spacing: 0.02em;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        font-family: 'Source Sans 3', sans-serif;
        color: #C9B97A !important;
        font-size: 0.88rem;
    }
    section[data-testid="stSidebar"] .stMarkdown strong {
        color: #E8D48B !important;
    }
    section[data-testid="stSidebar"] .stSelectbox label {
        color: #CFB53B !important;
        font-family: 'Source Sans 3', sans-serif;
        font-weight: 500;
    }

    /* ---------- Main content text ---------- */
    .stApp .stMarkdown p, .stApp .stMarkdown li {
        font-family: 'Source Sans 3', sans-serif;
        color: #E8D48B;
    }
    .stApp .stMarkdown strong {
        color: #CFB53B;
    }

    /* ---------- File uploader ---------- */
    .stFileUploader {
        border: none !important;
        background: transparent !important;
    }
    .stFileUploader label {
        color: #CFB53B !important;
        font-family: 'Source Sans 3', sans-serif;
        font-weight: 500;
    }
    .stFileUploader section {
        border: 2px dashed rgba(207,181,59,0.4) !important;
        border-radius: 12px !important;
        background: rgba(207,181,59,0.04) !important;
        padding: 1.5rem !important;
        transition: all 0.2s ease;
    }
    .stFileUploader section:hover {
        border-color: rgba(207,181,59,0.7) !important;
        background: rgba(207,181,59,0.08) !important;
    }
    .stFileUploader section > div {
        background: transparent !important;
        border: none !important;
    }
    .stFileUploader p, .stFileUploader span, .stFileUploader small {
        color: #C9B97A !important;
    }
    .stFileUploader button {
        color: #CFB53B !important;
        border-color: rgba(207,181,59,0.4) !important;
        background: rgba(207,181,59,0.08) !important;
        font-family: 'Source Sans 3', sans-serif;
    }
    .stFileUploader button:hover {
        background: rgba(207,181,59,0.15) !important;
        border-color: rgba(207,181,59,0.6) !important;
    }

    /* ---------- Tabs ---------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.4rem;
        background: rgba(207,181,59,0.06);
        border-radius: 10px;
        padding: 4px;
        border: 1px solid rgba(207,181,59,0.12);
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Source Sans 3', sans-serif;
        font-size: 0.9rem;
        font-weight: 500;
        color: #C9B97A;
        border-radius: 8px;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(207,181,59,0.2), rgba(232,212,139,0.15)) !important;
        color: #CFB53B !important;
        font-weight: 600;
        border: 1px solid rgba(207,181,59,0.3);
    }

    /* ---------- Status expander ---------- */
    .stStatus {
        background: rgba(207,181,59,0.04) !important;
        border: 1px solid rgba(207,181,59,0.18) !important;
        border-radius: 10px;
    }
    .stStatus p { color: #E8D48B !important; }

    /* ---------- Download buttons ---------- */
    .stDownloadButton > button {
        font-family: 'Source Sans 3', sans-serif;
        background: linear-gradient(135deg, #CFB53B, #b8972e) !important;
        color: #0a1628 !important;
        font-weight: 600;
        border: none !important;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        letter-spacing: 0.03em;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(207,181,59,0.2);
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #E8D48B, #CFB53B) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(207,181,59,0.35);
    }

    /* ---------- Divider ---------- */
    hr { border-color: rgba(207,181,59,0.18) !important; }

    /* ---------- JSON viewer ---------- */
    .stJson {
        background: rgba(207,181,59,0.04) !important;
        border-radius: 8px;
        border: 1px solid rgba(207,181,59,0.1);
    }

    /* ---------- Warning/Error ---------- */
    .stAlert { border-radius: 8px; }

    /* ---------- Goizueta footer ---------- */
    .goizueta-footer {
        text-align: center;
        padding: 1.5rem 0;
        margin-top: 2rem;
        border-top: 1px solid rgba(207,181,59,0.18);
    }
    .goizueta-footer span {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 0.85rem;
        color: rgba(207,181,59,0.5);
        letter-spacing: 0.1em;
    }

    /* ---------- Selectbox ---------- */
    .stSelectbox > div > div {
        background: rgba(207,181,59,0.06) !important;
        border: 1px solid rgba(207,181,59,0.2) !important;
        color: #CFB53B !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="emory-header">
    <h1>🎯 Strategy Agent</h1>
    <div class="subtitle">
        Upload a 10-K annual report → Strategy Map · SWOT · Financial Health
    </div>
    <div class="course-tag">
        Powered by Claude AI · Koçak Strategic Management · Emory Goizueta
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")

    model_choice = st.selectbox(
        "Model",
        options=["Sonnet (Better Quality ~$0.50)", "Haiku (Faster & Cheaper ~$0.10)"],
        index=1,
    )

    if "Sonnet" in model_choice:
        selected_model = "claude-sonnet-4-6"
    else:
        selected_model = "claude-haiku-4-5-20251001"

    st.divider()

    st.markdown("### How It Works")
    st.markdown("""
    1. **Upload** a 10-K or annual report PDF
    2. **Extract** text from all pages
    3. **Analyze** with Claude using the Koçak strategy framework
    4. **Visualize** as Strategy Map + SWOT + Financial Health

    Uses **only** information from the uploaded report — no outside data.
    """)

    st.divider()
    st.markdown("""
    <div style="font-size:0.75rem; color:rgba(207,181,59,0.5); text-align:center;
                font-family:'Source Sans 3',sans-serif;">
    ISOM 640 · Strategic Management<br>
    Prof. Koçak · Emory Goizueta<br>
    EvMBA28 · Summer 2026
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload Annual Report (PDF)",
    type=["pdf"],
    help="10-K filings, annual reports — most work well. 50-200 pages typical.",
)

if uploaded_file and not api_key:
    st.warning("Please set your ANTHROPIC_API_KEY in the .env file.")

if uploaded_file and api_key:
    file_key = f"{uploaded_file.name}_{uploaded_file.size}"

    if st.session_state.get("result_key") != file_key:
        with st.status("📄 Extracting text from PDF...", expanded=True) as status:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            try:
                full_text = extract_text(tmp_path)
                chunks = chunk_text(full_text)
                st.write(f"✅ Extracted **{len(full_text):,}** characters")
                st.write(f"📦 Split into **{len(chunks)}** chunk(s) for analysis")
                status.update(label="✅ Text extracted!", state="complete")
            except Exception as e:
                st.error(f"Error extracting PDF: {e}")
                st.stop()
            finally:
                os.unlink(tmp_path)

        with st.status("🧠 Analyzing with Claude (this may take 2-5 minutes for large reports)...", expanded=True) as status:
            try:
                result = analyze_report(full_text, chunks, model=selected_model)
                company = result.get("company_name", "Unknown")
                fy = result.get("fiscal_year", "")
                st.write(f"✅ Analysis complete for **{company}** ({fy})")
                status.update(label=f"✅ Analysis complete — {company}", state="complete")

                st.session_state["result"] = result
                st.session_state["result_key"] = file_key

            except Exception as e:
                st.error(f"Error during analysis: {e}")
                st.stop()

# ---------------------------------------------------------------------------
# Display results (from cache if available)
# ---------------------------------------------------------------------------
if "result" in st.session_state:
    result = st.session_state["result"]
    company = result.get("company_name", "Unknown")
    fy = result.get("fiscal_year", "")

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️ Strategy Map",
        "📊 SWOT Analysis",
        "💰 Financial Health",
        "📝 Strategy Statement",
        "🔍 Raw JSON"
    ])

    with tab1:
        st.components.v1.html(
            generate_strategy_map_html(result),
            height=900,
            scrolling=True,
        )

    with tab2:
        st.components.v1.html(
            generate_swot_html(result),
            height=1200,
            scrolling=True,
        )

    with tab3:
        st.components.v1.html(
            generate_financial_health_html(result),
            height=900,
            scrolling=True,
        )

    with tab4:
        st.components.v1.html(
            generate_strategy_statement_html(result),
            height=150,
        )

    with tab5:
        st.json(result)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        pdf_filename = f"strategy_report_{company.replace(' ', '_')}.pdf"
        pdf_path = os.path.join(tempfile.gettempdir(), pdf_filename)
        generate_pdf(result, pdf_path)

        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_file.read(),
                file_name=pdf_filename,
                mime="application/pdf",
            )

    with col2:
        st.download_button(
            label="📥 Download Raw JSON",
            data=json.dumps(result, indent=2),
            file_name=f"strategy_analysis_{company.replace(' ', '_')}.json",
            mime="application/json",
        )

    st.markdown("""
    <div class="goizueta-footer">
        <span>GOIZUETA BUSINESS SCHOOL · EMORY UNIVERSITY</span>
    </div>
    """, unsafe_allow_html=True)