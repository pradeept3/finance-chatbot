# frontend/utils/api_client.py

import os
from typing import Any, Dict, List
import requests

# Point this at your Flask backend - MUST match backend host:port
API_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5000")

print(f"[API Client] Configured to use: {API_URL}")


# -------------------------------------------------------------------
# Health & status helpers (used in sidebar / main header)
# -------------------------------------------------------------------
def get_backend_status(timeout: float = 5.0) -> Dict[str, Any]:
    """
    Return status dict from /api/status, or {'status': 'offline'} on error.
    """
    try:
        resp = requests.get(f"{API_URL}/api/status", timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
    except requests.exceptions.ConnectionError as e:
        print(f"[get_backend_status] Connection error: {e}")
    except requests.exceptions.Timeout:
        print(f"[get_backend_status] Timeout connecting to {API_URL}")
    except Exception as e:
        print(f"[get_backend_status] Error: {e}")
    
    return {"status": "offline", "error": "Connection failed"}


def check_backend(timeout: float = 5.0) -> bool:
    """True if backend is responding properly."""
    try:
        resp = requests.get(f"{API_URL}/api/health", timeout=timeout)
        is_healthy = resp.status_code == 200
        print(f"[check_backend] Backend health: {resp.status_code} - {'OK' if is_healthy else 'ERROR'}")
        return is_healthy
    except Exception as e:
        print(f"[check_backend] Backend unreachable: {e}")
        return False


def get_document_count(timeout: float = 5.0) -> int:
    """Number of chunks/documents stored in ChromaDB."""
    try:
        resp = requests.get(f"{API_URL}/api/documents", timeout=timeout)
        if resp.status_code == 200:
            count = int(resp.json().get("total_documents", 0))
            print(f"[get_document_count] Found {count} documents")
            return count
    except Exception as e:
        print(f"[get_document_count] Error: {e}")
    return 0


# -------------------------------------------------------------------
# Chat helper
# -------------------------------------------------------------------
def send_message(message: str, timeout: float = 60.0) -> Dict[str, Any]:
    """
    Call /api/chat with the user's message.

    On success: backend JSON (with 'response', 'key_points', etc.).
    On timeout: {'timeout': True, 'error': '...'}
    On other errors: {'error': '...'}
    """
    try:
        print(f"[send_message] Sending to {API_URL}/api/chat")
        resp = requests.post(
            f"{API_URL}/api/chat",
            json={"message": message},
            timeout=timeout,
        )
        
        if resp.status_code == 200:
            print("[send_message] ✓ Response received successfully")
            return resp.json()
        else:
            print(f"[send_message] ✗ HTTP {resp.status_code}")
            return {
                "error": f"HTTP {resp.status_code}",
                "response": None,
            }

    except requests.exceptions.Timeout:
        print("[send_message] ✗ Request timed out")
        return {
            "timeout": True,
            "error": "Request to backend timed out (60s+). Try a simpler query.",
            "response": None,
        }
    except requests.exceptions.ConnectionError as e:
        print(f"[send_message] ✗ Connection error: {e}")
        return {
            "error": f"Cannot connect to backend at {API_URL}",
            "response": None,
        }
    except Exception as e:
        print(f"[send_message] ✗ Unexpected error: {e}")
        return {
            "error": str(e),
            "response": None,
        }


# -------------------------------------------------------------------
# NEXT STEPS helper
# -------------------------------------------------------------------
def fetch_next_steps(
    user_question: str,
    answer_text: str,
    key_points: List[str] = None,
    timeout: float = 10.0,
) -> List[Dict[str, Any]]:
    """
    Call /api/next-steps to get recommended next actions.

    Returns a list like:
      [
        {"label": "...", "category": "...", "reason": "..."},
        ...
      ]
    """
    payload = {
        "user_question": user_question,
        "answer_text": answer_text,
        "key_points": key_points or [],
    }

    try:
        resp = requests.post(
            f"{API_URL}/api/next-steps",
            json=payload,
            timeout=timeout,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("suggestions", [])
    except Exception as e:
        print("[fetch_next_steps ERROR]", e)

    return []