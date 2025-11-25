import os
import re
from typing import Dict, Any, List, Optional

import requests

from bs4 import BeautifulSoup
from google import genai
from dotenv import load_dotenv


# -------------------------------------------------------------------
#  Configuration
# -------------------------------------------------------------------
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL = os.getenv("GOOGLE_API_MODEL", "gemini-2.5-flash")
OLLAMA_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

# Initialize Google client
google_client = None
if GOOGLE_API_KEY:
    try:
        from google import genai
        google_client = genai.Client(api_key=GOOGLE_API_KEY)
        print("[Response Generator] ✓ Google client initialized")
    except Exception as e:
        print(f"[Response Generator] ✗ Google Init ERROR: {e}")

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
            }
        )

    return passages


# -------------------------------------------------------------------
#  Helpers – URL content
# -------------------------------------------------------------------

def _fetch_url_snippet(url: str, max_chars: int = 3000) -> Optional[str]:
    """
    Fetch the URL and extract readable clean text using BeautifulSoup.
    Minimal change from your version — only parser improved.
    """
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code != 200:
            print(f"[URL FETCH] HTTP {resp.status_code} for {url}")
            return None

        html = resp.text or ""
        if not html:
            return None

        soup = BeautifulSoup(html, "lxml")

        # remove scripts/styles
        for tag in soup(["script", "style", "header", "footer", "nav"]):
            tag.extract()

        text = soup.get_text(separator=" ", strip=True)
        text = " ".join(text.split())  # compress whitespace

        if not text:
            return None

        return text[:max_chars]

    except Exception as e:
        print(f"[URL FETCH ERROR] {url}: {e}")
        return None


# -------------------------------------------------------------------
#  Prompt builder – STRICT RAG
# -------------------------------------------------------------------

def _build_prompt(
    user_query: str,
    passages: List[Dict[str, Any]],
    url_snippets: List[Dict[str, str]],
) -> str:
    """Build a strict RAG prompt"""
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
        "Rules (VERY IMPORTANT):\n"
        "1. Every factual statement in your answer MUST be supported by at least one passage ID "
        "   or URL label. Do **not** rely on outside knowledge.\n"
        "2. If the documents and URLs do not contain enough information, clearly say so.\n"
        "3. Be detailed and specific: quote or closely paraphrase the relevant text.\n"
        "4. Focus on finance, accounting, investments, and business topics when relevant.\n"
    )

    lines.append(f"\nUSER QUESTION:\n{user_query}\n")

    # Document passages
    if passages:
        lines.append("\n=== DOCUMENT PASSAGES (from uploaded files) ===\n")
        for p in passages[:12]:
            snippet = p.get("text", "").strip()
            if len(snippet) > 1200:
                snippet = snippet[:1200] + " ..."
            src = p.get("source", "Unknown")
            url = p.get("url") or "None"
            lines.append(
                f"[{p['id']}] (source file: {src}, url: {url})\n{snippet}\n"
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
        "model_used": "context-only",
    }


# -------------------------------------------------------------------
#  Main entry
# -------------------------------------------------------------------

def generate_detailed_response(user_query, retrieved_data):
    """Generate response using retrieved documents"""
    
    # 🔍 DEBUG: Check what we received
    print(f"\n{'='*60}")
    print(f"[Response Generator] Processing query: {user_query}")
    print(f"{'='*60}")
    
    passages = retrieved_data.get('passages', [])

    # Extract URL content from passages
    url_snippets = []
    seen_urls = set()

    for p in passages:
        url = p.get("url")
        if url and url not in seen_urls:
            snippet = _fetch_url_snippet(url)
            if snippet:
                url_snippets.append({"url": url, "text": snippet})
                seen_urls.add(url)

    print(f"[Response Generator] Received {len(passages)} passages")
    
    if passages:
        for i, p in enumerate(passages[:3], 1):
            print(f"   Passage {i}:")
            print(f"      Source: {p.get('source', 'Unknown')}")
            print(f"      Text: {p.get('text', '')[:100]}...")
    else:
        print("[Response Generator] ⚠️ NO PASSAGES RECEIVED!")
    
    # Build context from passages
    context_parts = []

    # Add document passages
    for passage in passages[:5]:
        source = passage.get('source', 'Unknown')
        text = passage.get('text', '')
        context_parts.append(f"[DOC] From {source}:\n{text}\n")

    # Add URL snippets
    for idx, item in enumerate(url_snippets, 1):
        context_parts.append(f"[URL{idx}] ({item['url']}):\n{item['text']}\n")

    
    context = "\n".join(context_parts)
    
    print(f"[Response Generator] Context length: {len(context)} chars")
    
    if not context or len(context) < 50:
        print("[Response Generator] ⚠️ Context too short or empty!")
        return {
            "main_response": "I don't have enough information to answer this question. Please make sure documents are uploaded.",
            "key_points": [],
            "passages": passages,
            "sections": [],
            "google_raw": "",
            "ollama_raw": "",
            "model_used": "none"
        }
    
    # Create prompt with context
    prompt = f"""Based on the following context from uploaded documents, answer the user's question.

CONTEXT FROM DOCUMENTS:
{context}

USER QUESTION: {user_query}

INSTRUCTIONS:
- Answer based ONLY on the context provided above
- If the context doesn't contain enough information, say so clearly
- Cite specific courses, requirements, or details from the context
- Be specific and detailed
- Use bullet points where appropriate

ANSWER:"""
    
    print(f"[Response Generator] Prompt ready ({len(prompt)} chars), sending to LLM...")
    
    # Call Google Gemini
    google_response = ""
    google_raw = ""
    
    if google_client:
        try:
            print("[Response Generator] Calling Google Gemini...")
            response = google_client.models.generate_content(
                model=GOOGLE_MODEL,
                contents=prompt
            )
            google_response = response.text if response else ""
            google_raw = google_response
            print(f"[Response Generator] ✓ Google response: {len(google_response)} chars")
        except Exception as e:
            print(f"[Response Generator] ✗ Google error: {e}")
            google_response = f"Error calling Google Gemini: {str(e)}"
    else:
        print("[Response Generator] ✗ Google client not available")
        google_response = "Google API not configured"
    
    # Call Ollama (optional)
    ollama_response = ""
    ollama_raw = ""
    
    try:
        print("[Response Generator] Calling Ollama...")
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3}
            },
            timeout=30
        )
        if r.status_code == 200:
            ollama_response = r.json().get("response", "")
            ollama_raw = ollama_response
            print(f"[Response Generator] ✓ Ollama response: {len(ollama_response)} chars")
        else:
            print(f"[Response Generator] ✗ Ollama error: {r.status_code}")
    except Exception as e:
        print(f"[Response Generator] ✗ Ollama error: {e}")
    
    # Use Google response as main response
    main_response = google_response or ollama_response or "No response generated"
    
    # Extract key points (simple implementation)
    key_points = []
    if main_response:
        sentences = [s.strip() for s in main_response.split('.') if s.strip()]
        key_points = [s + '.' for s in sentences[:3]]
    
    # Determine which model was used
    if google_response and ollama_response:
        model_used = "google+ollama"
    elif google_response:
        model_used = "google"
    elif ollama_response:
        model_used = "ollama"
    else:
        model_used = "none"
    
    print(f"[Response Generator] ✓ Complete! Model: {model_used}")
    print(f"{'='*60}\n")
    
    return {
        "main_response": main_response,
        "key_points": key_points,
        "sections": [],  # Can be populated if needed
        "google_raw": google_raw,
        "ollama_raw": ollama_raw,
        "model_used": model_used,
        "passages": passages,
        "url_summaries": url_snippets

    }


# Test function
if __name__ == "__main__":
    print("Testing response generator...")
    
    # Mock retrieved data
    test_data = {
        "passages": [
            {
                "source": "test_prereq.txt",
                "text": "Finance prerequisite: FNCE 101 Introduction to Finance is required before FNCE 201 Corporate Finance.",
                "distance": 0.2
            },
            {
                "source": "finance_courses.pdf",
                "text": "FNCE 121 Financial Management requires OMIS 40, ACTG 11, and proficiency with spreadsheets.",
                "distance": 0.3
            }
        ],
        "total": 2
    }
    
    # Test query
    result = generate_detailed_response("What are the finance prerequisites?", test_data)
    
    print("\n" + "="*60)
    print("TEST RESULT:")
    print("="*60)
    print(f"Model used: {result['model_used']}")
    print(f"Response: {result['main_response']}")
    print(f"Key points: {len(result['key_points'])}")
    print("="*60)