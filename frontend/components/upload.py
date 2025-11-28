# ============================================================================
# frontend/components/upload.py - Fixed version
# ============================================================================

import streamlit as st
import requests
import os
import time
from utils.api_client import API_URL



def upload_interface():
    """File upload interface with URL support"""

    # st.subheader("📤 Upload & Process Documents")

    st.info(
        "📋 **Supported Formats:** PDF (with images), DOCX, XLSX, TXT, PNG, JPG, JPEG\n\n"
        "🌐 **URL Support:** Add web page URLs to extract content\n\n"
        "👁️ **Vision Enabled:** Images in PDFs are automatically analyzed\n\n"
        "**Max File Size:** 50 MB"
    )
    
    # ⭐ NEW: URL Input Section
    st.markdown("### 🌐 Add URLs (Optional)")
    
    url_input = st.text_area(
        "Enter URLs (one per line)",
        height=100,
        placeholder="https://example.com/article1\nhttps://example.com/article2",
        help="Add web page URLs to extract and index their content"
    )
    
    urls = []
    if url_input:
        urls = [url.strip() for url in url_input.split('\n') if url.strip()]
        if urls:
            st.success(f"✅ {len(urls)} URL(s) added")
            for url in urls:
                st.caption(f"🔗 {url}")
    
    st.markdown("---")
    st.markdown("### 📂 Select Files")

    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=["pdf", "docx", "xlsx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Select one or more documents or images",
    )

    if not uploaded_files and not urls:
        st.warning("👆 No files or URLs provided. Please upload files or add URLs above.")
        return

    # Show selected files
    if uploaded_files:
        st.markdown(f"### ✓ Selected {len(uploaded_files)} File(s)")

        total_size = 0
        for file in uploaded_files:
            file_size_mb = file.size / (1024 * 1024)
            total_size += file.size

            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.caption(f"📄 {file.name}")
            with col2:
                st.caption(f"{file_size_mb:.2f} MB")
            with col3:
                st.caption(file.type or "Unknown")

        st.caption(f"**Total Size:** {total_size / (1024 * 1024):.2f} MB")
    
    st.markdown("---")

    col1, _ = st.columns([3, 1])

    with col1:
        upload_clicked = st.button(
            "🚀 Upload & Process",
            key="btn_upload_files",
            use_container_width=True,
            type="primary",
            help="Upload files and/or process URLs",
        )

    if upload_clicked:
        upload_files_and_urls(uploaded_files, urls)


def upload_files_and_urls(uploaded_files, urls):
    """Upload files and URLs to backend"""
    if not uploaded_files and not urls:
        st.error("❌ No files or URLs provided")
        return

    progress_container = st.container()

    with progress_container:
        st.markdown("### 📊 Upload Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Prepare files
            files_to_upload = []
            if uploaded_files:
                for file in uploaded_files:
                    files_to_upload.append(
                        ("files", (file.name, file.getvalue(), file.type))
                    )
            
            # Prepare form data with URLs
            data = {}
            if urls:
                data["urls"] = urls

            status_text.info("⏳ Uploading to server...")
            progress_bar.progress(25)

            response = requests.post(
                f"{API_URL}/api/upload",
                files=files_to_upload if files_to_upload else None,
                data=data if data else None,
                timeout=180,
            )

            progress_bar.progress(50)

            if response.status_code == 200:
                result = response.json()

                progress_bar.progress(75)
                status_text.info("⏳ Processing...")
                time.sleep(1)
                progress_bar.progress(100)

                st.markdown("---")
                st.success("✅ Upload Successful!")

                results_col = st.container()
                with results_col:
                    st.markdown("### 📈 Upload Results")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(
                            label="Files",
                            value=len(result.get("files_uploaded", [])),
                        )
                    with col2:
                        st.metric(
                            label="URLs",
                            value=result.get("urls_processed", 0),
                        )
                    with col3:
                        st.metric(
                            label="Images",
                            value=result.get("images_processed", 0),
                        )
                    with col4:
                        st.metric(
                            label="Total Added",
                            value=result.get("documents_added", 0),
                        )

                    # Vision-enabled PDFs
                    if result.get("vision_enabled_pdfs", 0) > 0:
                        st.info(
                            f"👁️ **Vision Enabled:** {result['vision_enabled_pdfs']} PDF(s) processed with image extraction"
                        )

                    # Show uploaded files
                    if result.get("files_uploaded"):
                        st.markdown("### 📄 Uploaded Files")
                        for filename in result["files_uploaded"]:
                            st.caption(f"✓ {filename}")
                    
                    # Show processed URLs
                    if result.get("urls_processed", 0) > 0:
                        st.markdown("### 🌐 Processed URLs")
                        for url in urls:
                            st.caption(f"✓ {url}")

                    # Show errors
                    if result.get("errors"):
                        st.markdown("### ⚠️ Errors")
                        for error in result["errors"]:
                            st.warning(f"❌ {error}")

                    st.info(
                        f"✅ **{result.get('documents_added', 0)} items** added to knowledge base.\n\n"
                        "You can now ask questions in the **Chat** tab!"
                    )

                st.session_state.doc_count = get_total_documents()
                time.sleep(1)
                st.rerun()
            else:
                error_msg = response.json().get("message", "Unknown error")
                st.error(f"❌ Upload Failed: {error_msg}")

        except requests.exceptions.Timeout:
            st.error("❌ Upload Timeout")
            st.info("💡 Try smaller files or fewer items at once")

        except requests.exceptions.ConnectionError:
            st.error("❌ Connection Error")
            st.info("💡 Make sure backend is running")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            with st.expander("🔍 Error Details"):
                st.code(traceback.format_exc())






def upload_interface():
    """File upload interface with proper processing"""

    #st.subheader("📤 Upload & Process Documents")

    st.info(
        "📋 **Supported Formats:** PDF, DOCX, XLSX, TXT, PNG, JPG, JPEG\n\n"
        "**Max File Size:** 50 MB\n\n"
        "Files will be automatically processed and added to the knowledge base."
    )

    st.markdown("### 📂 Select Files")

    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=["pdf", "docx", "xlsx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Select one or more documents or images",
    )

    if not uploaded_files:
        st.warning("👆 No files selected. Please upload at least one file above.")
        return

    st.markdown(f"### ✓ Selected {len(uploaded_files)} File(s)")

    total_size = 0
    for file in uploaded_files:
        file_size_mb = file.size / (1024 * 1024)
        total_size += file.size

        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.caption(f"📄 {file.name}")
        with col2:
            st.caption(f"{file_size_mb:.2f} MB")
        with col3:
            st.caption(file.type or "Unknown")

    st.caption(f"**Total Size:** {total_size / (1024 * 1024):.2f} MB")
    st.markdown("---")

    col1, _ = st.columns([3, 1])

    with col1:
        upload_clicked = st.button(
            "🚀 Upload & Process Files",
            key="btn_upload_files",
            use_container_width=True,
            type="primary",
            help="Upload files and add to knowledge base",
        )

    if upload_clicked:
        upload_files_handler(uploaded_files)


def upload_files_handler(uploaded_files):
    if not uploaded_files:
        st.error("❌ No files selected")
        return

    progress_container = st.container()

    with progress_container:
        st.markdown("### 📊 Upload Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            files_to_upload = []
            for file in uploaded_files:
                files_to_upload.append(
                    ("files", (file.name, file.getvalue(), file.type))
                )

            status_text.info("⏳ Uploading files to server...")
            progress_bar.progress(25)

            response = requests.post(
                f"{API_URL}/api/upload",
                files=files_to_upload,
                timeout=120,
            )

            progress_bar.progress(50)

            if response.status_code == 200:
                result = response.json()

                progress_bar.progress(75)
                status_text.info("⏳ Processing documents...")
                time.sleep(1)
                progress_bar.progress(100)

                st.markdown("---")
                st.success("✅ Upload Successful!")

                results_col = st.container()
                with results_col:
                    st.markdown("### 📈 Upload Results")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            label="Files Uploaded",
                            value=len(result.get("files_uploaded", [])),
                        )
                    with col2:
                        st.metric(
                            label="Document Chunks",
                            value=result.get("documents_added", 0),
                        )
                    with col3:
                        st.metric(label="Status", value="✅ Complete")

                    if result.get("files_uploaded"):
                        st.markdown("### 📄 Uploaded Files")
                        for filename in result["files_uploaded"]:
                            st.caption(f"✓ {filename}")

                    if result.get("errors"):
                        st.markdown("### ⚠️ Errors")
                        for error in result["errors"]:
                            st.warning(f"❌ {error}")

                    st.info(
                        f"✅ **{result.get('documents_added', 0)} document chunks** have been added to the knowledge base.\n\n"
                        "You can now ask questions about these documents in the **Chat** tab!"
                    )

                st.session_state.doc_count = get_total_documents()
                time.sleep(1)
                st.rerun()
            else:
                error_msg = response.json().get("message", "Unknown error")
                st.error(f"❌ Upload Failed: {error_msg}")
                if response.json().get("errors"):
                    st.markdown("### Details:")
                    for error in response.json()["errors"]:
                        st.caption(f"⚠️ {error}")

        except requests.exceptions.Timeout:
            st.error("❌ Upload Timeout - The server took too long to respond")
            st.info("💡 Try uploading smaller files or fewer files at once")

        except requests.exceptions.ConnectionError:
            st.error("❌ Connection Error - Cannot reach backend server")
            st.info(
                "💡 Make sure the backend is running:\n"
                "```bash\ncd backend\npython app.py\n```"
            )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Check if all services are running properly")


def get_total_documents():
    try:
        response = requests.get(f"{API_URL}/api/documents", timeout=5)
        if response.status_code == 200:
            return response.json().get("total_documents", 0)
    except Exception:
        pass
    return 0
