import os
import re
from typing import Dict, Any, List, Optional

import requests

from bs4 import BeautifulSoup
from google import genai
from dotenv import load_dotenv

# ✓ NEW: DeepSeek imports (replaces OpenAI)
try:
    from openai import OpenAI  # DeepSeek uses OpenAI client format
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False
    print("[Response Generator] ⚠️ DeepSeek library not installed. Run: pip install openai")


# -------------------------------------------------------------------
#  Configuration
# -------------------------------------------------------------------
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL = os.getenv("GOOGLE_API_MODEL", "gemini-2.5-flash")

# ✓ NEW: DeepSeek configuration (replaces OpenAI)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

OLLAMA_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", 120))

# Initialize Google client
google_client = None
if GOOGLE_API_KEY:
    try:
        from google import genai
        google_client = genai.Client(api_key=GOOGLE_API_KEY)
        print("[Response Generator] ✓ Google client initialized")
    except Exception as e:
        print(f"[Response Generator] ✗ Google Init ERROR: {e}")

# ✓ NEW: Initialize DeepSeek client (replaces OpenAI)
deepseek_client = None
if DEEPSEEK_API_KEY and DEEPSEEK_AVAILABLE:
    try:
        deepseek_client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
        print("[Response Generator] ✓ DeepSeek client initialized")
    except Exception as e:
        print(f"[Response Generator] ✗ DeepSeek Init ERROR: {e}")
elif DEEPSEEK_API_KEY and not DEEPSEEK_AVAILABLE:
    print("[Response Generator] ⚠️ DeepSeek API key set but library not installed")
else:
    print("[Response Generator] ⚠️ DeepSeek API key not configured")

# -------------------------------------------------------------------
#  Helpers – Chroma results → passages
# -------------------------------------------------------------------

def _flatten_chroma_field(field: Any) -> List[Any]:
    """
    Chroma .query() usually returns lists-of-lists (one list per query).
    We only ever issue a single query, so take the first inner list.
    """
    if not field:
        return []
    if not isinstance(field, list):
        return [field]
    if len(field) == 0:
        return []
    first = field[0]
    if isinstance(first, (list, tuple)):
        return list(first)
    return list(field)


def _prepare_passages(retrieved: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normalize ChromaDB result dict into a flat list of passage dicts.
    """
    docs_raw = retrieved.get("documents") or []
    metas_raw = retrieved.get("metadatas") or []
    dists_raw = retrieved.get("distances") or []

    docs = _flatten_chroma_field(docs_raw)
    metas = _flatten_chroma_field(metas_raw)
    dists = _flatten_chroma_field(dists_raw)

    passages: List[Dict[str, Any]] = []

    for idx, text in enumerate(docs):
        if isinstance(text, list):
            joined = " ".join(str(t) for t in text if t)
        else:
            joined = str(text) if text is not None else ""
        joined = joined.strip()
        if not joined:
            continue

        meta = metas[idx] if idx < len(metas) and isinstance(metas[idx], dict) else {}
        distance = None
        if idx < len(dists):
            try:
                distance = float(dists[idx])
            except Exception:
                distance = None

        source = str(meta.get("source", meta.get("file_name", "Unknown")))
        url = meta.get("url") or meta.get("source_url") or None

        # Auto-detect raw URLs inside text
        found_urls = re.findall(r'https?://\S+', joined)
        if found_urls and not url:
            url = found_urls[0]

        passages.append(
            {
                "id": f"P{idx + 1}",
                "text": joined,
                "source": source,
                "url": url,
                "distance": distance,
                "has_images": meta.get("has_images", False),
                "image_count": meta.get("image_count", 0),
            }
        )

    return passages


# -------------------------------------------------------------------
#  Helpers – URL content with BeautifulSoup
# -------------------------------------------------------------------

def _fetch_url_snippet(url: str, max_chars: int = 3000) -> Optional[str]:
    """
    Fetch the URL and extract readable clean text using BeautifulSoup.
    Enhanced version with better parsing and metadata extraction.
    
    ✓ VISION SUPPORT: Extracts text from pages containing images
    """
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"[URL FETCH] HTTP {resp.status_code} for {url}")
            return None

        html = resp.text or ""
        if not html:
            return None

        soup = BeautifulSoup(html, "lxml")

        # Remove scripts, styles, navigation, footers
        for tag in soup(["script", "style", "header", "footer", "nav", "noscript"]):
            tag.decompose()

        # Extract metadata
        meta_description = soup.find("meta", attrs={"name": "description"})
        description = ""
        if meta_description and meta_description.get("content"):
            description = meta_description.get("content", "").strip()

        # Get page title
        title = soup.title.string if soup.title else ""

        # Extract main content text
        text = soup.get_text(separator=" ", strip=True)
        text = " ".join(text.split())  # compress whitespace

        # Build comprehensive content
        content_parts = []
        
        if title:
            content_parts.append(f"[PAGE TITLE] {title}")
        
        if description:
            content_parts.append(f"[META DESCRIPTION] {description}")
        
        if text:
            content_parts.append(f"[PAGE CONTENT] {text}")

        full_content = "\n".join(content_parts)

        if not full_content:
            return None

        return full_content[:max_chars]

    except Exception as e:
        print(f"[URL FETCH ERROR] {url}: {e}")
        return None


# -------------------------------------------------------------------
#  Prompt builder – STRICT RAG with Vision Support
# -------------------------------------------------------------------

def _build_prompt(
    user_query: str,
    passages: List[Dict[str, Any]],
    url_snippets: List[Dict[str, str]],
) -> str:
    """
    Build a strict RAG prompt with vision support indicator.
    ✓ VISION SUPPORT ENABLED: Includes image analysis descriptions
    """
    if not passages and not url_snippets:
        return (
            "You are a finance-focused assistant.\n"
            "No supporting passages or URLs were retrieved from the knowledge base.\n\n"
            f"USER QUESTION:\n{user_query}\n\n"
            "Explain that the system has no indexed information relevant to this question "
            "and politely ask the user to upload documents or provide URLs."
        )

    lines: List[str] = []

    lines.append(
        "You are a **strict finance-focused RAG assistant**.\n"
        "You MUST answer the user's question using **only** the information found in:\n"
        "  • the uploaded document passages (labelled P1, P2, ...), and\n"
        "  • the URL page snippets (labelled URL1, URL2, ...).\n\n"
        "IMPORTANT - VISION SUPPORT ENABLED ✓:\n"
        "  • Some passages may include extracted image descriptions and OCR text\n"
        "  • These are marked with [IMAGE ANALYSIS] or [MULTIMODAL]\n"
        "  • Use this information as part of your answer\n\n"
        "Rules (VERY IMPORTANT):\n"
        "1. Every factual statement in your answer MUST be supported by at least one passage ID "
        "   or URL label. Do **not** rely on outside knowledge.\n"
        "2. If the documents and URLs do not contain enough information, clearly say so.\n"
        "3. Be detailed and specific: quote or closely paraphrase the relevant text.\n"
        "4. Focus on finance, accounting, investments, and business topics when relevant.\n"
    )

    lines.append(f"\nUSER QUESTION:\n{user_query}\n")

    # Document passages with vision indicators
    if passages:
        lines.append("\n=== DOCUMENT PASSAGES (from uploaded files) ===\n")
        for p in passages[:12]:
            snippet = p.get("text", "").strip()
            if len(snippet) > 1200:
                snippet = snippet[:1200] + " ..."
            src = p.get("source", "Unknown")
            url = p.get("url") or "None"
            
            # Vision indicator
            vision_indicator = ""
            if p.get("has_images"):
                vision_indicator = f" [📷 IMAGES: {p.get('image_count', '?')}]"
            
            lines.append(
                f"[{p['id']}] (source file: {src}, url: {url}){vision_indicator}\n{snippet}\n"
            )

    # URL snippets
    if url_snippets:
        lines.append("\n=== URL PAGE CONTENT (external pages) ===\n")
        for idx, item in enumerate(url_snippets, start=1):
            label = f"URL{idx}"
            url = item.get("url", "")
            snippet = item.get("text", "")
            if len(snippet) > 1500:
                snippet = snippet[:1500] + " ..."
            lines.append(f"[{label}] ({url})\n{snippet}\n")

    lines.append(
        "\nReturn your answer in **this exact markdown structure**:\n\n"
        "## ANSWER\n"
        "...a detailed answer grounded ONLY in the passages and URLs above...\n\n"
        "## KEY POINTS\n"
        "- point 1 (mention which passage IDs / URL labels you used)\n"
        "- point 2 (mention which passage IDs / URL labels you used)\n"
        "- point 3 (mention which passage IDs / URL labels you used)\n\n"
        "## CITED SOURCES\n"
        "- P1, URL1: very short snippet or description\n"
        "- P3: very short snippet or description\n"
    )

    return "\n".join(lines)


# -------------------------------------------------------------------
#  LLM callers
# -------------------------------------------------------------------

def _call_google(prompt: str) -> Optional[str]:
    """Call Gemini with the strict RAG prompt."""
    if google_client is None:
        print("[Google] Client not initialized")
        return None

    try:
        print("[Google] Calling Gemini...")
        resp = google_client.models.generate_content(
            model=GOOGLE_MODEL,
            contents=prompt,
        )
        text = getattr(resp, "text", "") or ""
        text = text.strip()
        if not text:
            print("[Google] Empty response")
            return None
        print(f"[Google] ✓ Response received ({len(text)} chars)")
        return text
    except Exception as e:
        print(f"[Google ERROR] {e}")
        return None


# ✓ NEW: DeepSeek caller (replaces OpenAI)
def _call_deepseek(prompt: str) -> Optional[str]:
    """Call DeepSeek Chat"""
    if deepseek_client is None:
        print("[DeepSeek] Client not initialized")
        return None

    try:
        print(f"[DeepSeek] Calling {DEEPSEEK_MODEL}...")
        response = deepseek_client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful finance expert assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        text = response.choices[0].message.content
        text = text.strip()
        if not text:
            print("[DeepSeek] Empty response")
            return None
        print(f"[DeepSeek] ✓ Response received ({len(text)} chars)")
        return text
    except Exception as e:
        print(f"[DeepSeek ERROR] {e}")
        return None


def _call_ollama(prompt: str) -> Optional[str]:
    """
    Call the local Ollama model with low temperature for less hallucination.
    Includes timeout handling and connection error detection.
    """
    try:
        print(f"[Ollama] Connecting to {OLLAMA_URL}...")
        
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
            },
        }
        
        print(f"[Ollama] Sending request (timeout={OLLAMA_TIMEOUT}s)...")
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        )
        
        if resp.status_code != 200:
            print(f"[Ollama ERROR] HTTP {resp.status_code}: {resp.text[:200]}")
            return None

        data = resp.json()
        text = data.get("response") or data.get("output") or ""
        text = text.strip()
        
        if not text:
            print("[Ollama] Empty response")
            return None
        
        print(f"[Ollama] ✓ Response received ({len(text)} chars)")
        return text
        
    except requests.exceptions.ConnectionError as e:
        print(f"[Ollama CONNECTION ERROR] Cannot reach {OLLAMA_URL}")
        print(f"  Make sure Ollama is running: ollama serve")
        print(f"  Error: {e}")
        return None
        
    except requests.exceptions.Timeout:
        print(f"[Ollama TIMEOUT] Request exceeded {OLLAMA_TIMEOUT}s timeout")
        print(f"  The model is taking too long to respond.")
        print(f"  Try increasing OLLAMA_TIMEOUT env var")
        return None
        
    except Exception as e:
        print(f"[Ollama ERROR] {e}")
        return None


# -------------------------------------------------------------------
#  Parsing helpers
# -------------------------------------------------------------------

def _extract_key_points_from_answer(answer_text: str) -> List[str]:
    """Look for a '## KEY POINTS' section and collect bullets."""
    lines = answer_text.splitlines()
    key_points: List[str] = []

    in_section = False
    for line in lines:
        stripped = line.strip()
        upper = stripped.upper()

        if upper.startswith("## KEY POINTS"):
            in_section = True
            continue

        if in_section and upper.startswith("## "):
            break

        if in_section and (stripped.startswith("- ") or stripped.startswith("* ")):
            point = stripped[2:].strip()
            if point:
                key_points.append(point)

    if not key_points:
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            key_points.append(stripped)
            if len(key_points) >= 5:
                break

    return key_points


def _build_sections_from_passages(passages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build a simple 'sections' list for the UI from the top passages."""
    sections: List[Dict[str, Any]] = []

    for idx, p in enumerate(passages[:5], start=1):
        distance = p.get("distance")
        relevance = "unknown"
        if isinstance(distance, (int, float)):
            if distance <= 0.6:
                relevance = "high"
            elif distance <= 1.0:
                relevance = "medium"
            else:
                relevance = "low"

        sections.append(
            {
                "title": f"Relevant Passage {idx}",
                "source_file": p.get("source", "Unknown"),
                "url": p.get("url"),
                "relevance": relevance,
                "content": p.get("text", ""),
                "has_images": p.get("has_images", False),
                "image_count": p.get("image_count", 0),
            }
        )

    return sections


def _context_only_fallback(
    user_query: str,
    passages: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Fallback when both LLMs fail: return deterministic context-only summary."""
    if not passages:
        main = (
            "I couldn't retrieve any relevant document chunks from the knowledge base "
            "for your question. Please upload more documents or try a more specific query."
        )
        key_points = [
            "No relevant document chunks were found.",
            "Try uploading additional files or using a more specific question.",
        ]
        sections = []
    else:
        header = (
            f"Based on the **{len(passages)} most similar document chunk(s)** I found "
            f"for your question:\n\n> **{user_query}**\n\n"
            "here are some extracted passages:\n\n"
        )

        body_lines: List[str] = []
        for idx, p in enumerate(passages[:3], start=1):
            text = (p.get("text") or "").replace("\n", " ").strip()
            snippet = text[:500] + ("..." if len(text) > 500 else "")
            src = p.get("source", "Unknown")
            body_lines.append(f"**{idx}. Source:** `{src}`\n\n{snippet}\n")

        main = header + "\n".join(body_lines)

        key_points: List[str] = []
        for p in passages[:5]:
            text = (p.get("text") or "").replace("\n", " ").strip()
            if not text:
                continue
            sent = text.split(".")[0].strip()
            if not sent:
                continue
            if len(sent) > 180:
                sent = sent[:180] + "..."
            key_points.append(sent)
            if len(key_points) >= 5:
                break

        if not key_points:
            key_points.append(
                "No clear key points could be extracted from the retrieved document chunks."
            )

    sections = _build_sections_from_passages(passages)
    return {
        "main_response": main,
        "key_points": key_points,
        "sections": sections,
        "ollama_raw": "",
        "google_raw": "",
        "deepseek_raw": "",  # ✓ NEW
        "model_used": "context-only",
    }


# -------------------------------------------------------------------
#  Main entry - UPDATED with model_mode parameter
# -------------------------------------------------------------------

def generate_detailed_response(user_query, retrieved_data, model_mode="Google only"):
    """
    Generate response using retrieved documents with FULL detail display
    ✅ Google is now the default model mode (changed from "Best (Google + Ollama)")
    
    Args:
        user_query: User's question
        retrieved_data: Retrieved documents from ChromaDB
        model_mode: Which model to use - defaults to "Google only" ✅ UPDATED
    
    Returns:
        dict: Response data with main response, key points, passages, etc.
    """
    
    print(f"\n{'='*70}")
    print(f"[Response Generator] Query: {user_query}")
    print(f"[Response Generator] Model Mode: {model_mode}")
    print(f"{'='*70}")
    
    passages = retrieved_data.get('passages', [])
    
    for idx, p in enumerate(passages):
        if 'id' not in p:
            p['id'] = f"P{idx + 1}"
        
        source = p.get('source', 'Unknown')
        text_len = len(p.get('text', ''))
        has_images = p.get('has_images', False)
        image_count = p.get('image_count', 0)
        
        print(f"   P{idx + 1}: {source} ({text_len} chars)")
        if has_images:
            print(f"          🖼️ {image_count} images")

    # Extract URL content from passages using BeautifulSoup
    url_snippets = []
    seen_urls = set()

    for p in passages:
        url = p.get("url")
        if url and url not in seen_urls:
            snippet = _fetch_url_snippet(url)
            if snippet:
                url_snippets.append({"url": url, "text": snippet})
                seen_urls.add(url)
                print(f"[Response Generator] ✅ URL content fetched: {url}")

    print(f"[Response Generator] URL snippets: {len(url_snippets)}\n")
    
    context_parts = []

    for idx, passage in enumerate(passages, 1):
        source = passage.get('source', 'Unknown')
        text = passage.get('text', '')
        passage_id = passage.get('id', f'P{idx}')
        
        metadata = passage.get('metadata', {})
        has_images = passage.get('has_images', False)
        image_count = passage.get('image_count', 0)
        doc_type = metadata.get('type', 'unknown')
        
        header = f"\n{'='*70}\n[{passage_id}] SOURCE: {source}\n"
        header += f"Type: {doc_type} | Content: {len(text)} chars\n"
        
        if has_images:
            header += f"🖼️ Images: {image_count} (with vision analysis)\n"
        
        if metadata:
            header += f"Metadata: {metadata}\n"
        
        header += f"{'='*70}\n"
        
        context_parts.append(header + text)

    for idx, item in enumerate(url_snippets, 1):
        context_parts.append(f"\n{'='*70}\n[URL{idx}] ({item['url']})\n{'='*70}\n{item['text']}")

    context = "\n".join(context_parts)
    
    print(f"[Response Generator] Total context: {len(context)} chars")
    
    if not context or len(context) < 50:
        print("[Response Generator] ⚠️ Context too short!")
        return {
            "main_response": "I don't have enough information to answer this question.",
            "key_points": [],
            "passages": passages,
            "sections": [],
            "google_raw": "",
            "ollama_raw": "",
            "deepseek_raw": "",
            "model_used": "none",
            "selected_model": model_mode,
            "retrieved_count": len(passages)
        }
    
    prompt = f"""You are a finance expert assistant with access to comprehensive documents.

IMPORTANT INSTRUCTIONS:
1. Use ALL the information provided below
2. Extract MAXIMUM detail from the documents
3. Reference specific passages (P1, P2, etc.) in your answer
4. Include all relevant data, numbers, and details
5. Be comprehensive and thorough

FULL DOCUMENT CONTENT:
{context}

USER QUESTION: {user_query}

REQUIREMENTS:
- Answer based ONLY on the provided documents
- Be detailed and specific with all information
- Include all data points, numbers, and important details
- If insufficient information, clearly state that

ANSWER FORMAT:
## MAIN ANSWER
[Comprehensive answer with all details]

## KEY DETAILS
- Detail 1
- Detail 2
- Detail 3

## SOURCES USED
[List which passages were used]
"""
    
    print(f"[Response Generator] Prompt ready ({len(prompt)} chars)")
    print(f"[Response Generator] Model mode: {model_mode}\n")
    
    google_response = ""
    ollama_response = ""
    deepseek_response = ""
    
    # ✅ UPDATED: Model selection logic with Google as default
    if model_mode == "Google only":
        print("[Response Generator] 🔵 Using Google only (DEFAULT)")
        google_response = _call_google(prompt)
    
    elif model_mode == "Ollama only":
        print("[Response Generator] 🟢 Using Ollama only")
        ollama_response = _call_ollama(prompt)
    
    elif model_mode == "DeepSeek":
        print("[Response Generator] 🔷 Using DeepSeek")
        deepseek_response = _call_deepseek(prompt)
    
    elif model_mode == "Context-only":
        print("[Response Generator] ⚪ Using Context-only")
        return _context_only_fallback(user_query, passages)
    
    else:  # Best (Google + Ollama)
        print("[Response Generator] 🟣 Using Best (Google + Ollama)")
        google_response = _call_google(prompt)
        ollama_response = _call_ollama(prompt)
    
    # Choose response with priority
    main_response = (
        deepseek_response
        or google_response
        or ollama_response
        or "No response generated"
    )
    
    key_points = []
    if main_response and "## KEY DETAILS" in main_response:
        lines = main_response.split("## KEY DETAILS")[1].split("##")[0].split("\n")
        key_points = [line.strip() for line in lines if line.strip().startswith("-")]
    else:
        sentences = [s.strip() for s in main_response.split('.') if s.strip() and len(s.strip()) > 20]
        key_points = sentences[:5]
    
    # Detect which model was actually used
    if model_mode == "DeepSeek":
        model_used = "deepseek"
    elif model_mode == "Google only":
        model_used = "google"
    elif model_mode == "Ollama only":
        model_used = "ollama"
    elif model_mode == "Context-only":
        model_used = "context-only"
    else:  # Best
        if deepseek_response:
            model_used = "deepseek"
        elif google_response and ollama_response:
            model_used = "google+ollama"
        elif google_response:
            model_used = "google"
        elif ollama_response:
            model_used = "ollama"
        else:
            model_used = "none"
    
    print(f"[Response Generator] ✅ Complete!")
    print(f"[Response Generator] Model used: {model_used}")
    print(f"{'='*70}\n")
    
    return {
        "main_response": main_response,
        "key_points": key_points,
        "sections": _build_sections_from_passages(passages),
        "google_raw": google_response,
        "ollama_raw": ollama_response,
        "deepseek_raw": deepseek_response,
        "model_used": model_used,
        "selected_model": model_mode,
        "passages": passages,
        "url_summaries": url_snippets,
        "full_context": context,
        "retrieved_count": len(passages),
        "total_context_chars": len(context)
    }
