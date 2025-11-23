import os
import requests
from google import genai
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL = os.getenv("GOOGLE_API_MODEL", "gemini-2.5-flash")
OLLAMA_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

google_client = None
if GOOGLE_API_KEY:
    try:
        google_client = genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print("[Google Init ERROR]", e)


class FileAnalyzer:

    @staticmethod
    def analyze_with_google(file_path, file_content):

        if google_client is None:
            return {"source": "google", "status": "error", "error": "Google not initialized"}

        try:
            prompt = f"""
Analyze this document and return:

1. Summary (3–5 sentences)
2. Key Topics (5–7 bullet points)
3. Document Type (finance, legal, HR, invoice, etc.)
4. Confidence (High/Medium/Low)
5. Keywords (10)

Document name: {os.path.basename(file_path)}
Content preview:
{file_content[:2000]}
"""

            response = google_client.models.generate_content(
                model=GOOGLE_MODEL,
                contents=prompt
            )

            return {
                "source": "google",
                "analysis": response.text,
                "status": "success"
            }

        except Exception as e:
            return {"source": "google", "status": "error", "error": str(e)}

    @staticmethod
    def analyze_with_ollama(file_path, file_content):
        try:
            prompt = f"""
Analyze this document and provide summary, topics, type, confidence, keywords.

Document name: {os.path.basename(file_path)}
Content:
{file_content[:2000]}
"""

            r = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                timeout=60
            )

            if r.status_code == 200:
                return {
                    "source": "ollama",
                    "model": OLLAMA_MODEL,
                    "analysis": r.json().get("response"),
                    "status": "success"
                }

            return {"source": "ollama", "status": "error", "error": f"HTTP {r.status_code}"}

        except Exception as e:
            return {"source": "ollama", "status": "error", "error": str(e)}
