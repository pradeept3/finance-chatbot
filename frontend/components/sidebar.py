import streamlit as st


def _init_sidebar_state():
    """Initialize sidebar-related session state keys."""
    if "model_mode" not in st.session_state:
        st.session_state.model_mode = "best"  # best / ollama / google / context-only

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

    # LLM Mode
    st.sidebar.markdown("### 🧠 LLM Mode")

    label_map = {
        "🟣 Best (Google + Ollama)": "best",
        "🟢 Ollama only": "ollama",
        "🔵 Google only": "google",
        "🟡 Context-only (no LLM)": "context-only",
    }
    labels = list(label_map.keys())

    current_val = st.session_state.get("model_mode", "best")
    current_label = next(
        (lbl for lbl, v in label_map.items() if v == current_val),
        "🟣 Best (Google + Ollama)",
    )

    selected_label = st.sidebar.radio(
        "Choose model mode",
        options=labels,
        index=labels.index(current_label),
        key="sidebar_llm_mode_radio",
    )

    st.session_state.model_mode = label_map[selected_label]
    st.sidebar.caption(f"Current LLM mode: **{st.session_state.model_mode}**")

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
