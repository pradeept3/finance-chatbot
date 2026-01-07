# frontend/utils/api_client.py - UPDATED FOR GOOGLE DEFAULT

import requests
import streamlit as st

# Backend API URL
API_URL = "http://127.0.0.1:5000"


def check_backend(timeout=5):
    """Check if backend is running"""
    try:
        response = requests.get(f"{API_URL}/api/status", timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def get_document_count():
    """Get total document count from backend"""
    try:
        response = requests.get(f"{API_URL}/api/documents", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("total_documents", 0)
        return 0
    except Exception as e:
        print(f"[Error] Failed to get document count: {e}")
        return 0


def send_message(query, use_google=True, use_ollama=False):
    """Send chat message to backend"""
    try:
        print(f"[API Client] Sending query: {query[:50]}...")
        
        # ✅ UPDATED: Get model_mode from sidebar with Google default
        model_mode = st.session_state.get("model_mode", "Google only")  # ✅ CHANGED
        print(f"[API Client] Model mode: {model_mode}")
        
        # Send model_mode to backend
        response = requests.post(
            f"{API_URL}/api/chat",
            json={
                "message": query,
                "model_mode": model_mode,
                "use_google": use_google,
                "use_ollama": use_ollama
            },
            timeout=120
        )
        
        print(f"[API Client] Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[API Client] Model used: {data.get('model_used', 'unknown')}")
            print(f"[API Client] Response keys: {list(data.keys())}")
            return data
        else:
            error_text = response.text[:200] if response.text else "No error message"
            print(f"[API Client] Error response: {error_text}")
            return {
                "error": f"Backend returned status {response.status_code}",
                "response": f"Error: {error_text}"
            }
    except requests.exceptions.Timeout:
        print("[API Client] Request timeout")
        return {
            "error": "Request timeout",
            "response": "The request took too long. Please try again."
        }
    except requests.exceptions.ConnectionError:
        print("[API Client] Connection error")
        return {
            "error": "Connection error",
            "response": "Cannot connect to backend. Please ensure the backend server is running."
        }
    except Exception as e:
        print(f"[API Client] Exception: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "response": f"An error occurred: {str(e)}"
        }


def upload_files(files):
    """Upload files to backend"""
    try:
        files_data = []
        for file in files:
            file.seek(0)
            files_data.append(
                ('files', (file.name, file.getvalue(), file.type))
            )
        
        response = requests.post(
            f"{API_URL}/api/upload",
            files=files_data,
            timeout=300
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Upload failed with status {response.status_code}"
            }
    except Exception as e:
        return {
            "error": str(e)
        }


def analyze_file(file, use_google=True, use_ollama=False):
    """Analyze a single file"""
    try:
        file.seek(0)
        
        files = {
            'file': (file.name, file.getvalue(), file.type)
        }
        
        data = {
            'use_google': str(use_google).lower(),
            'use_ollama': str(use_ollama).lower()
        }
        
        response = requests.post(
            f"{API_URL}/api/analyze-file",
            files=files,
            data=data,
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Analysis failed with status {response.status_code}"
            }
    except Exception as e:
        return {
            "error": str(e)
        }


def get_ai_status():
    """Get AI services status"""
    try:
        response = requests.get(f"{API_URL}/api/ai-status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {
            "google_api": "error",
            "ollama": "error"
        }
    except Exception as e:
        print(f"[Error] Failed to get AI status: {e}")
        return {
            "google_api": "error",
            "ollama": "error"
        }


def clear_documents():
    """Clear all documents from database"""
    try:
        response = requests.post(f"{API_URL}/api/clear-documents", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {
            "error": f"Failed with status {response.status_code}"
        }
    except Exception as e:
        return {
            "error": str(e)
        }