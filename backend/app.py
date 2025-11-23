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
from utils.response_generator import generate_detailed_response
from utils.document_loader import load_documents, chunk_documents
from werkzeug.utils import secure_filename
from utils.file_analyzer import FileAnalyzer
from next_steps_graph import run_next_steps_graph

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
        user_query = data.get("message", "").strip()

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

        # Retrieve passages from ChromaDB
        retrieved_data = query_documents(collection, user_query, n_results=10)

        # Let response_generator build the full RAG answer
        response_data = generate_detailed_response(user_query, retrieved_data)

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
        print(f"Error in chat endpoint: {e}")
        return (
            jsonify({"error": str(e), "response": "An error occurred."}),
            500,
        )


# -----------------------------------------------------------------------------
# Upload & index files into ChromaDB
# -----------------------------------------------------------------------------
@app.route("/api/upload", methods=["POST"])
def upload_documents():
    try:
        if "files" not in request.files:
            return (
                jsonify(
                    {
                        "error": "No files provided",
                        "message": "Please upload at least one file",
                    }
                ),
                400,
            )

        files = request.files.getlist("files")
        uploaded_files = []
        errors = []

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                uploaded_files.append(filename)
            elif file:
                errors.append(f"{file.filename} - Invalid file type")

        if uploaded_files:
            print(f"Processing {len(uploaded_files)} uploaded files.")

            raw_docs = load_documents(app.config["UPLOAD_FOLDER"])
            chunks = chunk_documents(raw_docs)
            count = add_documents_to_chromadb(collection, chunks)

            return (
                jsonify(
                    {
                        "status": "success",
                        "message": f"Successfully uploaded {len(uploaded_files)} file(s)",
                        "files_uploaded": uploaded_files,
                        "documents_added": count,
                        "errors": errors,
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "No valid files uploaded",
                        "errors": errors,
                    }
                ),
                400,
            )

    except Exception as e:
        print(f"Error uploading documents: {e}")
        return (
            jsonify({"error": str(e), "message": "Error uploading documents"}),
            500,
        )


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
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/api/batch-analyze", methods=["POST"])
def batch_analyze():
    """Analyze multiple uploaded files"""
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


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Finance Chatbot Backend on port {port}...")
    print(f"API available at: http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)