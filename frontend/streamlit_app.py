# ============================================================================
# frontend/streamlit_app.py
# ============================================================================
# ============================================================================
# frontend/streamlit_app.py
# ============================================================================

import os
import sys
import streamlit as st

# Ensure the "frontend" directory (this file's dir) is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# 👇 FIRST Streamlit command – MUST be before any other st.* usage
st.set_page_config(
    page_title="Finance Chatbot",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 👇 All other imports that use Streamlit come *after* set_page_config
from components.sidebar import render_sidebar
from components.chat import chat_interface
from components.upload import upload_interface
from components.file_analysis import file_analysis_interface, show_ai_status
from utils.api_client import get_document_count, check_backend
import requests


# ============================================================================
# SECTION 3: Custom CSS
# ============================================================================

st.markdown(
    """
<style>
    /* ROOT VARIABLES */
    :root {
        --light-bg: #ffffff;
        --light-text: #0d1117;
        --light-accent: #2563eb;
        
        --dark-bg: #0d1117;
        --dark-text: #e6edf3;
        --dark-accent: #58a6ff;
    }
    
    /* MAIN CONTAINER */
    .main {
        padding: 2rem 3rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    @media (prefers-color-scheme: dark) {
        .main {
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        }
    }
    
    /* HEADER STYLING */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    
    @media (prefers-color-scheme: dark) {
        .header-container {
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        color: white;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .header-subtitle {
        font-size: 1.1rem;
        margin-top: 0.5rem;
        color: rgba(255, 255, 255, 0.9);
        font-weight: 300;
        letter-spacing: 0.5px;
    }
    
    /* API STATUS HEADER */
    .api-status-header {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border: 2px solid #e0e7ff;
    }
    
    @media (prefers-color-scheme: dark) {
        .api-status-header {
            background: #161b22;
            border: 2px solid #30363d;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
    }
    
    .api-status-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin: 0 0 1rem 0;
        color: #0d1117;
    }
    
    @media (prefers-color-scheme: dark) {
        .api-status-title {
            color: #e6edf3;
        }
    }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: transparent;
        border-bottom: 2px solid #e0e7ff;
        padding: 0.5rem 0;
    }
    
    @media (prefers-color-scheme: dark) {
        .stTabs [data-baseweb="tab-list"] {
            border-bottom: 2px solid #30363d;
        }
    }
    
    .stTabs [data-baseweb="tab-list"] button {
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 8px 8px 0 0;
        transition: all 0.3s ease;
        color: #666666;
        background: transparent;
        border: none;
        outline: none;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 700;
    }
    
    /* BUTTONS */
    .stButton > button {
        border-radius: 8px;
        transition: all 0.3s ease;
        font-weight: 600;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* METRICS */
    .stMetric {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border-top: 4px solid #2563eb;
    }
    
    @media (prefers-color-scheme: dark) {
        .stMetric {
            background: #161b22;
            border-top: 4px solid #58a6ff;
        }
    }
    
    /* TEXT */
    h1, h2, h3, h4, h5, h6 {
        color: #0d1117;
    }
    
    @media (prefers-color-scheme: dark) {
        h1, h2, h3, h4, h5, h6 {
            color: #e6edf3;
        }
    }

    /* ==== AI assistant response bubble ==== */
    .ai-response-box {
        background-color: rgba(255, 255, 255, 0.96);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08);
        max-height: 360px;
        overflow-y: auto;
        word-wrap: break-word;
        white-space: pre-wrap;
    }

    @media (prefers-color-scheme: dark) {
        .ai-response-box {
            background-color: #020617;
            border-color: #1f2937;
        }
    }

    /* ==== Chat input - fixed at bottom, ChatGPT style ==== */
    .stChatInput {
        position: fixed;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 100%;
        max-width: 900px;
        padding: 0.4rem 1rem 0.85rem 1rem;
        background: transparent;
        z-index: 1000;
    }

    .stChatInput > div {
        border-radius: 999px;
        border: 1px solid rgba(148, 163, 184, 0.65);
        background-color: rgba(15, 23, 42, 0.98);
        box-shadow: 0 12px 32px rgba(15, 23, 42, 0.5);
    }

    @media (prefers-color-scheme: light) {
        .stChatInput > div {
            background-color: #f9fafb;
            border-color: #e5e7eb;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.18);
        }
    }

    .stChatInput textarea,
    .stChatInput input {
        min-height: 52px;
        max-height: 120px;
        border-radius: 999px !important;
        font-size: 0.95rem;
    }

    /* Leave room at bottom so messages aren't covered by fixed input */
    .main {
        padding-bottom: 5.5rem;
    }

    /* ==== Raw LLM output cards (Gemini / Ollama) ==== */
    .raw-llm-card {
        border-radius: 14px;
        padding: 0.85rem 1rem 0.9rem 1rem;
        margin-top: 0.75rem;
        margin-bottom: 0.75rem;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
            sans-serif;
        border: 1px solid rgba(148, 163, 184, 0.45);
        box-shadow: 0 14px 30px rgba(15, 23, 42, 0.25);
        background: #0b1120;
        color: #e5e7eb;
    }

    .raw-llm-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 0.4rem;
    }

    .raw-llm-badge {
        font-size: 0.7rem;
        font-weight: 650;
        padding: 3px 9px;
        border-radius: 999px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: white;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
    }

    .raw-llm-badge-gemini {
        background: linear-gradient(135deg, #38bdf8, #6366f1);
    }

    .raw-llm-badge-ollama {
        background: linear-gradient(135deg, #22c55e, #16a34a);
    }

    .raw-llm-meta {
        font-size: 0.78rem;
        color: #cbd5f5;
        opacity: 0.9;
        white-space: nowrap;
    }

    .raw-llm-body {
        margin-top: 0.25rem;
    }

    .raw-llm-output {
        font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo,
            Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        margin: 0;
        padding: 0.65rem 0.8rem;
        border-radius: 9px;
        background: #020617;
        color: #e5e7eb;
        max-height: 260px;
        overflow-y: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        font-size: 0.86rem;
        line-height: 1.45;
        border: 1px solid rgba(31, 41, 55, 0.95);
    }

    @media (prefers-color-scheme: light) {
        .raw-llm-card {
            background: #f9fafb;
            color: #111827;
            border-color: #e5e7eb;
        }

        .raw-llm-meta {
            color: #4b5563;
        }

        .raw-llm-output {
            background: #ffffff;
            color: #111827;
            border-color: #e5e7eb;
        }
    }

    /* Optional: generic raw-output box (if you use raw-output-box somewhere else) */
    .raw-output-box {
        background-color: #0d1117;
        color: springgreen;
        padding: 20px;
        border-radius: 12px;
        margin-top: 20px;
        border: 1px solid #30363d;
        font-family: "Consolas", "Monaco", "Courier New", monospace;
        font-size: 20px;
        white-space: pre-wrap;
        overflow-x: auto;
        line-height: 1.5;
    }

    .raw-output-title {
        background: #238636;
        color: white;
        display: inline-block;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .raw-output.header{
        color: springgreen;
        background-color: #0d1117;
    }
    .raw-output-title.gemini {
        background: #0969da;
    }

    .raw-output-meta {
        color: #8b949e;
        font-size: 12px;
        margin-bottom: 10px;
    }

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================================
# SECTION 4: Session State Initialization
# ============================================================================

def initialize_session_state():
    """Initialize all session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "doc_count" not in st.session_state:
        st.session_state.doc_count = 0

    if "sidebar_theme" not in st.session_state:
        st.session_state.sidebar_theme = "Light"

    if "sidebar_search_results" not in st.session_state:
        st.session_state.sidebar_search_results = 5

    if "sidebar_auto_refresh" not in st.session_state:
        st.session_state.sidebar_auto_refresh = False

    if "sidebar_show_advanced" not in st.session_state:
        st.session_state.sidebar_show_advanced = False

    if "backend_connected" not in st.session_state:
        st.session_state.backend_connected = False

    if "model_mode" not in st.session_state:
        st.session_state.model_mode = "best"


initialize_session_state()

# ============================================================================
# SECTION 5: Sidebar
# ============================================================================

render_sidebar()

# ============================================================================
# SECTION 6: Header
# ============================================================================

st.markdown(
    """
<div class="header-container">
    <h1 class="header-title">💼 Finance Chatbot</h1>
    <p class="header-subtitle">Intelligent Document Analysis & Q&A System</p>
</div>
""",
    unsafe_allow_html=True,
)

# ============================================================================
# SECTION 7: API Status
# ============================================================================

def get_api_status():
    """Get detailed API status information"""
    try:
        backend_response = requests.get(
            "http://127.0.0.1:5000/api/status", timeout=5
        )
        backend_status = (
            backend_response.json()
            if backend_response.status_code == 200
            else {}
        )
    except Exception:
        backend_status = {}

    # Check Google API
    google_api_key = ""
    try:
        with open("../backend/.env", "r") as f:
            for line in f:
                if "GOOGLE_API_KEY" in line and "=" in line:
                    key_part = line.split("=", 1)[1].strip()
                    if key_part and not key_part.startswith("#"):
                        google_api_key = key_part
                    break
    except Exception:
        google_api_key = ""

    google_status = "🟢 Configured" if google_api_key else "🔴 Not Configured"

    # Check Ollama
    try:
        ollama_response = requests.get(
            "http://localhost:11434/api/tags", timeout=5
        )
        ollama_status = (
            "🟢 Connected"
            if ollama_response.status_code == 200
            else "🔴 Offline"
        )
    except Exception:
        ollama_status = "🔴 Offline"

    backend_state = (
        "🟢 Running"
        if backend_status.get("backend") == "running"
        else "🔴 Offline"
    )

    return {
        "google": google_status,
        "ollama": ollama_status,
        "backend": backend_state,
        "documents": backend_status.get("documents", 0),
    }


# Display API Status
st.markdown(
    """
<div class="api-status-header">
    <h3 class="api-status-title">🔌 API & Service Status</h3>
    <div class="api-status-grid">
""",
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)
api_status = get_api_status()

with col1:
    st.metric(label="Google API", value=api_status["google"])

with col2:
    st.metric(label="Ollama LLM", value=api_status["ollama"])

with col3:
    st.metric(label="Backend Server", value=api_status["backend"])

with col4:
    st.metric(label="Documents", value=api_status["documents"])

st.markdown("</div></div>", unsafe_allow_html=True)

st.markdown("---")

# ============================================================================
# SECTION 8: Backend Connection Check
# ============================================================================

if not check_backend():
    st.error(
        "⚠️ **Backend Not Connected**\n\n"
        "Please start the Flask backend server:\n\n"
        "```bash\n"
        "cd backend\n"
        # "venv\\Scripts\\activate.bat  # Windows\n"
        # "source venv/bin/activate   # Mac/Linux\n"
        "python app.py\n"
        "```"
    )
    st.stop()

st.session_state.backend_connected = True

# ============================================================================
# SECTION 9: Main Content - Tabs
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs(
    ["💬 Chat", "📤 Upload", "🔍 Analyze Files", "📊 Statistics"]
)

# TAB 1: CHAT
with tab1:
    st.subheader("💬 Chat with Your Documents")
    chat_interface()

# TAB 2: UPLOAD
with tab2:
    st.subheader("📤 Upload & Process Documents")
    upload_interface()

# TAB 3: ANALYZE FILES
with tab3:
    st.subheader("🔍 AI-Powered File Analysis")
    file_analysis_interface()

# TAB 4: STATISTICS
with tab4:
    st.subheader("📊 System Statistics & Analytics")

    st.markdown("### 🤖 AI Services Status")
    show_ai_status()

    st.markdown("---")
    st.markdown("### 📈 Performance Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Total Documents", value=get_document_count())

    with col2:
        st.metric(
            label="Chat Messages", value=len(st.session_state.messages)
        )

    with col3:
        st.metric(label="Backend Status", value="🟢 Running")

    with col4:
        st.metric(
            label="Search Results",
            value=st.session_state.sidebar_search_results,
        )

    st.markdown("---")
    st.markdown("### ⚙️ Current Settings")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(f"**🎨 Theme:** {st.session_state.sidebar_theme} Mode")

    with col2:
        st.info(
            f"**🔄 Auto-Refresh:** "
            f"{'✅ Enabled' if st.session_state.sidebar_auto_refresh else '❌ Disabled'}"
        )

    with col3:
        st.info(
            f"**🔧 Advanced:** "
            f"{'✅ Enabled' if st.session_state.sidebar_show_advanced else '❌ Disabled'}"
        )

    st.markdown("---")
    st.markdown("### 💬 Chat History")

    if st.session_state.messages:
        st.success(f"✅ Total messages: **{len(st.session_state.messages)}**")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📋 Export Chat", use_container_width=True):
                chat_text = (
                    "Finance Chatbot - Chat History\n"
                    + "=" * 60
                    + "\n\n"
                )
                for i, msg in enumerate(st.session_state.messages, 1):
                    role = (
                        "👤 USER"
                        if msg["role"] == "user"
                        else "🤖 ASSISTANT"
                    )
                    chat_text += (
                        f"[{i}] {role}:\n{msg['content']}\n"
                        + "-" * 60
                        + "\n"
                    )

                st.download_button(
                    label="⬇️ Download",
                    data=chat_text,
                    file_name="chat_history.txt",
                    mime="text/plain",
                )

        with col2:
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
    else:
        st.info("📝 No messages yet")

# ============================================================================
# SECTION 10: Footer
# ============================================================================

st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 12px;'>"
    "💼 Finance Chatbot v2.0.0 | Built with Streamlit + Python | "
    "Powered by Google AI & Ollama | © 2025"
    "</p>",
    unsafe_allow_html=True,
)
