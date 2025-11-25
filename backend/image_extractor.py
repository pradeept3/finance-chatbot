import os
from typing import Optional
from google import genai

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

google_client = None
if GOOGLE_API_KEY:
    try:
        google_client = genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print("[Google Vision Init ERROR]", e)


def extract_text_from_image_with_gemini(image_path: str) -> Optional[str]:
    """
    Use Gemini to read text / content from an image (PNG/JPG).
    Returns plain text summary/reading suitable for Chroma.
    """
    if google_client is None:
        print("[Gemini Vision] No Google client – cannot read image.")
        return None

    try:
        ext = image_path.lower().split(".")[-1]
        mime = "image/png"
        if ext in ("jpg", "jpeg"):
            mime = "image/jpeg"

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        prompt = (
            "Read all visible text and key numerical/financial details from this image. "
            "Return ONLY plain text, no markdown, no lists. "
            "If there are tables, read them row by row as text."
        )

        resp = google_client.models.generate_content(
            model="GOOGLE_API_MODEL",
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": mime, "data": image_bytes}},
                    ],
                }
            ],
        )

        text = getattr(resp, "text", None)
        return text.strip() if text else None

    except Exception as e:
        print("[Gemini Vision ERROR]", e)
        return None
