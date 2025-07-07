# DocIntel

> AI‑powered document intelligence platform built with **FastAPI**, **React + Tailwind CSS**, and free/open‑source large‑language models. Upload PDFs, get smart summaries, ask questions in Hinglish/English, and practise with auto‑generated quizzes


---

## Table of Contents

1. [Features](#features)  
2. [Architecture](#architecture)  
3. [Quick Start](#quick-start)  
4. [Detailed Setup](#detailed-setup)  
   - [Backend](#backend-setup)  
   - [Frontend](#frontend-setup)  
5. [Folder Structure](#folder-structure)   
6. [Contributing](#contributing)  

---

## Features

| ⭐ | Feature | Description |
| :-- | :-- | :-- |
| 📄 | **PDF Upload & Parsing** | Drag‑and‑drop PDFs; parsing via **PyMuPDF/pdfplumber** with automatic metadata extraction |
| 🔍 | **RAG‑based Q&A** | Hybrid keyword + vector search powered by **LangChain/LlamaIndex** and local **Mistral‑7B** (no paid APIs) |
| 📝 | **Smooth Summaries** | One‑click generation of paragraph‑style summaries with highlighted key terms (per user preference) |
| ❔ | **Challenge Mode** | Dynamic MCQs with correctness, score, feedback, justification & reference text (ideal for exam prep) |
| 🇮🇳 | **Hindi‑friendly** | Responses can switch between English or Hinglish as needed |
| 🎨 | **Modern UI** | Responsive React + Tailwind, dark‑mode toggle, soft shadows, smooth animations |
| ⚡ | **Fast & Light** | No heavyweight DB; in‑memory doc store for quick prototyping, pluggable with Postgres/Chroma later |

---

## Architecture

> **Flow Explanation:**  
> 1. **Client** uploads a PDF → FastAPI streams file to the server.  
> 2. **RAGService** splits & embeds chunks; stores metadata in memory.  
> 3. For each query/quiz request, contextual prompt is built & sent to **LLM Runtime**.  
> 4. Generated answer/MCQs return to the client for display.

---

## Quick Start

```bash
# 1. Clone 🛠️
git clone https://github.com/shivapareek/DocIntel.git && cd DocIntel

# 2. Fire up everything with Docker 🐳
docker compose up --build

# 3. Open http://localhost:5173  (frontend)
#    Backend runs on http://localhost:8000
```

> **Note:** Default compose pulls a pre‑quantised Mistral‑7B‑Instruct model (≈4 GB). First run may take a while.

---

## Detailed Setup

### Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```


### Frontend Setup

```bash
cd frontend
npm run dev
```
---

## Folder Structure

```text
GENAI-DOC-ASSISTANT/
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ services/
│  │  │   ├─ parser.py
│  │  │   ├─ quiz.py
│  │  │   ├─ rag.py
│  │  │   ├─ singleton.py 
│  │  │   └─ summary.py
│  │  ├─ routes/
│  │  │   ├─ __init__.py
│  │  │   ├─ challenge.py
│  │  │   ├─ qa.py
│  │  │   └─ upload.py
├─ frontend/
│  ├─ src/
│  │  ├─ components/
│  │  │   ├─ ChallengeMode.jsx
│  │  │   ├─ ChatInterface.jsx
│  │  │   ├─ DocumentSummary.jsx 
│  │  │   └─ DocumentUpload.jsx
│  │  ├─ context/
│  │  │   ├─ DocContext.jsx 
│  │  │   └─ ToastContext.jsx
|  ├─ vite.config.js
└─ └─ tailwind.config.js
```

---

## Contributing

Pull requests welcome! **Fork → Branch → PR**. Please open an issue for major changes.

```bash
git checkout -b feat/awesome-feature
# Commit & push, then open PR 🙌
```

---

> *Built with ❤️ by Shiva Pareek.*
