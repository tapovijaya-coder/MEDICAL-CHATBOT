# MediBot AI - Intelligent Medical Information Assistant (RAG)

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Groq](https://img.shields.io/badge/Groq-API%20Llama%20%2F%20Qwen-f55036.svg)](https://groq.com/)
[![FAISS](https://img.shields.io/badge/Vector%20Store-FAISS-0A85EA.svg)](https://github.com/facebookresearch/faiss)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**MediBot AI** is a production-grade clinical information chatbot powered by **Retrieval-Augmented Generation (RAG)**. It extracts, embeds, and indexes medical literature, clinical practice guidelines, and research PDFs into a high-performance **FAISS** vector store, synthesizing evidence-backed answers using **Groq's ultra-low-latency inference engine** while upholding strict medical safety protocols and page-level citations.

---

## 🌟 Key Features

- **Evidence-Grounded RAG Pipeline**: Restricts responses to verified medical PDF sources to prevent hallucinations.
- **Accurate Page Citations**: Every response references the exact document name, page number, and relevant excerpt.
- **Red-Flag Emergency Detection**: Proactively detects life-threatening symptom keywords (e.g., crushing chest pain, anaphylaxis, stroke symptoms) and injects immediate red-flag emergency guidance.
- **Multi-Turn Conversational Memory**: Session-isolated chat history maintaining recent dialogue context without deprecated memory chains.
- **Local FAISS Vector Database**: Fast cosine similarity retrieval over 384-dimensional dense semantic vectors with automated re-indexing on document deletion.
- **Document Management**: Drag-and-drop PDF upload with client-side validation, page extraction via PyPDF, and chunking with `RecursiveCharacterTextSplitter`.
- **Modern Healthcare Dashboard**: Emerald-themed UI inspired by modern clinical AI SaaS platforms, complete with mobile drawer navigation, live backend status indicators, and collapsible citation accordions.

---

## 🏗️ Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                                  USER / BROWSER                                   |
|                        (React + Vite @ http://localhost:5173)                     |
+------------------------------------------+----------------------------------------+
                                           | HTTP / REST (Axios)
                                           v
+-----------------------------------------------------------------------------------+
|                                FASTAPI BACKEND API                                |
|                                (http://localhost:8000)                            |
+-------------------+---------------------------------------+-----------------------+
                    |                                       |
       [Document Ingestion Flow]               [Query & Retrieval Flow]
                    |                                       |
                    v                                       v
        +-----------------------+               +-----------------------+
        |   PyPDF Text Extractor|               |  Symptom Emergency    |
        +-----------+-----------+               |   Keyword Detector    |
                    |                           +-----------+-----------+
                    v                                       |
        +-----------------------+                           v
        | RecursiveCharacter-   |               +-----------------------+
        |     TextSplitter      |               |  HuggingFace Embed    |
        +-----------+-----------+               |  (all-MiniLM-L6-v2)   |
                    |                           +-----------+-----------+
                    v                                       |
        +-----------------------+                           v
        |  HuggingFace Embed    |               +-----------------------+
        | (all-MiniLM-L6-v2)    |               |  FAISS Vector Search  |
        +-----------+-----------+               |  (Top-K Similarity)   |
                    |                           +-----------+-----------+
                    v                                       |
        +-----------------------+                           v
        |      FAISS Store      |<--------------------------+
        |    (vectorstore/)     |               (Retrieved Context Chunks)
        +-----------------------+                           |
                                                            v
                                                +-----------------------+
                                                |  Medical Prompt Build |
                                                |   + Session History   |
                                                +-----------+-----------+
                                                            |
                                                            v
                                                +-----------------------+
                                                |     GROQ Cloud API    |
                                                |  (Fast LLM Inference) |
                                                +-----------------------+
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite, Lucide React icons, Axios, Modern CSS (Responsive Flex/Grid) |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2, Python-dotenv |
| **Orchestration & RAG**| LangChain Core, LangChain Text Splitters, PyPDF |
| **Embeddings** | Hugging Face Sentence Transformers (`all-MiniLM-L6-v2`, 384-dim) |
| **Vector Database** | Meta FAISS (`faiss-cpu`) with local disk persistence |
| **LLM Inference** | Groq Cloud API (`qwen/qwen3.8-27b`, `openai/gpt-oss-120b`, or `llama-3.3-70b-versatile`) |
| **Testing** | Pytest, FastAPI TestClient, HTTPX |

---

## 📁 Project Structure

```
MEDICAL CHATBOT/
│
├── frontend/                     # React Single-Page Application
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx       # Document list, session history, brand emblem
│   │   │   ├── ChatWindow.jsx    # Hero screen, suggestions, message stream
│   │   │   ├── ChatInput.jsx     # Auto-resizing textarea, paperclip attach, send
│   │   │   ├── MessageBubble.jsx # Formatted text, emergency alert, citation drawer
│   │   │   ├── DocumentUpload.jsx# Drag-and-drop modal with progress bar
│   │   │   └── Header.jsx        # Connectivity pill, doc counter, mobile toggle
│   │   ├── pages/
│   │   │   └── Dashboard.jsx     # Master state, sessions, toast notifications
│   │   ├── services/
│   │   │   └── api.js            # Axios REST client with error interception
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css            # Emerald healthcare theme design system
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
├── backend/                      # FastAPI Python Application
│   ├── __init__.py
│   ├── main.py                   # REST endpoints, CORS middleware, lifespan
│   ├── chatbot.py                # Groq API client, session memory, RAG query flow
│   ├── document_processor.py     # PDF validation, text extraction & chunking
│   ├── embeddings.py             # Hugging Face Sentence Transformers singleton
│   ├── vectorstore.py            # FAISS IndexFlatIP, document registry, persistence
│   ├── prompt_template.py        # System prompt, red-flag regexes, citation rules
│   ├── schemas.py                # Pydantic v2 validation models
│   └── requirements.txt
│
├── data/
│   └── uploaded_pdfs/            # Local storage for uploaded medical PDFs
│
├── vectorstore/                  # Local FAISS index & metadata registry
│   ├── faiss.index
│   ├── chunks.json
│   └── registry.json
│
├── tests/                        # Automated unit & integration tests
│   ├── conftest.py
│   ├── test_api.py               # REST API endpoint tests
│   ├── test_documents.py         # PyPDF extraction & chunking tests
│   └── test_rag.py               # FAISS indexing, similarity & emergency detector
│
├── .env.example                  # Environment variable reference
├── .gitignore                    # Excludes secrets, dependencies, and caches
└── README.md
```

---

## ⚡ Quick Start & Installation

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- A free [Groq Cloud API Key](https://console.groq.com/keys)

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/MediBot-AI.git
cd MediBot-AI
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and provide your Groq API key:
```ini
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
DATA_DIR=data/uploaded_pdfs
VECTORSTORE_DIR=vectorstore
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=5173
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 4. Install Dependencies

#### Python Backend:
```bash
pip install -r backend/requirements.txt
```

#### React Frontend:
```bash
cd frontend
npm install
cd ..
```

---

## 🚀 Running the Application

### Option A: Run Both Servers Simultaneously

**Terminal 1 — FastAPI Backend:**
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
*API will be available at:* `http://localhost:8000`  
*Swagger Documentation:* `http://localhost:8000/docs`

**Terminal 2 — React Frontend:**
```bash
cd frontend
npm run dev
```
*Web Dashboard will open at:* `http://localhost:5173`

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health status, FAISS ready state, total document count, Groq config |
| `POST` | `/api/chat` | Send medical question with session ID; returns RAG answer + citations |
| `POST` | `/api/documents/upload` | Upload medical PDF file; extracts text, generates embeddings, updates FAISS |
| `GET` | `/api/documents` | Retrieve metadata list of all indexed medical documents |
| `DELETE` | `/api/documents/{id}` | Delete document and remove all associated vectors from FAISS index |
| `GET` | `/api/sessions/{id}/history`| Retrieve past message history for a conversation session |
| `DELETE` | `/api/sessions/{id}` | Clear conversation session history |

### Example Chat Request:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is hypertension and how is it managed lifestyle-wise?",
    "session_id": "session_1"
  }'
```

### Example Chat Response:
```json
{
  "answer": "According to the clinical guidelines, essential hypertension is defined as a persistent systolic blood pressure of 130 mmHg or greater...",
  "sources": [
    {
      "source": "clinical_hypertension_diabetes_guide.pdf",
      "page": 1,
      "excerpt": "Hypertension is defined as a persistent systolic blood pressure of 130 mmHg or greater..."
    }
  ],
  "session_id": "session_1",
  "is_emergency": false
}
```

---

## 🧪 Testing and Verification

Run the comprehensive pytest suite covering document processing, FAISS vector storage, RAG retrieval, emergency detectors, and API endpoints:

```bash
python -m pytest tests -v
```

To run individual test modules:
```bash
# Test PDF extraction and semantic chunking
python -m pytest tests/test_documents.py -v

# Test FAISS vector indexing, embeddings, and similarity search
python -m pytest tests/test_rag.py -v

# Test FastAPI HTTP endpoints
python -m pytest tests/test_api.py -v
```

To verify the React frontend production build:
```bash
cd frontend
npm run build
```

---

## ⚕️ Medical Disclaimer & Clinical Safety Notice

> **IMPORTANT CLINICAL NOTICE:**  
> **MediBot AI** is an artificial intelligence-powered information retrieval assistant designed strictly for **educational and research purposes**.  
> - It does **not** provide clinical medical diagnoses.  
> - It does **not** prescribe pharmaceuticals or recommend medication dosages.  
> - It does **not** replace the judgment, consultation, diagnosis, or treatment of a licensed physician or healthcare specialist.  
> - **In Case of Emergency:** If you or someone near you experiences acute, severe, or life-threatening symptoms (such as acute chest pain, sudden numbness/paralysis, difficulty breathing, slurred speech, or heavy uncontrolled bleeding), **call your local emergency medical services immediately (e.g., 911, 112, 999). Do not rely on an AI chatbot in an emergency.**

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

