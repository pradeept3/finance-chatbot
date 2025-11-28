# ============================================================================
# frontend/streamlit_app.py - WITH AUTHENTICATION
# ============================================================================

import os
import sys
import streamlit as st
import requests

# Ensure the "frontend" directory (this file's dir) is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# 👇 FIRST Streamlit command – MUST be before any other st.* usage
st.set_page_config(
    page_title="Finance Chatbot",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 👇 All other imports that use Streamlit come *after* set_page_config
from components.sidebar import render_sidebar
from components.chat import chat_interface
from components.upload import upload_interface
from components.file_analysis import file_analysis_interface, show_ai_status
from utils.api_client import get_document_count, check_backend, API_URL

# 🔐 Import authentication system
from components.auth import (
    check_authentication,
    user_profile_sidebar,
    is_admin,
    is_student,
    admin_user_management
)


# ============================================================================
# SECTION 1: Custom CSS (Enhanced version from document)
# ============================================================================

# [PASTE YOUR ENHANCED CSS HERE - The complete CSS from the artifact above]
st.markdown(
    """
<style>
    /* [PASTE THE COMPLETE ENHANCED CSS HERE] */
    /* For brevity, I'm showing placeholder - use the full CSS from previous artifact */

/* ==================== FONT IMPORTS ==================== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Poppins:wght@400;500;600;700&display=swap');

:root {
    --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-heading: 'Poppins', sans-serif;
    --font-mono: 'JetBrains Mono', 'Consolas', monospace;
    
    /* Light theme colors */
    --light-bg-primary: #fafbfc;
    --light-bg-secondary: #ffffff;
    --light-bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --light-text-primary: #1a202c;
    --light-text-secondary: #4a5568;
    --light-accent: #667eea;
    --light-border: #e2e8f0;
    --light-shadow: rgba(0, 0, 0, 0.1);
    
    /* Dark theme colors */
    --dark-bg-primary: #0d1117;
    --dark-bg-secondary: #161b22;
    --dark-bg-gradient: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
    --dark-text-primary: #e6edf3;
    --dark-text-secondary: #8b949e;
    --dark-accent: #58a6ff;
    --dark-border: #30363d;
    --dark-shadow: rgba(0, 0, 0, 0.4);
}

/* ==================== GLOBAL FONT STYLING ==================== */
* {
    font-family: var(--font-primary) !important;
}

body {
    font-family: var(--font-primary);
    font-size: 16px;
    line-height: 1.6;
    color: var(--light-text-primary);
    background: var(--light-bg-primary);
}

@media (prefers-color-scheme: dark) {
    body {
        color: var(--dark-text-primary);
        background: var(--dark-bg-primary);
    }
}

/* ==================== HEADINGS ==================== */
h1, h2, h3, h4, h5, h6,
.header-title,
.api-status-title {
    font-family: var(--font-heading) !important;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--light-text-primary);
    line-height: 1.3;
}

@media (prefers-color-scheme: dark) {
    h1, h2, h3, h4, h5, h6,
    .header-title,
    .api-status-title {
        color: var(--dark-text-primary);
    }
}

h1, .header-title {
    font-size: 2.75rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ff6f00 0%, #f0f0f0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

h2 {
    font-size: 2rem;
    font-weight: 700;
}

h3 {
    font-size: 1.5rem;
    font-weight: 600;
}

h4 {
    font-size: 1.25rem;
    font-weight: 600;
}

/* ==================== MAIN CONTAINER ==================== */
.main {
    padding: 2rem 3rem 6rem 3rem;
    background: linear-gradient(135deg, #f5f7fa 0%, #e8edf2 50%, #dfe5ef 100%);
    min-height: 100vh;
}

@media (prefers-color-scheme: dark) {
    .main {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1a1f2e 100%);
    }
}

/* ==================== HEADER STYLING ==================== */
.header-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2.5rem 2rem;
    border-radius: 20px;
    margin-bottom: 2rem;
    box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
    position: relative;
    overflow: hidden;
}

.header-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at top right, rgba(255,255,255,0.1) 0%, transparent 70%);
    pointer-events: none;
}

@media (prefers-color-scheme: dark) {
    .header-container {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    }
}

.header-subtitle {
    font-family: var(--font-primary);
    font-size: 1.15rem;
    margin-top: 0.75rem;
    color: rgba(255, 255, 255, 0.95);
    font-weight: 400;
    letter-spacing: 0.5px;
}

/* ==================== API STATUS HEADER ==================== */
.api-status-header {
    background: white;
    border-radius: 16px;
    padding: 1.75rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
    border: 2px solid #e0e7ff;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.api-status-header:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
}

@media (prefers-color-scheme: dark) {
    .api-status-header {
        background: #161b22;
        border: 2px solid #30363d;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }
}

.api-status-title {
    font-size: 1.4rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
}

/* ==================== TABS ==================== */
.stTabs {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

@media (prefers-color-scheme: dark) {
    .stTabs {
        background: #161b22;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }
}

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
    padding: 0.85rem 1.75rem;
    font-size: 1.05rem;
    font-weight: 600;
    border-radius: 12px;
    transition: all 0.3s ease;
    color: #64748b;
    background: transparent;
    border: none;
    font-family: var(--font-heading) !important;
}

.stTabs [data-baseweb="tab-list"] button:hover {
    background: rgba(102, 126, 234, 0.1);
    color: #667eea;
}

.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* ==================== BUTTONS ==================== */
.stButton > button {
    border-radius: 12px;
    transition: all 0.3s ease;
    font-weight: 600;
    font-family: var(--font-primary) !important;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

/* ==================== METRICS ==================== */
.stMetric {
    background: white;
    padding: 1.75rem;
    border-radius: 16px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    border-top: 4px solid #667eea;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stMetric:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

@media (prefers-color-scheme: dark) {
    .stMetric {
        background: #161b22;
        border-top: 4px solid #58a6ff;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }
}

.stMetric label {
    font-family: var(--font-primary) !important;
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
}

@media (prefers-color-scheme: dark) {
    .stMetric label {
        color: #8b949e;
    }
}

.stMetric [data-testid="stMetricValue"] {
    font-family: var(--font-heading) !important;
    font-size: 2rem;
    font-weight: 700;
}

/* ==================== CHAT INPUT ==================== */
.stChatInput {
    position: fixed;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 100%;
    /* max-width: 900px; */
    padding: 0.4rem 1rem 0.85rem 1rem;
    background: transparent;
    z-index: 1000;
}

.stChatInput > div {
    border-radius: 999px;
    border: 2px solid rgba(102, 126, 234, 0.3);
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(249, 250, 251, 0.98) 100%);
    box-shadow: 0 12px 40px rgba(15, 23, 42, 0.15);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

.stChatInput > div:focus-within {
    border-color: #667eea;
    box-shadow: 0 16px 48px rgba(102, 126, 234, 0.25);
}

@media (prefers-color-scheme: dark) {
    .stChatInput > div {
        background: linear-gradient(135deg, rgba(22, 27, 34, 0.98) 0%, rgba(13, 17, 23, 0.98) 100%);
        border-color: rgba(88, 166, 255, 0.3);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
    }
    
    .stChatInput > div:focus-within {
        border-color: #58a6ff;
        box-shadow: 0 16px 48px rgba(88, 166, 255, 0.3);
    }
}

.stChatInput textarea,
.stChatInput input {
    min-height: 56px;
    max-height: 120px;
    border-radius: 999px !important;
    font-size: 1rem;
    font-family: var(--font-primary) !important;
    padding: 1rem 1.5rem;
}

/* ==================== CHAT MESSAGES ==================== */
.stChatMessage {
    background: transparent !important;
    padding: 1.25rem 0 !important;
    margin: 0.5rem 0;
}

.stChatMessage [data-testid="chatAvatarIcon-user"],
.stChatMessage [data-testid="chatAvatarIcon-assistant"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
}

/* ==================== AI RESPONSE BOX ==================== */
.ai-response-box {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(249, 250, 251, 0.98) 100%);
    border-radius: 16px;
    padding: 2rem;
    border: 2px solid #e5e7eb;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    margin: 1.5rem 0;
    word-wrap: break-word;
    line-height: 1.7;
    font-family: var(--font-primary);
}

@media (prefers-color-scheme: dark) {
    .ai-response-box {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border-color: #30363d;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }
}

/* ==================== RAW LLM OUTPUT CARDS ==================== */
.raw-llm-card {
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-top: 1rem;
    margin-bottom: 1rem;
    font-family: var(--font-primary);
    border: 2px solid rgba(102, 126, 234, 0.2);
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.1);
    background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);
    color: #1a202c;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.raw-llm-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(15, 23, 42, 0.15);
}

@media (prefers-color-scheme: dark) {
    .raw-llm-card {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        color: #e6edf3;
        border-color: rgba(88, 166, 255, 0.2);
    }
}

.raw-llm-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
}

.raw-llm-badge {
    font-family: var(--font-primary) !important;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 999px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: white;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
}

.raw-llm-badge-gemini {
    background: linear-gradient(135deg, #38bdf8, #3b82f6);
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.raw-llm-badge-ollama {
    background: linear-gradient(135deg, #22c55e, #16a34a);
    box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);
}

.raw-llm-meta {
    font-family: var(--font-mono) !important;
    font-size: 0.8rem;
    color: #64748b;
    opacity: 0.9;
    white-space: nowrap;
}

@media (prefers-color-scheme: dark) {
    .raw-llm-meta {
        color: #8b949e;
    }
}

.raw-llm-output {
    font-family: var(--font-mono) !important;
    margin: 0;
    padding: 1rem 1.25rem;
    border-radius: 12px;
    background: #fafbfc;
    color: #1a202c;
    max-height: 300px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 0.9rem;
    line-height: 1.6;
    border: 1px solid #e5e7eb;
}

@media (prefers-color-scheme: dark) {
    .raw-llm-output {
        background: #0d1117;
        color: #e6edf3;
        border-color: #30363d;
    }
}

/* ==================== CODE BLOCKS ==================== */
pre {
    background: #fafbfc !important;
    border: 2px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    overflow-x: auto !important;
    line-height: 1.6 !important;
    font-family: var(--font-mono) !important;
}

pre code {
    color: #1e293b !important;
    font-family: var(--font-mono) !important;
    font-size: 0.9rem !important;
}

@media (prefers-color-scheme: dark) {
    pre {
        background: #0d1117 !important;
        border: 2px solid #30363d !important;
    }

    pre code {
        color: #e2e8f0 !important;
    }
}

/* ==================== EXPANDER ==================== */
.streamlit-expanderHeader {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
    padding: 1.25rem !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-family: var(--font-heading) !important;
    transition: all 0.3s ease;
}

.streamlit-expanderHeader:hover {
    background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%) !important;
}

@media (prefers-color-scheme: dark) {
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #161b22 0%, #1a1f2e 100%) !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #1a1f2e 0%, #21262d 100%) !important;
    }
}

/* ==================== ALERTS & MESSAGES ==================== */
.stInfo {
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%) !important;
    border-left: 4px solid #0284c7 !important;
    border-radius: 12px !important;
    padding: 1.25rem !important;
    margin: 1rem 0 !important;
    font-family: var(--font-primary);
}

@media (prefers-color-scheme: dark) {
    .stInfo {
        background: linear-gradient(135deg, #082f49 0%, #0c4a6e 100%) !important;
        border-left-color: #0ea5e9 !important;
    }
}

.stSuccess {
    background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%) !important;
    border-left: 4px solid #22c55e !important;
    border-radius: 12px !important;
    padding: 1.25rem !important;
    font-family: var(--font-primary);
}

@media (prefers-color-scheme: dark) {
    .stSuccess {
        background: linear-gradient(135deg, #14532d 0%, #166534 100%) !important;
        border-left-color: #4ade80 !important;
    }
}

.stWarning {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%) !important;
    border-left: 4px solid #f59e0b !important;
    border-radius: 12px !important;
    padding: 1.25rem !important;
    font-family: var(--font-primary);
}

@media (prefers-color-scheme: dark) {
    .stWarning {
        background: linear-gradient(135deg, #78350f 0%, #92400e 100%) !important;
        border-left-color: #fbbf24 !important;
    }
}

.stError {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%) !important;
    border-left: 4px solid #ef4444 !important;
    border-radius: 12px !important;
    padding: 1.25rem !important;
    font-family: var(--font-primary);
}

@media (prefers-color-scheme: dark) {
    .stError {
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%) !important;
        border-left-color: #f87171 !important;
    }
}

/* ==================== MODEL INDICATORS ==================== */
.model-indicator {
    display: inline-block;
    padding: 0.35rem 1rem;
    border-radius: 999px;
    font-size: 0.9rem;
    font-weight: 700;
    margin: 0.5rem 0;
    font-family: var(--font-primary) !important;
    letter-spacing: 0.03em;
}

.model-google {
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
    color: #1e40af;
    border: 2px solid #93c5fd;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

@media (prefers-color-scheme: dark) {
    .model-google {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: #dbeafe;
        border: 2px solid #3b82f6;
    }
}

.model-ollama {
    background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
    color: #166534;
    border: 2px solid #86efac;
    box-shadow: 0 2px 8px rgba(34, 197, 94, 0.2);
}

@media (prefers-color-scheme: dark) {
    .model-ollama {
        background: linear-gradient(135deg, #15803d 0%, #22c55e 100%);
        color: #dcfce7;
        border: 2px solid #22c55e;
    }
}

.model-combined {
    background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
    color: #5b21b6;
    border: 2px solid #d8b4fe;
    box-shadow: 0 2px 8px rgba(168, 85, 247, 0.2);
}

@media (prefers-color-scheme: dark) {
    .model-combined {
        background: linear-gradient(135deg, #6b21a8 0%, #a855f7 100%);
        color: #f3e8ff;
        border: 2px solid #a855f7;
    }
}

/* ==================== SOURCES CONTAINER ==================== */
.sources-container {
    background: white;
    border: 2px solid #e5e7eb;
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1.5rem 0;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

@media (prefers-color-scheme: dark) {
    .sources-container {
        background: #161b22;
        border-color: #30363d;
    }
}

.source-item {
    padding: 1rem;
    background: #f9fafb;
    border-radius: 10px;
    margin: 0.75rem 0;
    border-left: 4px solid #3b82f6;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.source-item:hover {
    transform: translateX(4px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

@media (prefers-color-scheme: dark) {
    .source-item {
        background: #0d1117;
        border-left-color: #58a6ff;
    }
}

/* ==================== CAPTIONS ==================== */
.stCaption {
    color: #64748b;
    font-size: 0.9rem;
    margin: 0.35rem 0;
    font-family: var(--font-primary);
}

@media (prefers-color-scheme: dark) {
    .stCaption {
        color: #8b949e;
    }
}

/* ==================== SCROLLBAR ==================== */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

@media (prefers-color-scheme: dark) {
    ::-webkit-scrollbar-track {
        background: #1a1f2e;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
    }
}

/* ==================== DIVIDERS ==================== */
hr {
    margin: 2rem 0 !important;
    border: none !important;
    height: 2px !important;
    background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.3), transparent) !important;
}

@media (prefers-color-scheme: dark) {
    hr {
        background: linear-gradient(90deg, transparent, rgba(88, 166, 255, 0.3), transparent) !important;
    }
}

/* ==================== RESPONSIVE DESIGN ==================== */
@media (max-width: 768px) {
    .main {
        padding: 1rem 1.5rem 6rem 1.5rem;
    }
    
    .header-title {
        font-size: 2rem;
    }
    
    .header-subtitle {
        font-size: 1rem;
    }
    
    .stChatInput {
        max-width: 100%;
        padding: 0.4rem 0.75rem 0.85rem 0.75rem;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================================
# SECTION 2: Session State Initialization
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

    # ✅ CHANGED: Google as default instead of "best"
    if "model_mode" not in st.session_state:
        st.session_state.model_mode = "Google only"
    
    # 🔐 Authentication states
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "user" not in st.session_state:
        st.session_state.user = None


initialize_session_state()


# ============================================================================
# SECTION 3: Authentication Check
# ============================================================================

# 🔐 Check if user is authenticated - if not, show login page
check_authentication()


# ============================================================================
# SECTION 4: Sidebar (with User Profile)
# ============================================================================

# Show user profile in sidebar
user_profile_sidebar()

# Show sidebar based on role
if is_admin():
    # Admin sees full sidebar
    render_sidebar()
else:
    # Students see limited sidebar (only theme)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Settings")
    
    theme_option = st.sidebar.selectbox(
        "🎨 Theme",
        ["Light", "Dark", "Auto"],
        index=0,
        key="student_theme"
    )
    st.session_state.sidebar_theme = theme_option
    
    st.sidebar.info("🎓 **Student Mode** - Limited access")


# ============================================================================
# SECTION 5: Header
# ============================================================================

# Welcome message with user name
user_name = st.session_state.user.get("name", "User")
role_badge = "👑 Admin" if is_admin() else "🎓 Student"

st.markdown(
    f"""
<div class="header-container">
    <h1 class="header-title">💼 Finance Chatbot</h1>
    <p class="header-subtitle">Intelligent Document Analysis & Q&A System</p>
    <p style="margin-top: 1rem; font-size: 1rem; opacity: 0.9;">
        Welcome back, <strong>{user_name}</strong> | {role_badge}
    </p>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================================
# SECTION 6: API Status Display (Admin Only)
# ============================================================================

def get_api_status():
    """Get detailed API status information"""
    backend_status = {}
    try:
        resp = requests.get(f"{API_URL}/api/status", timeout=5)
        if resp.status_code == 200:
            backend_status = resp.json()
            print("[Status] Backend responded OK")
        else:
            print(f"[Status] Backend returned {resp.status_code}")
    except Exception as e:
        print(f"[Status] Backend error: {e}")

    # Check Google API - WITHOUT exposing the key
    google_status = "🟢 Configured"
    try:
        backend_resp = requests.get(f"{API_URL}/api/ai-status", timeout=5)
        if backend_resp.status_code == 200:
            ai_status = backend_resp.json()
            google_status = (
                "🟢 Configured" 
                if ai_status.get("google_api") == "configured" 
                else "🔴 Not Configured"
            )
    except Exception:
        google_status = "🔴 Not Configured"

    # Check Ollama
    ollama_status = "🔴 Offline"
    try:
        ollama_resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if ollama_resp.status_code == 200:
            ollama_status = "🟢 Connected"
    except Exception:
        pass

    backend_state = "🟢 Running" if backend_status.get("backend") == "running" else "🔴 Offline"

    return {
        "google": google_status,
        "ollama": ollama_status,
        "backend": backend_state,
        "documents": backend_status.get("documents", 0),
    }


# Only show API status for admins
if is_admin():
    st.markdown(
    """
<div class="api-status-header">
        <h3 class="api-status-title">🔌 API & Service Status</h3>
</div>
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

st.markdown("---")


# ============================================================================
# SECTION 6: Backend Connection Check
# ============================================================================

print("\n" + "="*60)
print(f"[Startup] Checking backend at: {API_URL}")
print("="*60)

backend_ok = check_backend(timeout=5)

if not backend_ok:
    st.error(
        f"⚠️ **Backend Not Connected**\n\n"
        f"Cannot reach backend at: **{API_URL}**\n\n"
        f"Please start the Flask backend server:\n\n"
        f"```bash\n"
        f"cd backend\n"
        f"python app.py\n"
        f"```\n\n"
        f"The backend should start on: **http://127.0.0.1:5000**"
    )
    st.stop()

st.session_state.backend_connected = True
print("[Startup] ✓ Backend connection verified")

# ============================================================================
# SECTION 7: Main Content - Tabs
# ============================================================================

if is_admin():
    # 👑 ADMIN VIEW - Full Access
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["💬 Chat", "📤 Upload", "🔍 Analyze Files", "📊 Statistics", "👥 Users"]
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

    # TAB 5: USER MANAGEMENT
    with tab5:
        st.subheader("👥 User Management")
        admin_user_management()

else:
    # 🎓 STUDENT VIEW - Limited Access (Chat + Theme Only)
    st.info("🎓 **Student Mode** - You have access to chat functionality and theme settings")
    
    tab1, tab2 = st.tabs(["💬 Chat", "ℹ️ Info"])

    # TAB 1: CHAT
    with tab1:
        st.subheader("💬 Chat with Documents")
        chat_interface()

    # TAB 2: INFO
    with tab2:
        st.subheader("ℹ️ Information")
        
        st.markdown("""
        ### 🎓 Welcome to Finance Chatbot Student Portal
        
        As a student, you have access to:
        
        ✅ **Chat Interface** - Ask questions about uploaded documents
        ✅ **Theme Settings** - Customize your viewing experience
        
        #### 📝 How to Use:
        
        1. **Navigate to the Chat tab**
        2. **Type your question** in the chat input at the bottom
        3. **Press Enter** to get AI-powered answers
        4. **Review sources** to see where the information came from
        
        #### 💡 Tips for Better Results:
        
        - Be specific with your questions
        - Ask one question at a time
        - Use proper terminology related to finance
        - Review the suggested follow-up questions
        
        #### 🆘 Need Help?
        
        Contact your administrator if you:
        - Cannot access certain documents
        - Experience technical issues
        - Need additional features
        
        ---
        
        **Current Session Info:**
        - 👤 User: {user_name}
        - 🎨 Theme: {st.session_state.sidebar_theme}
        - 📚 Available Documents: {get_document_count()}
        """)
        
        # Quick Stats
        st.markdown("### 📊 Your Activity")

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
# SECTION 9: Footer
# ============================================================================

st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 12px;'>"
    "💼 Finance Chatbot v2.1.0 | Built with Streamlit + Python | "
    "Powered by Google AI & Ollama | © 2025 | 🔐 Secure Login System"
    "</p>",
    unsafe_allow_html=True,
)

