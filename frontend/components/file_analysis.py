import streamlit as st
import requests
from utils.api_client import API_URL

# ============================================================
#   MAIN INTERFACE
# ============================================================

def file_analysis_interface():
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
            st.error(f"❌ Analysis failed: {response.json().get('error', 'Unknown error')}")
            return

        data = response.json()

        st.markdown(f"## 📄 {file.name}")

        col1, col2, col3 = st.columns(3)
        with col1:
            file_size_mb = data['file'].get('size_mb', 0)
            st.metric("File Size", f"{file_size_mb} MB")
        with col2:
            ext = data['file'].get('extension', 'Unknown')
            st.metric("Type", ext)
        with col3:
            st.metric("Status", "✓ Analyzed")

        with st.expander("📋 Preview"):
            preview = data.get("preview", "No preview available.")
            if isinstance(preview, str) and len(preview) > 0:
                st.text(preview[:2000])
            else:
                st.text("No preview available")

        st.markdown("---")

        google_res = data["analysis"]["google"]
        st.markdown("### 🔵 Google Generative AI Analysis")
        if google_res.get("status") == "success":
            analysis_text = google_res.get("analysis", "")
            if analysis_text:
                st.markdown(analysis_text)
            else:
                st.warning("No analysis returned")
        else:
            error_msg = google_res.get('error', 'Google analysis failed')
            st.warning(f"⚠️ {error_msg}")

        ollama_res = data["analysis"]["ollama"]
        st.markdown("### 🟢 Ollama (Local LLM) Analysis")
        if ollama_res.get("status") == "success":
            analysis_text = ollama_res.get("analysis", "")
            if analysis_text:
                st.markdown(analysis_text)
            else:
                st.warning("No analysis returned")
        else:
            error_msg = ollama_res.get('error', 'Ollama analysis failed')
            st.warning(f"⚠️ {error_msg}")

        st.markdown("---")

    except requests.exceptions.Timeout:
        st.error("❌ Request timed out. The server took too long to respond.")
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to backend at {API_URL}")
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
            st.error(response.json().get("error", "Unknown error"))
            return

        data = response.json()

        st.success(f"✅ Analyzed {data['files_analyzed']} file(s)")

        for result in data["results"]:
            filename = result['file'].get('filename', 'Unknown')
            with st.expander(f"📄 {filename}"):
                col1, col2 = st.columns(2)
                with col1:
                    size_mb = result['file'].get('size_mb', 0)
                    st.metric("Size", f"{size_mb} MB")
                with col2:
                    ext = result['file'].get('extension', 'Unknown')
                    st.metric("Type", ext)

                st.markdown("### 🔵 Google Analysis")
                if result["analysis"]["google"]["status"] == "success":
                    google_text = result["analysis"]["google"].get("analysis", "")
                    if google_text:
                        st.markdown(google_text)
                    else:
                        st.text("No response")
                else:
                    error = result["analysis"]["google"].get("error", "Failed")
                    st.warning(f"⚠️ {error}")

                st.markdown("### 🟢 Ollama Analysis")
                if result["analysis"]["ollama"]["status"] == "success":
                    ollama_text = result["analysis"]["ollama"].get("analysis", "")
                    if ollama_text:
                        st.markdown(ollama_text)
                    else:
                        st.text("No response")
                else:
                    error = result["analysis"]["ollama"].get("error", "Failed")
                    st.warning(f"⚠️ {error}")

    except requests.exceptions.Timeout:
        st.error("❌ Request timed out. Files may be too large.")
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to backend at {API_URL}")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


# ============================================================
#   AI SERVICES STATUS
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
        else:
            st.warning("⚠️ Could not get AI status")
    except Exception as e:
        st.warning(f"⚠️ Could not check AI services: {str(e)}")