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

# ✓ Comprehensive document processor (replaces old vision processor)
from utils.comprehensive_document_processor import create_comprehensive_document

import requests
from werkzeug.serving import WSGIRequestHandler
WSGIRequestHandler.timeout = 120

load_dotenv()


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

UPLOAD_FOLDER = os.getenv("UPLOAD_DIR", "./uploaded_documents")
MAX_FILE_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 50)) * 1024 * 1024

# Allow images too if you want to analyze them
ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx", "txt", "png", "jpg", "jpeg"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")

# Configure Google Gemini for image analysis
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
# Configure Google Gemini for image analysis
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
        
        # Use comprehensive prompts for detailed analysis
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
    return (
        jsonify(
            {
                "status": "healthy",
                "message": "Finance Chatbot Backend is running",
                "timestamp": datetime.now().isoformat(),
            }
        ),
        200,
    )


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
# Chat endpoint (RAG over ChromaDB)
# -----------------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        
        # Accept both "message" and "query" for compatibility
        user_query = data.get("message", "") or data.get("query", "")
        user_query = user_query.strip()
        
        print(f"\n{'='*60}")
        print(f"[Chat] Received query: {user_query}")
        print(f"{'='*60}")

        if not user_query:
            return (
                jsonify(
                    {
                        "error": "Message required",
                        "response": "Please provide a message.",
                    }
                ),
                400,
            )

        if not collection:
            return (
                jsonify(
                    {
                        "error": "DB error",
                        "response": "System error: Database not initialized.",
                    }
                ),
                500,
            )

        # Query ChromaDB
        print("[Chat] Querying ChromaDB...")
        retrieved_data = query_documents(collection, user_query, n_results=5)
        
        print(f"[Chat] Retrieved {len(retrieved_data.get('passages', []))} passages")
        if retrieved_data.get('passages'):
            for i, p in enumerate(retrieved_data.get('passages', [])[:3], 1):
                print(f"  {i}. {p.get('source', 'Unknown')}: {p.get('text', '')[:60]}...")

        # Generate response
        print("[Chat] Generating response...")
        response_data = generate_detailed_response(user_query, retrieved_data)
        
        print(f"[Chat] Response generated ({len(response_data.get('main_response', ''))} chars)")
        print(f"[Chat] Model used: {response_data.get('model_used', 'unknown')}")
        print(f"{'='*60}\n")

        return (
            jsonify(
                {
                    "response": response_data["main_response"],
                    "key_points": response_data["key_points"],
                    "sections": response_data["sections"],
                    "google_raw": response_data["google_raw"],
                    "ollama_raw": response_data["ollama_raw"],
                    "model_used": response_data["model_used"],
                    "passages": response_data["passages"],
                    "url_summaries": response_data.get("url_summaries", []),
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                }
            ),
            200,
        )

    except Exception as e:
        print(f"\n[Chat ERROR] {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        return (
            jsonify({
                "error": str(e), 
                "response": "An error occurred while processing your request.",
                "status": "error"
            }),
            500,
        )

# -----------------------------------------------------------------------------
# Upload & index files into ChromaDB
# -----------------------------------------------------------------------------
# Replace the entire /api/upload section with this:

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

        # ========== PROCESS FILES ==========
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                
                print(f"\n[UPLOAD] 📄 Processing: {filename}")
                print(f"[UPLOAD] Path: {filepath}")
                
                # Determine file type
                ext = filename.rsplit('.', 1)[1].lower()
                
                try:
                    # Use comprehensive processor for ALL file types
                    print(f"[UPLOAD] 🔍 Calling comprehensive_document_processor...")
                    result = create_comprehensive_document(filepath, ext)
                    
                    print(f"[UPLOAD] Result - Success: {result['success']}")
                    print(f"[UPLOAD] Content length: {len(result['content'])} characters")
                    print(f"[UPLOAD] Metadata: {result['metadata']}")
                    
                    if result["success"] and result["content"]:
                        from langchain_core.documents import Document
                        
                        # Create document for ChromaDB
                        doc = Document(
                            page_content=result["content"],
                            metadata=result["metadata"]
                        )
                        
                        print(f"[UPLOAD] 💾 Storing in ChromaDB...")
                        # Add to ChromaDB - returns number of documents added
                        docs_added = add_documents_to_chromadb(collection, [doc])
                        print(f"[UPLOAD] ✓ Stored {docs_added} document chunk(s)")
                        
                        total_documents_added += docs_added
                        
                        # Track what was processed
                        if ext in ['jpg', 'jpeg', 'png']:
                            image_count += 1
                            print(f"[UPLOAD] ✓ Image counted")
                        elif ext == 'pdf' and result["metadata"].get("has_images"):
                            vision_enabled_pdfs += 1
                            img_cnt = result["metadata"].get("image_count", 0)
                            image_count += img_cnt
                            print(f"[UPLOAD] ✓ Vision PDF with {img_cnt} images")
                        
                        uploaded_files.append({
                            "filename": filename,
                            "size": os.path.getsize(filepath),
                            "type": ext,
                            "content_length": len(result["content"]),
                            "metadata": result["metadata"]
                        })
                        
                        print(f"[UPLOAD] ✓✓✓ {filename} SUCCESS")
                    else:
                        error_msg = "Processing failed - no content"
                        errors.append(f"{filename} - {error_msg}")
                        print(f"[UPLOAD] ✗ {error_msg}")
                        
                except Exception as e:
                    error_msg = str(e)
                    errors.append(f"{filename} - {error_msg}")
                    print(f"[UPLOAD] ✗✗✗ ERROR: {error_msg}")
                    import traceback
                    traceback.print_exc()
            elif file:
                errors.append(f"{file.filename} - Invalid file type")
                print(f"[UPLOAD] ✗ Invalid: {file.filename}")

        # ========== PROCESS URLs ==========
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
                        print(f"[UPLOAD] ✓ URL processed: {url}")
                    else:
                        errors.append(f"{url} - {result.get('error', 'Failed to scrape')}")
                        print(f"[UPLOAD] ✗ URL failed: {url}")
                        
                except Exception as e:
                    errors.append(f"{url} - {str(e)}")
                    print(f"[UPLOAD] ✗ URL error: {str(e)}")
            else:
                errors.append(f"{url} - Invalid URL")
                print(f"[UPLOAD] ✗ Invalid URL: {url}")

        print(f"\n{'='*70}")
        print(f"[UPLOAD] SUMMARY")
        print(f"{'='*70}")
        print(f"Files uploaded: {len(uploaded_files)}")
        print(f"URLs processed: {url_count}")
        print(f"Images found: {image_count}")
        print(f"Vision PDFs: {vision_enabled_pdfs}")
        print(f"Total docs in ChromaDB: {total_documents_added}")
        print(f"Errors: {len(errors)}")
        print(f"{'='*70}\n")

        # Return comprehensive response
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
        print(f"{'='*70}\n")
        
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

        return (
            jsonify(
                {
                    "total_documents": collection.count(),
                    "status": "success",
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------------------------
# File analysis (Google + Ollama)
# -----------------------------------------------------------------------------
@app.route("/api/analyze-file", methods=["POST"])
def analyze_file():
    """Analyze uploaded file with Google API and Ollama"""
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
        
        # ✓ Check if image
        if is_image_file(filename):
            # Image analysis with enhanced detail
            preview = "Image file - detailed visual analysis below"
            
            google_analysis = FileAnalyzer.analyze_image_with_google(filepath)
            ollama_analysis = {
                "status": "error",
                "error": "Ollama does not support image analysis"
            }
        else:
            # Document analysis
            preview = FileAnalyzer.get_file_preview(filepath)
            google_analysis = FileAnalyzer.analyze_with_google(filepath, preview)
            ollama_analysis = FileAnalyzer.analyze_with_ollama(filepath, preview)

        response_data = {
            "status": "success",
            "file": metadata,
            "preview": preview,
            "analysis": {
                "google": google_analysis,
                "ollama": ollama_analysis,
            },
            "timestamp": datetime.now().isoformat(),
        }

        return jsonify(response_data), 200

    except Exception as e:
        print(f"Error analyzing file: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route("/api/batch-analyze", methods=["POST"])
def batch_analyze():
    """Analyze multiple uploaded files (including images with detailed vision)"""
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
                
                # ✓ Check if image
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

                results.append(
                    {
                        "file": metadata,
                        "preview": preview[:300],
                        "analysis": {
                            "google": google_analysis,
                            "ollama": ollama_analysis,
                        },
                    }
                )

        return (
            jsonify(
                {
                    "status": "success",
                    "files_analyzed": len(results),
                    "results": results,
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        print(f"Error in batch analysis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "status": "error"}), 500


# -----------------------------------------------------------------------------
# AI services status
# -----------------------------------------------------------------------------
@app.route("/api/ai-status", methods=["GET"])
def ai_status():
    try:
        # Google
        google_status = "configured" if GOOGLE_API_KEY else "not_configured"

        # Ollama
        ollama_status = "disconnected"
        try:
            resp = requests.get(f"{OLLAMA_API_URL}/api/tags", timeout=5)
            if resp.status_code == 200:
                ollama_status = "connected"
        except Exception:
            ollama_status = "disconnected"

        return (
            jsonify(
                {
                    "status": "success",
                    "google_api": google_status,
                    "ollama": ollama_status,
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------------------
# NEXT STEPS ENDPOINT (Rule-based suggester)
# -----------------------------------------------------------------------
@app.route("/api/next-steps", methods=["POST"])
def api_next_steps():
    """
    Accepts:
      {
        "user_question": "...",
        "answer_text": "...",
        "key_points": [...]
      }

    Returns:
      {
        "suggestions": [ {label, category, reason}, ... ],
        "error": null | str
      }
    """
    try:
        data = request.get_json(force=True) or {}

        user_question = (data.get("user_question") or "").strip()
        answer_text = (data.get("answer_text") or "").strip()
        key_points = data.get("key_points") or []

        if not user_question or not answer_text:
            return jsonify(
                {
                    "error": "user_question and answer_text are required",
                    "suggestions": [],
                }
            ), 400

        result = run_next_steps_graph(
            user_question=user_question,
            answer_text=answer_text,
            key_points=key_points,
        )

        return jsonify(result), 200

    except Exception as e:
        print("[/api/next-steps ERROR]", e)
        return jsonify({"error": str(e), "suggestions": []}), 500


# -----------------------------------------------------------------------
# CORS preflight handler
# -----------------------------------------------------------------------
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        return response, 200


# Add this endpoint to app.py to debug document storage:

@app.route("/api/debug-documents", methods=["GET"])
def debug_documents():
    """Debug endpoint - shows all documents in ChromaDB"""
    try:
        if not collection:
            return jsonify({"error": "ChromaDB not initialized"}), 500

        print(f"\n{'='*70}")
        print(f"[DEBUG] Retrieving all documents from ChromaDB...")
        print(f"{'='*70}\n")
        
        total_count = collection.count()
        print(f"Total documents in ChromaDB: {total_count}\n")
        
        if total_count == 0:
            return jsonify({
                "status": "empty",
                "total_documents": 0,
                "message": "ChromaDB is empty"
            }), 200
        
        # Get a sample of documents
        results = collection.get(limit=100)
        
        documents = []
        if results and 'documents' in results:
            for idx, (doc_id, doc_text, metadata) in enumerate(zip(
                results.get('ids', []),
                results.get('documents', []),
                results.get('metadatas', [])
            ), 1):
                doc_info = {
                    "index": idx,
                    "id": doc_id,
                    "content_length": len(doc_text),
                    "content_preview": doc_text[:200] + "..." if len(doc_text) > 200 else doc_text,
                    "metadata": metadata,
                    "full_content_length": len(doc_text)
                }
                documents.append(doc_info)
                
                print(f"[{idx}] ID: {doc_id}")
                print(f"    Length: {len(doc_text)} chars")
                print(f"    Metadata: {metadata}")
                print(f"    Preview: {doc_text[:100]}...\n")
        
        return jsonify({
            "status": "success",
            "total_documents": total_count,
            "sample_count": len(documents),
            "documents": documents,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@app.route("/api/search-debug", methods=["POST"])
def search_debug():
    """Debug search - shows what's retrieved"""
    try:
        data = request.json or {}
        query = data.get("query", "")
        
        if not query:
            return jsonify({"error": "Query required"}), 400
        
        print(f"\n{'='*70}")
        print(f"[DEBUG SEARCH] Query: {query}")
        print(f"{'='*70}\n")
        
        if not collection:
            return jsonify({"error": "ChromaDB not initialized"}), 500
        
        # Search with different result counts
        results = collection.query(
            query_texts=[query],
            n_results=10,
            include=["documents", "metadatas", "distances"]
        )
        
        print(f"Retrieved {len(results.get('documents', [[]])[0])} results\n")
        
        passages = []
        docs = results.get('documents', [[]])[0]
        metas = results.get('metadatas', [[]])[0]
        dists = results.get('distances', [[]])[0]
        
        for idx, (doc_text, metadata, distance) in enumerate(zip(docs, metas, dists), 1):
            passage = {
                "rank": idx,
                "id": f"P{idx}",
                "source": metadata.get('source', 'Unknown'),
                "type": metadata.get('type', 'unknown'),
                "distance": float(distance) if distance else None,
                "content_length": len(doc_text),
                "content_preview": doc_text[:300] + "..." if len(doc_text) > 300 else doc_text,
                "full_content": doc_text,
                "metadata": metadata
            }
            passages.append(passage)
            
            print(f"[P{idx}] Distance: {distance:.4f}")
            print(f"      Source: {metadata.get('source')}")
            print(f"      Type: {metadata.get('type')}")
            print(f"      Length: {len(doc_text)} chars")
            print(f"      Preview: {doc_text[:100]}...\n")
        
        return jsonify({
            "status": "success",
            "query": query,
            "results_count": len(passages),
            "passages": passages,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"[DEBUG SEARCH] Error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Finance Chatbot Backend on port {port}...")
    print(f"API available at: http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)