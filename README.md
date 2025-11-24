📑 Table of Contents

Features
Tech Stack
System Architecture
Prerequisites
Installation
Configuration
Usage
Authentication
API Documentation
Project Structure
Troubleshooting
Contributing
License


✨ Features
🔐 Authentication & Authorization

Role-Based Access Control (RBAC)

Admin: Full system access
Student: Chat-only access with theme customization


Secure SHA-256 password hashing
Session management with login time tracking
Guest mode for quick access
User profile management
Password change functionality

💬 Intelligent Chat Interface

AI-powered Q&A using Google Gemini and Ollama
Context-aware responses from uploaded documents
Source citation and passage highlighting
Relevance scoring for retrieved documents
Key points extraction
Next steps suggestions
Chat history export

📤 Document Management

Multi-format support (PDF, DOCX, TXT, CSV, XLSX)
Batch upload capability
Automatic text extraction and chunking
Vector embeddings with ChromaDB
Document metadata tracking
Progress tracking for uploads

🔍 AI-Powered Analysis

File content analysis
Automatic summarization
Key information extraction
Multi-model AI support (Google Gemini + Ollama)
Raw model output inspection

📊 Admin Dashboard

System statistics and analytics
API status monitoring
User management panel
Document count tracking
Chat history management
Performance metrics

🎨 Modern UI/UX

Beautiful gradient designs
Google Fonts (Inter, Poppins, JetBrains Mono)
Dark/Light theme support
Responsive design
Smooth animations and transitions
Custom scrollbars


🛠 Tech Stack
Frontend

Streamlit - Web framework for Python
HTML/CSS - Custom styling
Google Fonts - Typography

Backend

Flask - RESTful API server
Python 3.8+ - Core language

AI/ML

Google Gemini AI - Primary LLM for chat
Ollama - Local LLM (llama3.2)
ChromaDB - Vector database for embeddings
LangChain - Document processing and chunking

Document Processing

PyPDF2 - PDF text extraction
python-docx - DOCX processing
openpyxl - Excel file handling
pandas - CSV processing

Storage

JSON - User database
ChromaDB - Vector embeddings storage


🏗 System Architecture
┌─────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │   Auth   │  │   Chat   │  │  Upload  │  │  Admin  │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
                         ▼
┌─────────────────────────────────────────────────────────┐
│                     FLASK BACKEND                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │   API    │  │ Document │  │  Vector  │  │   AI    │ │
│  │  Routes  │  │Processing│  │  Store   │  │ Engine  │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   ChromaDB   │  │ Google Gemini│  │    Ollama    │
│   (Vectors)  │  │     API      │  │  (Local LLM) │
└──────────────┘  └──────────────┘  └──────────────┘

📋 Prerequisites
Software Requirements

Python 3.8 or higher
pip (Python package manager)
Git
Ollama (for local LLM)

API Keys

Google Gemini API Key (Get it here)

System Requirements

RAM: 8GB minimum (16GB recommended for Ollama)
Storage: 5GB free space
OS: Windows 10/11, macOS, or Linux


🚀 Installation
1. Clone the Repository
bashgit clone https://github.com/pradeept3/finance-chatbot.git
cd finance-chatbot
2. Create Virtual Environment
bash# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
3. Install Dependencies
bash# Install backend dependencies
pip install -r requirements.txt

# Or install manually
pip install flask flask-cors streamlit google-generativeai chromadb langchain pypdf2 python-docx openpyxl pandas requests
4. Install Ollama
Windows/macOS:

Download from Ollama.ai
Run installer

Linux:
bashcurl -fsSL https://ollama.ai/install.sh | sh
Pull the model:
bashollama pull llama3.2
5. Set Up Environment Variables
Create a .env file in the backend directory:
bash# backend/.env
GOOGLE_API_KEY=your_google_gemini_api_key_here
FLASK_ENV=development
FLASK_DEBUG=True

⚙️ Configuration
Backend Configuration
Edit backend/config.py (if exists) or set environment variables:
python# API Configuration
GOOGLE_API_KEY = "your_api_key_here"
OLLAMA_BASE_URL = "http://localhost:11434"
FLASK_PORT = 5000

# ChromaDB Configuration
CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "finance_docs"

# Document Processing
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_FILE_SIZE_MB = 50
Frontend Configuration
Edit frontend/utils/api_client.py:
pythonAPI_URL = "http://127.0.0.1:5000"  # Backend URL

🎯 Usage
1. Start the Backend Server
bashcd backend
python app.py
Expected output:
 * Running on http://127.0.0.1:5000
 * Backend server started successfully
2. Start the Frontend
Open a new terminal:
bashcd frontend
streamlit run streamlit_app.py
Expected output:
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
  Network URL: http://192.168.1.x:8501
3. Access the Application
Open your browser and navigate to:
http://localhost:8501

🔐 Authentication
Default Login Credentials
Admin Account
Username: admin
Password: admin123
Permissions:

Upload documents
Analyze files
View statistics
Manage users
Full system access

Student Accounts
Username: student1
Password: student123

Username: student2
Password: student123
Permissions:

Chat interface only
Theme customization
Limited access

Guest Mode
Click "Guest Mode" button for instant student-level access without login.
Managing Users (Admin Only)

Login as admin
Go to "Users" tab
View Users - See all registered users
Add User - Create new accounts
Delete User - Remove user accounts
Change Password - Update your password


📚 API Documentation
Backend API Endpoints
1. Health Check
httpGET /api/status
Response:
json{
  "backend": "running",
  "documents": 150
}
2. Upload Documents
httpPOST /api/upload
Content-Type: multipart/form-data
Request:
files: [file1.pdf, file2.docx]
Response:
json{
  "message": "Files uploaded successfully",
  "processed_files": 2,
  "total_chunks": 45
}
3. Chat Query
httpPOST /api/chat
Content-Type: application/json
Request:
json{
  "query": "What is the revenue for Q3?",
  "use_google": true,
  "use_ollama": false
}
Response:
json{
  "response": "Based on the documents...",
  "passages": [...],
  "key_points": [...],
  "model_used": "google"
}
4. Get Documents
httpGET /api/documents
Response:
json{
  "total_documents": 150,
  "collections": ["finance_docs"]
}
5. AI Status
httpGET /api/ai-status
Response:
json{
  "google_api": "configured",
  "ollama": "running"
}
6. Analyze File
httpPOST /api/analyze-file
Content-Type: multipart/form-data
Request:
file: document.pdf
use_google: true
use_ollama: false
Response:
json{
  "filename": "document.pdf",
  "google_response": "Summary of document...",
  "ollama_response": null
}

📂 Project Structure
finance-chatbot/
├── backend/
│   ├── app.py                 # Flask application
│   ├── chroma_db/             # Vector database storage
│   ├── uploads/               # Uploaded files
│   └── requirements.txt       # Backend dependencies
│
├── frontend/
│   ├── components/
│   │   ├── auth.py           # 🔐 Authentication system
│   │   ├── sidebar.py        # Sidebar component
│   │   ├── chat.py           # Chat interface
│   │   ├── upload.py         # File upload interface
│   │   └── file_analysis.py  # File analysis component
│   │
│   ├── utils/
│   │   └── api_client.py     # API communication
│   │
│   ├── streamlit_app.py      # Main application
│   └── user_database.json    # User credentials (auto-generated)
│
├── .gitignore
├── README.md                  # This file
└── LICENSE

🔧 Troubleshooting
Common Issues
1. Backend Not Connecting
Problem: Frontend shows "Backend Not Connected"
Solution:
bash# Check if backend is running
curl http://127.0.0.1:5000/api/status

# Restart backend
cd backend
python app.py
2. Ollama Not Working
Problem: "Ollama: 🔴 Offline"
Solution:
bash# Start Ollama service
ollama serve

# Pull the model
ollama pull llama3.2

# Test Ollama
curl http://localhost:11434/api/tags
3. Google API Error
Problem: "Google API: 🔴 Not Configured"
Solution:

Check your .env file has correct API key
Verify API key at Google AI Studio
Restart backend server

4. Import Error
Problem: ModuleNotFoundError: No module named 'components.auth'
Solution:
bash# Ensure auth.py exists
ls frontend/components/auth.py

# If missing, create the file with authentication code
5. ChromaDB Permission Error
Problem: Permission denied for chroma_db directory
Solution:
bash# Linux/macOS
chmod -R 755 backend/chroma_db

# Windows - Run as Administrator
6. Port Already in Use
Problem: Port 5000 or 8501 already in use
Solution:
bash# Backend (change port in app.py)
app.run(host="0.0.0.0", port=5001)

# Frontend
streamlit run streamlit_app.py --server.port 8502

🧪 Testing
Manual Testing
bash# Test backend health
curl http://127.0.0.1:5000/api/status

# Test Ollama
curl http://localhost:11434/api/tags

# Test Google API (requires valid key)
python -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print('OK')"
User Flow Testing

Login Flow

 Admin login works
 Student login works
 Guest mode works
 Logout works


Admin Features

 Upload documents
 Chat with documents
 Analyze files
 View statistics
 Add/delete users


Student Features

 Chat interface accessible
 Theme selection works
 Cannot access admin features




🤝 Contributing
Contributions are welcome! Please follow these steps:

Fork the repository
Create a feature branch

bash   git checkout -b feature/amazing-feature

Commit your changes

bash   git commit -m "✨ Add amazing feature"

Push to the branch

bash   git push origin feature/amazing-feature

Ope