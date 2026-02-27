# RAG_ON_DSA (DSA Terminal Assistant)

This project is a **DSA learning assistant** designed as a retro-style terminal in the browser. It answers Data Structures and Algorithms questions using a **Retrieval-Augmented Generation (RAG)** pipeline.

Instead of relying only on an LLM’s internal knowledge, the system:

1. Retrieves relevant DSA notes from a local **FAISS vector database**
2. Sends the retrieved context along with the user’s query to an LLM
3. Returns a grounded, context-aware answer

---

## Who Is This For?

* **Beginners** who want a simple DSA helper with explanations and time complexity.
* **Intermediate developers** who want to understand a real RAG pipeline end-to-end.
* **Advanced users** who want an extendable codebase (UI improvements, dataset upgrades, provider switching, deployment, caching, etc.).

---

# Architecture Overview

### Request Flow

```
Browser (Terminal UI)
        ↓
Django (POST /start/)
        ↓
FastAPI Backend (POST /start)
        ↓
Embedding API + FAISS + LLM API
        ↓
Response Returned to UI
```

Django acts as a proxy layer between the browser and the RAG backend.

---

# Repository Structure

```
.
├─ app/                      # Django app
│  ├─ templates/
│  │   └─ index.html         # Terminal UI
│  ├─ views.py               # Proxy endpoints
│  └─ ...
├─ project/                  # Django project config
│  ├─ settings.py
│  └─ urls.py
├─ Backend/                  # FastAPI RAG backend
│  ├─ main.py                # RAG pipeline
│  ├─ requirements.txt
│  ├─ .env
│  ├─ DSAdataFaiss.faiss
│  ├─ DSAdataPKL.pkl
│  └─ Text_to_Embeddings.ipynb
├─ db.sqlite3
└─ manage.py
```

---

# Local Development Setup

## 1. Install Python

Use Python **3.10 or 3.11** (recommended for FAISS compatibility).

---

## 2. Create Virtual Environment

From project root:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

---

## 3. Install Dependencies

### Django Side

```powershell
pip install django requests
```

(Optional)

```powershell
pip freeze > requirements.txt
```

---

### Backend (FastAPI) Side

```powershell
pip install -r .\Backend\requirements.txt
```

If FAISS fails:

* Upgrade pip: `pip install -U pip`
* Ensure Python 3.10/3.11

---

# Configuration

## Backend Environment (`Backend/.env`)

```
LLM_URL="https://your-llm-endpoint"
Embedding_URL="https://your-embedding-endpoint"
```

Both variables are required or the backend will fail at startup.

---

## Django Backend URL (`project/settings.py`)

```python
DSA_BACKEND_START_URL = os.getenv(
    "DSA_BACKEND_START_URL",
    "http://127.0.0.1:8001/start"
)
```

Default ports:

* Django → 8000
* FastAPI → 8001

---

# Running Locally

You must run **two servers**.

---

## Start FastAPI Backend

```powershell
python -m uvicorn Backend.main:app --host 127.0.0.1 --port 8001
```

Test:

```
http://127.0.0.1:8001/
```

Expected:

```json
{"status":"running"}
```

---

## Start Django Server

```powershell
python manage.py runserver 8000
```

Open:

```
http://127.0.0.1:8000/
```

---

# Deployment Guide (Production-Ready Fix)

The most common issue during deployment (especially on Render) is:

> Root directory misconfiguration
> Backend server not starting
> Gunicorn not pointing to correct WSGI
> Uvicorn not exposing correct port

Below is the correct approach.

---

# Deploying Django (Render Example)

### 1. Root Directory

If deploying from GitHub:

Set **Root Directory = repository root**, NOT:

```
/Backend/
```

Your Django app runs from project root where `manage.py` exists.

---

### 2. Add Production Dependencies

Create root-level `requirements.txt` including:

```
django
gunicorn
requests
```

---

### 3. Add Procfile (Important)

Create a file named:

```
Procfile
```

Content:

```
web: gunicorn project.wsgi:application
```

Replace `project` with your actual Django project folder name.

---

### 4. Set Environment Variables in Render

Add:

```
DSA_BACKEND_START_URL = https://your-backend-url/start
```

If backend is deployed separately.

---

# Deploying FastAPI Backend (Render Example)

Deploy backend as a separate service.

### Root Directory

Set:

```
Backend
```

NOT repository root.

---

### Start Command

```
uvicorn main:app --host 0.0.0.0 --port 10000
```

Use:

```
$PORT
```

If required by platform:

```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

### Add Backend Procfile (Optional)

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

### Add Environment Variables

In backend service dashboard:

```
LLM_URL=...
Embedding_URL=...
```

---

# Important Deployment Fix Notes

### 1. Use 0.0.0.0 in Production

Never use:

```
127.0.0.1
```

Use:

```
0.0.0.0
```

For external access.

---

### 2. Use Environment Port

Most platforms require:

```
--port $PORT
```

Not hardcoded 8001.

---

### 3. Update Django Backend URL

After backend deployment:

```python
DSA_BACKEND_START_URL = "https://your-backend-service.onrender.com/start"
```

---

# API Reference

## Django

### GET /

Returns terminal UI

### POST /start/

Form field:

```
question
```

Returns:

```json
{
  "answer": "...",
  "time": "0.123s"
}
```

---

## FastAPI

### GET /

```json
{"status":"running"}
```

### POST /start

Body:

```json
{
  "query": "what is stack"
}
```

Response:

```json
{
  "decision": "...answer...",
  "time": "0.123s"
}
```

---

# Customization

### Change Retrieval Depth

In `Backend/main.py`:

```python
search_embed(query, top_k=5)
```

Modify `top_k`.

---

### Modify LLM Prompt

Edit `llm_process()` system instructions.

---

### Improve UI Formatting

Modify:

```
app/templates/index.html
```

Add:

* Code block rendering
* Heading detection
* Syntax formatting

---

# Rebuilding FAISS Index

Use:

```
Backend/Text_to_Embeddings.ipynb
```

Steps:

1. Load dataset
2. Chunk text
3. Generate embeddings
4. Build FAISS index
5. Save:

   * `.faiss`
   * `.pkl`

Ensure embedding dimension matches FAISS index dimension.

---

# Final Notes

This project demonstrates:

* Full-stack Django + FastAPI integration
* Practical RAG implementation
* FAISS-based semantic search
* Production-ready architecture
