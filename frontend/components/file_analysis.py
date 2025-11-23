import streamlit as st
import requests
from utils.api_client import API_URL

# ============================================================
#   MAIN INTERFACE
# ============================================================

def file_analysis_interface():
    st.subheader("🔍 File Analysis")

    st.info(
        "📊 Upload files to analyze them using Google Generative AI and Ollama (local LLM).\n\n"
        "Supported: **PDF, DOCX, XLSX, TXT, PNG, JPG, JPEG**"
    )

    uploaded_files = st.file_uploader(
        "Choose files to analyze",
        type=["pdf", "docx", "xlsx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.markdown(f"### **Selected {len(uploaded_files)} file(s):**")
        for f in uploaded_files:
            st.write(f"✓ {f.name} ({f.size/1024:.1f} KB)")

        analysis_type = st.radio("Analysis Type", ["Single File Analysis", "Batch Analysis"])

        if st.button("🔍 Analyze Files", type="primary"):
            with st.spinner("🤖 Analyzing files with AI..."):
                try:
                    if analysis_type == "Single File Analysis":
                        for uploaded_file in uploaded_files:
                            analyze_single_file(uploaded_file)
                    else:
                        analyze_batch_files(uploaded_files)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


# ============================================================
#   SINGLE FILE ANALYSIS
# ============================================================

def analyze_single_file(file):
    try:
        response = requests.post(
            f"{API_URL}/api/analyze-file",
            files={"file": (file.name, file.read(), file.type)},
            timeout=90
        )

        if response.status_code != 200:
            st.error(f"❌ Analysis failed: {response.json().get('error')}")
            return

        data = response.json()

        st.markdown(f"## 📄 {file.name}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Size", f"{data['file']['file_size_kb']} KB")
        with col2:
            st.metric("Type", data['file']['file_type'])
        with col3:
            st.metric("Status", "✓ Analyzed")

        with st.expander("📋 Preview"):
            st.text(data.get("preview", "No preview available."))

        st.markdown("---")

        google_res = data["analysis"]["google"]
        st.markdown("### 🔵 Google Generative AI Analysis")
        if google_res.get("status") == "success":
            st.markdown(google_res.get("analysis", ""))
        else:
            st.warning(f"⚠️ {google_res.get('error', 'Google analysis failed')}")

        ollama_res = data["analysis"]["ollama"]
        st.markdown("### 🟢 Ollama (Local LLM) Analysis")
        if ollama_res.get("status") == "success":
            st.markdown(ollama_res.get("analysis", ""))
        else:
            st.warning(f"⚠️ {ollama_res.get('error', 'Ollama analysis failed')}")

        st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


# ============================================================
#   BATCH ANALYSIS
# ============================================================

def analyze_batch_files(files):
    try:
        file_tuples = [("files", (f.name, f.read(), f.type)) for f in files]

        response = requests.post(
            f"{API_URL}/api/batch-analyze",
            files=file_tuples,
            timeout=180
        )

        if response.status_code != 200:
            st.error("❌ Batch analysis failed.")
            return

        data = response.json()

        st.success(f"✅ Analyzed {data['files_analyzed']} file(s)")

        for result in data["results"]:
            with st.expander(f"📄 {result['file']['filename']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Size", f"{result['file']['file_size_kb']} KB")
                with col2:
                    st.metric("Type", result['file']['file_type'])

                st.markdown("### 🔵 Google Analysis")
                if result["analysis"]["google"]["status"] == "success":
                    st.markdown(result["analysis"]["google"]["analysis"])
                else:
                    st.warning(result["analysis"]["google"].get("error", "Failed"))

                st.markdown("### 🟢 Ollama Analysis")
                if result["analysis"]["ollama"]["status"] == "success":
                    st.markdown(result["analysis"]["ollama"]["analysis"])
                else:
                    st.warning(result["analysis"]["ollama"].get("error", "Failed"))

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


# ============================================================
#   AI SERVICES STATUS (used by Statistics tab)
# ============================================================

def show_ai_status():
    """Display AI services status"""
    try:
        response = requests.get(f"{API_URL}/api/ai-status", timeout=5)
        if response.status_code == 200:
            status = response.json()

            col1, col2 = st.columns(2)
            with col1:
                google_icon = "🟢" if status["google_api"] == "configured" else "🔴"
                st.metric("Google API", f"{google_icon} {status['google_api']}")
            with col2:
                ollama_icon = "🟢" if status["ollama"] == "connected" else "🔴"
                st.metric("Ollama", f"{ollama_icon} {status['ollama']}")
    except Exception:
        st.warning("⚠️ Could not check AI services status")
