import requests
import streamlit as st

# ✅ IMPORTANT: Backend runs on port 5000, not 5001
API_URL = "http://localhost:5000"


@st.cache_data(ttl=300)
def get_backend_status():
    """Return full backend status JSON, or None on error."""
    try:
        resp = requests.get(f"{API_URL}/api/status", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def check_backend() -> bool:
    """Quick health-check used to gate the app."""
    try:
        resp = requests.get(f"{API_URL}/api/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def send_message(message: str):
    """Send a chat message to the backend /api/chat endpoint."""
    try:
        resp = requests.post(
            f"{API_URL}/api/chat",
            json={"message": message},
            timeout=60,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            try:
                err = resp.json().get("error", resp.text)
            except Exception:
                err = resp.text
            st.error(f"Backend error: {err}")
            return None
    except requests.Timeout:
        st.error("⏰ Request timeout. Please try again.")
        return None
    except Exception as e:
        st.error(f"⚠️ Error talking to backend: {e}")
        return None


def upload_files(files):
    """
    Upload multiple files to /api/upload.

    `files` is expected to be a list of `UploadedFile` from st.file_uploader.
    """
    try:
        file_tuples = []
        for f in files:
            file_tuples.append(
                (
                    "files",
                    (f.name, f.read(), f.type or "application/octet-stream"),
                )
            )

        resp = requests.post(f"{API_URL}/api/upload", files=file_tuples, timeout=120)

        if resp.status_code == 200:
            return resp.json()
        else:
            try:
                err = resp.json().get("error", resp.text)
            except Exception:
                err = resp.text
            st.error(f"Upload error: {err}")
            return None
    except requests.Timeout:
        st.error("⏰ Upload timeout. Try smaller files or fewer at once.")
        return None
    except Exception as e:
        st.error(f"Upload error: {e}")
        return None


@st.cache_data(ttl=60)
def get_document_count() -> int:
    """Get total document count from /api/documents."""
    try:
        resp = requests.get(f"{API_URL}/api/documents", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return int(data.get("total_documents", 0))
    except Exception:
        pass
    return 0

# 🔽 ADD THIS NEW FUNCTION NEAR THE BOTTOM
# def send_email(subject: str, body: str) -> dict:
#     """Call backend to send an email via Agno EmailTools agent."""
#     try:
#         resp = requests.post(
#             f"{API_URL}/api/send-email",
#             json={"subject": subject, "body": body},
#             timeout=20,
#         )
#         if resp.status_code == 200:
#             return resp.json()
#         return {"sent": False, "error": f"HTTP {resp.status_code}"}
#     except Exception as e:
#         return {"sent": False, "error": str(e)}