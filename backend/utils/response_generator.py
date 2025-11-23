import os
from typing import Dict, Any, List, Optional

import requests
from bs4 import BeautifulSoup
from google import genai

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL = os.getenv("GOOGLE_API_MODEL", "gemini-2.5-flash")
OLLAMA_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

google_client: Optional[genai.Client] = None
if GOOGLE_API_KEY:
    try:
        google_client = genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"[Google Init ERROR] {e}")


# -------------------------------------------------------------------
# URL fetching helper – used to let LLM see page contents
# -------------------------------------------------------------------
def _fetch_url_text(url: str, max_chars: int = 2000) -> Optional[str]:
    """
    Fetch a URL and return a cleaned text snippet.

    - Uses requests with a short timeout so backend doesn't hang.
    - Uses BeautifulSoup to strip scripts/styles.
    - Truncates to max_chars to keep prompts small.
    """
    try:
        if not url.lower().startswith(("http://", "https://")):
            return None

        resp = requests.get(url, timeout=6)
        if resp.status_code != 200:
            print(f"[URL FETCH] HTTP {resp.status_code} for {url}")
            return None

        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            # Non-HTML (e.g., PDF) – skip for now
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # remove scripts / styles / noscript
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [ln.strip() for ln in text.splitlines()]
        text = "\n".join(ln for ln in lines if ln)

        if not text:
            return None

        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        return text

    except Exception as e:
        print(f"[URL FETCH ERROR] {url} -> {e}")
        return None


# -------------------------------------------------------------------
# Passages from ChromaDB
# -------------------------------------------------------------------
def _prepare_passages(retrieved: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normalize ChromaDB result dict into a flat list of passage dicts.

    Each passage has:
      - id:         "P1", "P2", ...
      - text:       chunk text (+ optional URL snippet)
      - source:     filename or 'source' metadata
      - url:        optional URL from metadata
      - url_snippet: optional text snippet fetched from URL
      - distance:   similarity distance (float or None)
    """
    docs = retrieved.get("documents") or []
    metas = retrieved.get("metadatas") or []
    dists = retrieved.get("distances") or []

    passages: List[Dict[str, Any]] = []

    for idx, text in enumerate(docs):
        base_text = str(text) if text is not None else ""
        meta = metas[idx] if idx < len(metas) and isinstance(metas[idx], dict) else {}

        distance: Optional[float] = None
        if idx < len(dists):
            try:
                distance = float(dists[idx])
            except Exception:
                distance = None

        source = str(meta.get("source", meta.get("file_name", "Unknown")))
        url = meta.get("url") or None

        # NEW: fetch URL content (if present) and append as labelled snippet
        url_snippet: Optional[str] = None
        if url:
            url_snippet = _fetch_url_text(url)
            if url_snippet:
                base_text += (
                    f"\n\n[URL CONTENT SNIPPET from {url}]\n"
                    f"{url_snippet}"
                )

        passages.append(
            {
                "id": f"P{idx + 1}",
                "text": base_text,
                "source": source,
                "url": url,
                "url_snippet": url_snippet,
                "distance": distance,
            }
        )

    return passages


def _build_prompt(user_query: str, passages: List[Dict[str, Any]]) -> str:
    """
    Build the RAG prompt that instructs the LLM to answer ONLY from the retrieved passages.
    """
    if not passages:
        return (
            "You are a helpful **finance-focused** assistant.\n"
            "No supporting passages were retrieved from the knowledge base.\n\n"
            f"USER QUESTION:\n{user_query}\n\n"
            "If you cannot answer from your general knowledge for compliance reasons, say so briefly."
        )

    lines: List[str] = []

    lines.append(
        "You are a helpful **finance-focused** assistant.\n"
        "You MUST answer the user's question using **only** the information in the provided passages.\n"
        "Passages may include snippets of content fetched from external URLs.\n"
        "If the passages do not contain enough information, say so explicitly.\n\n"
        "Tasks:\n"
        "1. Read the user's question.\n"
        "2. Carefully read each passage.\n"
        "3. Synthesize a clear answer based ONLY on those passages.\n"
        "4. Provide a short bullet list of key points.\n"
        "5. List which passage IDs you used.\n"
    )

    lines.append(f"\nUSER QUESTION:\n{user_query}\n")
    lines.append("PASSAGES:\n")

    for p in passages[:10]:  # keep prompt manageable
        snippet = (p.get("text") or "").strip()
        if len(snippet) > 1000:
            snippet = snippet[:1000] + " ..."
        src = p.get("source", "Unknown")
        url = p.get("url") or "None"
        lines.append(f"[{p['id']}] (source: {src}, url: {url})\n{snippet}\n")

    lines.append(
        "\nReturn your answer in **this exact markdown structure**:\n\n"
        "## ANSWER\n"
        "...your main answer...\n\n"
        "## KEY POINTS\n"
        "- point 1\n"
        "- point 2\n"
        "- point 3\n\n"
        "## CITED PASSAGES\n"
        "- P1: short snippet\n"
        "- P3: short snippet\n"
    )

    return "\n".join(lines)


def _call_google(prompt: str) -> Optional[str]:
    """
    Call Gemini (via google.genai Client) with the given prompt.
    Returns the response text, or None on failure / missing API key.
    """
    if google_client is None:
        return None

    try:
        resp = google_client.models.generate_content(
            model=GOOGLE_MODEL,
            contents=prompt,
        )
        text = getattr(resp, "text", "") or ""
        return text.strip() or None
    except Exception as e:
        print("[Google ERROR]", e)
        return None


def _call_ollama(prompt: str) -> Optional[str]:
    """
    Call a local Ollama model with the same RAG prompt.
    """
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=40,
        )
        if r.status_code != 200:
            print("[Ollama ERROR]", r.status_code, r.text)
            return None

        data = r.json()
        text = data.get("response") or data.get("output") or ""
        return text.strip() or None
    except Exception as e:
        print("[Ollama ERROR]", e)
        return None


def _extract_key_points_from_answer(answer_text: str) -> List[str]:
    """
    Try to find the '## KEY POINTS' section and gather bullets.
    Fallback: first 3–5 non-empty lines.
    """
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
        # next section heading
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


def _summarize_url_page(url: str) -> Optional[Dict[str, str]]:
    """
    Fetch and summarize a web page linked in the document metadata.
    Uses Gemini if available; otherwise returns None.
    """
    if google_client is None:
        return None

    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code != 200:
            print(f"[URL SUMMARY] HTTP {resp.status_code} for {url}")
            return None

        raw_html = resp.text
        if not raw_html:
            return None

        # Keep content limited to avoid huge prompts
        snippet = raw_html[:8000]

        prompt = (
            "You are summarizing a web page referenced by a finance chatbot.\n"
            "Given the following HTML/text content, provide:\n"
            "1. A short one-line title.\n"
            "2. 3–5 bullet points summarizing key information that would be useful in a finance/document Q&A context.\n\n"
            "Return markdown in this structure:\n\n"
            "### Title\n"
            "<one line>\n\n"
            "### Summary\n"
            "- point 1\n"
            "- point 2\n"
            "- point 3\n\n"
            "### Notes\n"
            "- Optional notes if needed.\n\n"
            "-----\n"
            "PAGE CONTENT:\n"
            f"{snippet}\n"
        )

        resp2 = google_client.models.generate_content(
            model=GOOGLE_MODEL,
            contents=prompt,
        )
        summary_text = getattr(resp2, "text", "") or ""
        summary_text = summary_text.strip()
        if not summary_text:
            return None

        return {
            "url": url,
            "summary_markdown": summary_text,
        }

    except Exception as e:
        print(f"[URL SUMMARY ERROR] for {url}: {e}")
        return None


def _build_sections_from_passages(passages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build 'sections' for the frontend from the top N passages.
    """
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


def generate_detailed_response(user_query: str, retrieved: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry used by app.py:

    - Takes the raw ChromaDB 'retrieved' dict.
    - Builds a prompt including top passages (with optional URL snippets).
    - Calls Gemini and/or Ollama.
    - Returns a dict ready for the frontend.
    """
    passages = _prepare_passages(retrieved)
    prompt = _build_prompt(user_query, passages)

    google_raw = _call_google(prompt)
    ollama_raw = _call_ollama(prompt)

    main_response: str
    model_used = "none"

    if google_raw and ollama_raw:
        # prefer Google for main answer, but keep Ollama raw available
        main_response = google_raw
        model_used = "google+ollama"
    elif google_raw:
        main_response = google_raw
        model_used = "google"
    elif ollama_raw:
        main_response = ollama_raw
        model_used = "ollama"
    else:
        main_response = (
            "No language model (Gemini or Ollama) returned a response.\n"
            "Please check your AI configuration (API keys, Ollama service, etc.)."
        )
        model_used = "none"

    key_points = _extract_key_points_from_answer(main_response)
    sections = _build_sections_from_passages(passages)

    # Summarize any URLs that appear in the passages (at most 5 unique URLs)
    url_summaries: List[Dict[str, str]] = []
    seen_urls = set()
    for p in passages:
        url = p.get("url")
        if not url or url in seen_urls:
            continue
        summary = _summarize_url_page(url)
        if summary:
            url_summaries.append(summary)
            seen_urls.add(url)
        if len(url_summaries) >= 5:
            break

    return {
        "main_response": main_response,
        "key_points": key_points,
        "sections": sections,
        "ollama_raw": ollama_raw or "",
        "google_raw": google_raw or "",
        "model_used": model_used,
        "passages": passages,
        "url_summaries": url_summaries,
    }
