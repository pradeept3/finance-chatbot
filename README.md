PyPI installation
-------------------
pip install finance-chatbot


Prerequisites
----------------
Python 3.8+
pip (Python package manager)
Google Gemini API Key
Ollama (optional)


Installation
------------------
1. Clone the Repository

```console
git clone https://github.com/pradeept3/finance-chatbot.git
cd finance-chatbot
```
2. Install Dependencies
```python
pip install -r requirements.txt
```


3. update the /backend/.env file:
  
  ```css
  GOOGLE_API_KEY=your_google_api_key_here
  OLLAMA_API_URL=http://localhost:11434
  PORT=5000
  UPLOAD_DIR=./uploaded_documents
  MAX_UPLOAD_SIZE=50
  ```


4. Running the Application
    
  ```python
  Start Backend Server
    Open Terminal/ Command prompt:
    Goto the finance-chatbot folder and type cd backend
    python app.py
    Backend runs on: http://127.0.0.1:5000
  Start Frontend (in new terminal)
    Goto the finance-chatbot folder and type cd frontend
    streamlit run main.py
    Frontend runs on: http://localhost:8501
  ```

5. Checklist Before Deployment

  A.  All dependencies installed (pip install -r requirements.txt)
  B.  .env file configured with API keys
  C.  Backend tested (python app.py)
  D.  Frontend tested (streamlit run main.py)
  E.  Sample documents uploaded and searched
  F.  Admin/Student/Guest roles working

