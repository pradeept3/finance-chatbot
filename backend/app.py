from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
from dotenv import load_dotenv

from chromadb_setup import (
    initialize_chromadb,
    query_documents,
    add_documents_to_chromadb,
)

from PIL import Image
import google.generativeai as genai

from utils.response_generator import generate_detailed_response
from utils.document_loader import load_documents, chunk_documents
from utils.file_analyzer import FileAnalyzer
from utils.url_scraper import scrape_url, is_valid_url
from next_steps_graph import run_next_steps_graph
from werkzeug.utils import secure_filename

# ✓ Comprehensive document processor
from utils.comprehensive_document_processor import create_comprehensive_document

# ✅ NEW: Add these imports for URL fetching
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

import requests
from werkzeug.serving import WSGIRequestHandler
WSGIRequestHandler.timeout = 120

load_dotenv()


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

UPLOAD_FOLDER = os.getenv("UPLOAD_DIR", "./uploaded_documents")
MAX_FILE_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 50)) * 1024 * 1024

ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx", "txt", "png", "jpg", "jpeg"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    print("✓ Google Gemini configured for image analysis")

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# -----------------------------------------------------------------------------
# Initialize ChromaDB
# -----------------------------------------------------------------------------
try:
    collection = initialize_chromadb()
    print("✓ ChromaDB initialized successfully")
except Exception as e:
    print(f"✗ Error initializing ChromaDB: {e}")
    collection = None


# -----------------------------------------------------------------------------
# ✅ NEW: URL Fetching Functions
# -----------------------------------------------------------------------------
def extract_text_from_url(url: str) -> dict:
    """Extract text content from a URL"""
    try:
        print(f"[URL Fetch] Fetching: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        title = soup.title.string if soup.title else url
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit text length
        text = text[:8000]  # Increased to 8000 chars for better context
        
        print(f"[URL Fetch] ✓ Fetched {len(text)} chars from {url}")
        
        return {
            "text": text,
            "title": title,
            "url": url,
            "error": None
        }
        
    except Exception as e:
        print(f"[URL Fetch] ✗ Error fetching {url}: {e}")
        return {
            "text": "",
            "title": url,
            "url": url,
            "error": str(e)
        }


def detect_and_fetch_urls(query: str) -> list:
    """Detect URLs in query and fetch their content"""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, query)
    
    if not urls:
        return []
    
    print(f"[URL Detection] Found {len(urls)} URLs in query")
    
    results = []
    for url in urls:
        result = extract_text_from_url(url)
        if result["text"]:
            results.append(result)
    
    return results


# -----------------------------------------------------------------------------
# Image processing
# -----------------------------------------------------------------------------
def is_image_file(filename):
    """Check if file is an image"""
    image_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in image_extensions


def process_image_with_gemini(image_path):
    """Process image using Google Gemini Vision API with detailed analysis"""
    try:
        img = Image.open(image_path)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompts = [
            "Extract ALL visible text from this image exactly as shown. Include labels, numbers, headers, and any written content.",
            "Describe this image in detail: What objects, data, charts, or information does it contain? What is the main purpose?",
            "If this image contains numbers, data, or metrics, extract and list them all. Include any financial, statistical, or quantitative information."
        ]
        
        descriptions = []
        for prompt in prompts:
            response = model.generate_content([prompt, img])
            if response and response.text:
                descriptions.append(response.text)
        
        return "\n\n".join(descriptions)
    except Exception as e:
        print(f"[Image Processing Error] {e}")
        return f"Error processing image: {str(e)}"


# -----------------------------------------------------------------------------
# Health check / status
# -----------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "Finance Chatbot Backend is running",
        "timestamp": datetime.now().isoformat(),
    }), 200


@app.route("/api/status", methods=["GET"])
def get_status():
    try:
        status = {
            "backend": "running",
            "chromadb": "connected" if collection else "disconnected",
            "documents": collection.count() if collection else 0,
            "timestamp": datetime.now().isoformat(),
        }
        return jsonify(status), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------------------------
# ✅ UPDATED: Chat endpoint with URL fetching
# -----------------------------------------------------------------------------
# Updated Chat endpoint with proper error handling
@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        
        user_query = data.get("message", "") or data.get("query", "")
        user_query = user_query.strip()
        
        model_mode = data.get("model_mode", "Best (Google + Ollama)")
        context_passages = data.get("context_passages")  # NEW: Get context passages
        
        print(f"\n{'='*70}")
        print(f"[Chat] Received query: {user_query}")
        print(f"[Chat] Model mode: {model_mode}")
        print(f"[Chat] Context passages: {len(context_passages) if context_passages else 0}")
        print(f"{'='*70}")

        if not user_query:
            return jsonify({
                "error": "Message required",
                "response": "Please provide a message.",
            }), 400

        if not collection:
            return jsonify({
                "error": "DB error",
                "response": "System error: Database not initialized.",
            }), 500

        # Check for URLs in the query and fetch them
        url_contents = detect_and_fetch_urls(user_query)
        
        if url_contents:
            print(f"[Chat] Fetched content from {len(url_contents)} URLs")
            
            url_context = "\n\n=== CONTENT FROM PROVIDED URLs ===\n\n"
            for idx, url_data in enumerate(url_contents, 1):
                url_context += f"[Source {idx}] {url_data['title']}\n"
                url_context += f"URL: {url_data['url']}\n"
                url_context += f"Content: {url_data['text']}\n\n"
            
            enhanced_query = f"{url_context}\n\nUser Question: {user_query}"
        else:
            enhanced_query = user_query
            url_context = ""

        # ============================================================
        # CONDITIONAL SEARCH LOGIC (NEW)
        # ============================================================
        print("[Chat] Determining search strategy...")
        
        if context_passages and len(context_passages) > 0:
            # CONSTRAINED SEARCH: Search only within provided passages
            print(f"[Chat] ✅ Using CONSTRAINED search ({len(context_passages)} passages)")
            retrieved_data = {"passages": context_passages}
            is_constrained = True
        else:
            # FULL SEARCH: Search all documents
            print("[Chat] ✅ Using FULL search (all documents)")
            retrieved_data = query_documents(collection, user_query, n_results=5)
            is_constrained = False
        
        # Check if we got results
        passages = retrieved_data.get("passages", [])
        if not passages:
            print("[Chat] No relevant passages found")
            return jsonify({
                "response": "No relevant information found. Try rephrasing your question.",
                "key_points": [],
                "passages": [],
                "model_used": "none",
                "selected_model": model_mode,
                "url_summaries": url_contents,
                "is_constrained": is_constrained,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
            }), 200
        
        print(f"[Chat] Retrieved {len(passages)} passages")

        # Generate response with passages
        print("[Chat] Generating response...")
        response_data = generate_detailed_response(
            user_query=enhanced_query,
            retrieved_data=retrieved_data,
            model_mode=model_mode
        )
        
        # Ensure passages are in response_data
        if "passages" not in response_data:
            response_data["passages"] = passages
        
        print(f"[Chat] Response generated ({len(response_data.get('main_response', ''))} chars)")
        print(f"[Chat] Model used: {response_data.get('model_used', 'unknown')}")
        print(f"{'='*70}\n")

        return jsonify({
            "response": response_data.get("main_response", ""),
            "key_points": response_data.get("key_points", []),
            "sections": response_data.get("sections", []),
            "google_raw": response_data.get("google_raw", ""),
            "ollama_raw": response_data.get("ollama_raw", ""),
            "openai_raw": response_data.get("openai_raw", ""),
            "model_used": response_data.get("model_used", "unknown"),
            "selected_model": response_data.get("selected_model", model_mode),
            "passages": response_data.get("passages", passages),
            "url_summaries": url_contents,
            "is_constrained": is_constrained,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
        }), 200

    except Exception as e:
        print(f"\n[Chat ERROR] {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*70}\n")
        
        return jsonify({
            "error": str(e), 
            "response": "An error occurred while processing your request.",
            "status": "error",
            "passages": [],
            "key_points": []
        }), 500


# -----------------------------------------------------------------------------
# Upload & index files into ChromaDB
# -----------------------------------------------------------------------------
@app.route("/api/upload", methods=["POST"])
def upload_documents():
    """Upload and process documents with comprehensive detail extraction"""
    try:
        files = request.files.getlist("files") if "files" in request.files else []
        urls = request.form.getlist("urls") if "urls" in request.form else []
        
        if not files and not urls:
            return jsonify({
                "error": "No files or URLs provided",
                "message": "Please upload files or provide URLs",
            }), 400

        uploaded_files = []
        errors = []
        image_count = 0
        url_count = 0
        vision_enabled_pdfs = 0
        total_documents_added = 0

        print(f"\n{'='*70}")
        print(f"[UPLOAD] Starting document processing...")
        print(f"{'='*70}\n")

        # Process files
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                
                print(f"\n[UPLOAD] 📄 Processing: {filename}")
                
                ext = filename.rsplit('.', 1)[1].lower()
                
                try:
                    print(f"[UPLOAD] 🔍 Calling comprehensive_document_processor...")
                    result = create_comprehensive_document(filepath, ext)
                    
                    if result["success"] and result["content"]:
                        from langchain_core.documents import Document
                        
                        doc = Document(
                            page_content=result["content"],
                            metadata=result["metadata"]
                        )
                        
                        docs_added = add_documents_to_chromadb(collection, [doc])
                        total_documents_added += docs_added
                        
                        if ext in ['jpg', 'jpeg', 'png']:
                            image_count += 1
                        elif ext == 'pdf' and result["metadata"].get("has_images"):
                            vision_enabled_pdfs += 1
                            image_count += result["metadata"].get("image_count", 0)
                        
                        uploaded_files.append({
                            "filename": filename,
                            "size": os.path.getsize(filepath),
                            "type": ext,
                            "content_length": len(result["content"]),
                            "metadata": result["metadata"]
                        })
                        
                        print(f"[UPLOAD] ✓✓✓ {filename} SUCCESS")
                    else:
                        errors.append(f"{filename} - Processing failed")
                        print(f"[UPLOAD] ✗ Processing failed")
                        
                except Exception as e:
                    errors.append(f"{filename} - {str(e)}")
                    print(f"[UPLOAD] ✗✗✗ ERROR: {e}")
            elif file:
                errors.append(f"{file.filename} - Invalid file type")

        # Process URLs
        for url in urls:
            if is_valid_url(url):
                print(f"\n[UPLOAD] 🌐 Processing URL: {url}")
                
                try:
                    result = scrape_url(url)
                    
                    if result["status"] == "success":
                        from langchain_core.documents import Document
                        
                        url_doc = Document(
                            page_content=f"Title: {result['title']}\n\nContent:\n{result['content']}",
                            metadata={
                                "source": url,
                                "type": "url",
                                "title": result["title"],
                                "length": len(result["content"])
                            }
                        )
                        
                        docs_added = add_documents_to_chromadb(collection, [url_doc])
                        url_count += 1
                        total_documents_added += docs_added
                        print(f"[UPLOAD] ✓ URL processed")
                    else:
                        errors.append(f"{url} - Failed to scrape")
                        
                except Exception as e:
                    errors.append(f"{url} - {str(e)}")
            else:
                errors.append(f"{url} - Invalid URL")

        print(f"\n{'='*70}")
        print(f"[UPLOAD] SUMMARY: {len(uploaded_files)} files, {url_count} URLs, {total_documents_added} docs")
        print(f"{'='*70}\n")

        if uploaded_files or url_count > 0:
            return jsonify({
                "status": "success",
                "message": f"Successfully processed {len(uploaded_files)} file(s) and {url_count} URL(s)",
                "files_uploaded": [f["filename"] for f in uploaded_files],
                "files_detail": uploaded_files,
                "documents_added": total_documents_added,
                "images_processed": image_count,
                "urls_processed": url_count,
                "vision_enabled_pdfs": vision_enabled_pdfs,
                "errors": errors,
                "timestamp": datetime.now().isoformat(),
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "No valid files or URLs processed",
                "errors": errors,
            }), 400

    except Exception as e:
        print(f"\n[UPLOAD] ✗✗✗ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "error": str(e),
            "message": "Error uploading documents",
            "status": "error"
        }), 500


# -----------------------------------------------------------------------------
# Document count
# -----------------------------------------------------------------------------
@app.route("/api/documents", methods=["GET"])
def get_documents_count():
    try:
        if not collection:
            return jsonify({"error": "ChromaDB not initialized"}), 500

        return jsonify({
            "total_documents": collection.count(),
            "status": "success",
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------------------------
# File analysis
# -----------------------------------------------------------------------------
@app.route("/api/analyze-file", methods=["POST"])
def analyze_file():
    """Analyze uploaded file"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        if not file or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        metadata = FileAnalyzer.extract_file_metadata(filepath, filename)
        
        if is_image_file(filename):
            preview = "Image file - detailed visual analysis below"
            google_analysis = FileAnalyzer.analyze_image_with_google(filepath)
            ollama_analysis = {
                "status": "error",
                "error": "Ollama does not support image analysis"
            }
        else:
            preview = FileAnalyzer.get_file_preview(filepath)
            google_analysis = FileAnalyzer.analyze_with_google(filepath, preview)
            ollama_analysis = FileAnalyzer.analyze_with_ollama(filepath, preview)

        return jsonify({
            "status": "success",
            "file": metadata,
            "preview": preview,
            "analysis": {
                "google": google_analysis,
                "ollama": ollama_analysis,
            },
            "timestamp": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        print(f"Error analyzing file: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/api/batch-analyze", methods=["POST"])
def batch_analyze():
    """Analyze multiple files"""
    try:
        if "files" not in request.files:
            return jsonify({"error": "No files provided"}), 400

        files = request.files.getlist("files")
        results = []

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)

                metadata = FileAnalyzer.extract_file_metadata(filepath, filename)
                
                if is_image_file(filename):
                    preview = "Image file"
                    google_analysis = FileAnalyzer.analyze_image_with_google(filepath)
                    ollama_analysis = {"status": "error", "error": "Not supported"}
                else:
                    preview = FileAnalyzer.get_file_preview(filepath)
                    google_analysis = FileAnalyzer.analyze_with_google(filepath, preview)
                    ollama_analysis = FileAnalyzer.analyze_with_ollama(filepath, preview)

                results.append({
                    "file": metadata,
                    "preview": preview[:300],
                    "analysis": {
                        "google": google_analysis,
                        "ollama": ollama_analysis,
                    },
                })

        return jsonify({
            "status": "success",
            "files_analyzed": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        print(f"Error in batch analysis: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500


# -----------------------------------------------------------------------------
# AI services status
# -----------------------------------------------------------------------------
@app.route("/api/ai-status", methods=["GET"])
def ai_status():
    try:
        google_status = "configured" if GOOGLE_API_KEY else "not_configured"

        ollama_status = "disconnected"
        try:
            resp = requests.get(f"{OLLAMA_API_URL}/api/tags", timeout=5)
            if resp.status_code == 200:
                ollama_status = "connected"
        except Exception:
            pass

        return jsonify({
            "status": "success",
            "google_api": google_status,
            "ollama": ollama_status,
            "timestamp": datetime.now().isoformat(),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------------------------
# Next steps endpoint
# -----------------------------------------------------------------------------
@app.route("/api/next-steps", methods=["POST"])
def api_next_steps():
    try:
        data = request.get_json(force=True) or {}

        user_question = (data.get("user_question") or "").strip()
        answer_text = (data.get("answer_text") or "").strip()
        key_points = data.get("key_points") or []

        if not user_question or not answer_text:
            return jsonify({
                "error": "user_question and answer_text are required",
                "suggestions": [],
            }), 400

        result = run_next_steps_graph(
            user_question=user_question,
            answer_text=answer_text,
            key_points=key_points,
        )

        return jsonify(result), 200

    except Exception as e:
        print("[/api/next-steps ERROR]", e)
        return jsonify({"error": str(e), "suggestions": []}), 500


# -----------------------------------------------------------------------------
# Debug endpoints
# -----------------------------------------------------------------------------
@app.route("/api/debug-documents", methods=["GET"])
def debug_documents():
    """Debug endpoint - shows all documents"""
    try:
        if not collection:
            return jsonify({"error": "ChromaDB not initialized"}), 500

        total_count = collection.count()
        
        if total_count == 0:
            return jsonify({
                "status": "empty",
                "total_documents": 0,
                "message": "ChromaDB is empty"
            }), 200
        
        results = collection.get(limit=100)
        
        documents = []
        if results and 'documents' in results:
            for idx, (doc_id, doc_text, metadata) in enumerate(zip(
                results.get('ids', []),
                results.get('documents', []),
                results.get('metadatas', [])
            ), 1):
                documents.append({
                    "index": idx,
                    "id": doc_id,
                    "content_length": len(doc_text),
                    "content_preview": doc_text[:200] + "...",
                    "metadata": metadata,
                })
        
        return jsonify({
            "status": "success",
            "total_documents": total_count,
            "sample_count": len(documents),
            "documents": documents,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/api/search-debug", methods=["POST"])
def search_debug():
    """Debug search"""
    try:
        data = request.json or {}
        query = data.get("query", "")
        
        if not query:
            return jsonify({"error": "Query required"}), 400
        
        if not collection:
            return jsonify({"error": "ChromaDB not initialized"}), 500
        
        results = collection.query(
            query_texts=[query],
            n_results=10,
            include=["documents", "metadatas", "distances"]
        )
        
        passages = []
        docs = results.get('documents', [[]])[0]
        metas = results.get('metadatas', [[]])[0]
        dists = results.get('distances', [[]])[0]
        
        for idx, (doc_text, metadata, distance) in enumerate(zip(docs, metas, dists), 1):
            passages.append({
                "rank": idx,
                "source": metadata.get('source', 'Unknown'),
                "distance": float(distance),
                "content_preview": doc_text[:300],
                "metadata": metadata
            })
        
        return jsonify({
            "status": "success",
            "query": query,
            "results_count": len(passages),
            "passages": passages,
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


# -----------------------------------------------------------------------------
# CORS preflight
# -----------------------------------------------------------------------------
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        return response, 200


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Finance Chatbot Backend on port {port}...")
    print(f"API available at: http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)