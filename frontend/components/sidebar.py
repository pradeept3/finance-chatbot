import streamlit as st


def _init_sidebar_state():
    """Initialize sidebar-related session state keys."""
    if "model_mode" not in st.session_state:
        st.session_state.model_mode = "Google only"  # ✅ CHANGED: Google as default

    if "sidebar_theme" not in st.session_state:
        st.session_state.sidebar_theme = "Light"

    if "sidebar_search_results" not in st.session_state:
        st.session_state.sidebar_search_results = 5

    if "sidebar_auto_refresh" not in st.session_state:
        st.session_state.sidebar_auto_refresh = False

    if "sidebar_show_advanced" not in st.session_state:
        st.session_state.sidebar_show_advanced = False


def render_sidebar():
    """
    Draw the sidebar UI.
    This is the ONLY function that streamlit_app.py should import.
    """
    _init_sidebar_state()

    st.sidebar.title("⚙️ Settings")

    # Theme
    st.sidebar.markdown("### 🎨 Theme")
    st.session_state.sidebar_theme = st.sidebar.radio(
        "Choose a theme",
        ["Light", "Dark"],
        index=0 if st.session_state.sidebar_theme == "Light" else 1,
        key="sidebar_theme_radio",
    )

    st.sidebar.markdown("---")

    # LLM Mode - GOOGLE AS DEFAULT
    st.sidebar.markdown("### 🧠 LLM Model")

    # ✅ UPDATED: Google moved to top as default
    label_map = {
        "🔵 Google only": "Google only",  # ✅ MOVED TO TOP (default)
        "🟣 Best (Google + Ollama)": "Best (Google + Ollama)",
        "🟢 Ollama only": "Ollama only",
        "🔷 DeepSeek": "DeepSeek",
        "⚪ Context-only": "Context-only",
    }
    labels = list(label_map.keys())

    current_val = st.session_state.get("model_mode", "Google only")  # ✅ CHANGED
    current_label = next(
        (lbl for lbl, v in label_map.items() if v == current_val),
        "🔵 Google only",  # ✅ UPDATED default label
    )

    selected_label = st.sidebar.radio(
        "Choose model mode",
        options=labels,
        index=labels.index(current_label),
        key="sidebar_llm_mode_radio",
    )

    st.session_state.model_mode = label_map[selected_label]
    st.sidebar.caption(f"Current mode: **{st.session_state.model_mode}**")

    # Model descriptions
    if st.sidebar.checkbox("Show model info", value=False):
        st.sidebar.markdown("#### Model Information")
        st.sidebar.markdown("""
        **🔵 Google only** (Default)
        - Google Gemini API
        - Fast and accurate
        - Best for most use cases
        
        **🟣 Best (Google + Ollama)**
        - Uses both Google Gemini and Ollama
        - Most accurate, slower
        
        **🟢 Ollama only**
        - Local LLM model
        - Privacy-focused, may be slower
        
        **🔷 DeepSeek**
        - Open-source LLM
        - Free with API key
        - Good reasoning abilities
        
        **⚪ Context-only**
        - No LLM - uses document retrieval
        - Fastest, uses exact content
        """)

    st.sidebar.markdown("---")

    # Misc options
    st.sidebar.markdown("### 🔧 Additional Options")

    st.session_state.sidebar_auto_refresh = st.sidebar.checkbox(
        "Auto-refresh statistics",
        value=st.session_state.sidebar_auto_refresh,
        key="sidebar_auto_refresh_checkbox",
    )

    st.session_state.sidebar_show_advanced = st.sidebar.checkbox(
        "Show advanced options",
        value=st.session_state.sidebar_show_advanced,
        key="sidebar_show_advanced_checkbox",
    )

    # Display current API configuration
    # st.sidebar.markdown("---")
    # st.sidebar.markdown("### 📡 API Status")
    
    # import os
    # from dotenv import load_dotenv
    
    # load_dotenv()
    
    # google_key = "✅ Configured" if os.getenv("GOOGLE_API_KEY") else "❌ Not set"
    # deepseek_key = "✅ Configured" if os.getenv("DEEPSEEK_API_KEY") else "❌ Not set"
    # ollama_url = "✅ Available" if os.getenv("OLLAMA_API_URL") else "❌ Not set"
    
    # st.sidebar.metric("Google API", google_key)
    # st.sidebar.metric("DeepSeek API", deepseek_key)
    # st.sidebar.metric("Ollama", ollama_url)