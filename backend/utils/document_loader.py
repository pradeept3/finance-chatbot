import os
from typing import List, Any, Optional

from dotenv import load_dotenv
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from unstructured.documents.elements import Text
from google import genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL = os.getenv("GOOGLE_API_MODEL", "gemini-2.5-flash")

google_client: Optional[genai.Client] = None
if GOOGLE_API_KEY:
    try:
        google_client = genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"[Gemini Init ERROR] {e}")


def _extract_text_from_image_with_gemini(filepath: str) -> Optional[str]:
    """Use Gemini 2.5 Flash Vision to extract text."""
    if google_client is None:
        return None

    try:
        ext = os.path.splitext(filepath)[1].lower()
        mime_type = "image/png" if ext == ".png" else "image/jpeg"

        with open(filepath, "rb") as f:
            img_bytes = f.read()

        prompt = "Extract ALL readable text in plain text."

        resp = google_client.models.generate_content(
            model=GOOGLE_MODEL,
            contents=[{
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime_type, "data": img_bytes}}
                ]
            }]
        )

        return getattr(resp, "text", "").strip()

    except Exception as e:
        print(f"[Gemini Vision ERROR] {e}")
        return None


def load_documents(data_dir: str) -> List[Any]:
    """Loads PDFs, TXT, images, DOCX, XLSX using Unstructured + Gemini Vision."""
    raw_documents = []

    if not os.path.exists(data_dir):
        print(f"Directory missing: {data_dir}")
        return raw_documents

    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)
        ext = os.path.splitext(filename)[1].lower()

        print(f"Loading {filename}...")

        # Image? → Use Gemini Vision
        if ext in [".png", ".jpg", ".jpeg"]:
            text = _extract_text_from_image_with_gemini(filepath)
            if text:
                elem = Text(text=text)
                elem.metadata = {"source": filename, "file_name": filename}
                raw_documents.append(elem)
                print("  ✓ Loaded via Gemini Vision")
                continue

        # Normal text/pdf/docx → Unstructured
        try:
            elements = partition(filename=filepath)
            raw_documents.extend(elements)
            print(f"  ✓ Loaded {len(elements)} elements")
        except Exception as e:
            print("  ✗ Error:", e)

    return raw_documents


def chunk_documents(raw_documents: List[Any], max_chars=1000):
    chunks = []
    for doc in raw_documents:
        try:
            parts = chunk_by_title([doc], max_characters=max_chars)
            chunks.extend(parts)
        except Exception as e:
            print(f"Chunk error: {e}")
    return chunks
