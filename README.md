# RAG_ON_DSA (DSA Terminal Assistant)

This project is a **DSA learning assistant** that looks like a retro terminal in your browser and answers Data Structures & Algorithms questions using **RAG (Retrieval Augmented Generation)**.

Instead of relying only on an LLM’s memory, it first **retrieves relevant DSA notes** from a local vector database (FAISS), then uses that retrieved context to generate a more grounded answer.

### Who is this for?

- **Beginners** who want a simple “ask and learn” DSA helper with steps + time complexity.
- **Intermediate developers** who want to understand how a real RAG pipeline is wired end-to-end.
- **Advanced users** who want a small codebase they can extend (better UI formatting, new datasets, different embedding/LLM providers, caching, deployment).

### What’s inside?

- A **Django** web app that serves the terminal-like UI and exposes `POST /start/`
- A **FastAPI** backend that:
  - embeds your query (via an **Embedding API**)
  - retrieves top matching DSA chunks from **FAISS**
  - calls an **LLM API** to generate the final answer using the retrieved context

### One-minute architecture

Browser (Terminal UI)
-> Django (`/start/` proxy)
-> FastAPI (`/start` RAG)
-> Embedding API + FAISS + LLM API
-> Answer back to the UI

This guide starts from zero (setup + run) and goes up to advanced topics (architecture, customization, and rebuilding the vector index).

---

## 1) What you are building (high-level)

When you type a question in the browser:

1. Browser UI (`app/templates/index.html`) sends the question to Django `POST /start/`
2. Django (`app/views.py`) forwards the question to the FastAPI backend `POST /start`
3. FastAPI (`Backend/main.py`) does:
   - create an embedding for your question
   - FAISS similarity search over your DSA knowledge chunks
   - sends (question + retrieved context) to the LLM API
4. FastAPI returns JSON:
   - `decision` (answer)
   - `time` (latency)
5. Django returns JSON to the browser:
   - `answer` (mapped from `decision`)
   - `time`
6. UI prints the answer in the terminal-like output.

---

## 2) Repository structure

```
.
├─ app/                       # Django app
│  ├─ templates/
│  │  └─ index.html           # Terminal UI (JS fetch + effects)
│  ├─ views.py                # Django endpoints: home + ask proxy
│  └─ ...
├─ project/                   # Django project settings
│  ├─ settings.py             # DSA_BACKEND_START_URL is here
│  └─ urls.py                 # /, /start/, /ask/
├─ Backend/                   # FastAPI RAG service
│  ├─ main.py                 # RAG pipeline + /start endpoint
│  ├─ requirements.txt        # FastAPI deps
│  ├─ .env                    # LLM_URL + Embedding_URL
│  ├─ DSAdataFaiss.faiss      # FAISS index
│  ├─ DSAdataPKL.pkl          # Metadata (chunks)
│  └─ Text_to_Embeddings.ipynb# Notebook used to build embeddings/index
├─ db.sqlite3                 # Django database (not heavily used here)
└─ manage.py                  # Django entry
```

---

## 3) Requirements (beginner setup)

### 3.1 Install Python
- Install **Python 3.10+** (recommended).
- On Windows installer, check:
  - **Add python.exe to PATH**

### 3.2 Create and activate a virtual environment (Django side)
From the repo root (`d:\dsa-terminal-rag`):

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3.3 Install Django dependencies
This repo currently does **not** include a root-level `requirements.txt`.

Install at least:

```powershell
pip install django requests
```

If you later want to freeze dependencies:

```powershell
pip freeze > requirements.txt
```

### 3.4 Install backend dependencies (FastAPI service)
Open a second terminal and install backend deps:

```powershell
.\venv\Scripts\activate
pip install -r .\Backend\requirements.txt
```

Note:
- `faiss-cpu` can sometimes be tricky on Windows depending on Python version.
- If installation fails, try:
  - upgrading pip: `pip install -U pip`
  - using a compatible Python version (often 3.10/3.11 helps)

---

## 4) Configuration (very important)

### 4.1 FastAPI backend env (`Backend/.env`)
Backend reads 2 variables (see `Backend/main.py`):

- `Embedding_URL`
- `LLM_URL`

Example (already present in your repo):

```env
LLM_URL = "https://..."
Embedding_URL = "https://..."
```

**Rules**:
- Don’t commit secret keys in `.env` if your endpoints require auth.
- The backend will crash on startup if either variable is missing.

### 4.2 Django -> Backend URL (`project/settings.py`)
Django forwards questions to the backend using:

- `DSA_BACKEND_START_URL`

Default is:

```python
DSA_BACKEND_START_URL = os.getenv("DSA_BACKEND_START_URL", "http://127.0.0.1:8001/start")
```

**Recommended ports**:
- Django dev server: `http://127.0.0.1:8000`
- FastAPI backend: `http://127.0.0.1:8001`

If you change ports, update `DSA_BACKEND_START_URL` accordingly.

---

## 5) Running the project (step-by-step)

You must run **two servers**.

### 5.1 Start the FastAPI backend (Terminal 1)
From repo root:

```powershell
.\venv\Scripts\activate
python -m uvicorn Backend.main:app --host 127.0.0.1 --port 8001
```

Check:
- Open: `http://127.0.0.1:8001/`
- You should see: `{"status":"running"}`

### 5.2 Start the Django web app (Terminal 2)
From repo root:

```powershell
.\venv\Scripts\activate
python manage.py runserver 8000
```

Open the UI:
- `http://127.0.0.1:8000/`

### 5.3 Ask a question
Type something like:

- `what is stack`
- `explain binary search with time complexity`

You should see:
- a **Thinking...** indicator while it waits
- then the answer + time.

---

## 6) How the code works (beginner explanation)

### 6.1 Django URL routing (`project/urls.py`)
Routes:
- `GET /` -> `views.home` -> returns the HTML UI
- `POST /start/` -> `views.ask` -> proxy to FastAPI
- `POST /ask/` -> same as `/start/`

### 6.2 Django proxy endpoint (`app/views.py`)
What it does:
- reads form field `question`
- sends JSON to backend: `{ "query": question }`
- expects backend response JSON containing:
  - `decision`
  - `time`
- returns JSON to UI:
  - `{ "answer": decision, "time": ... }`

Why proxy through Django?
- Simplifies UI (same origin requests)
- Keeps backend URL configurable in Django settings

### 6.3 Frontend terminal UI (`app/templates/index.html`)
The UI:
- captures Enter key in the input
- appends the user command to the output
- shows a `Thinking...` effect while waiting
- calls `fetch("/start/", { method: "POST" ... })`
- prints the response

It also performs light output formatting:
- removes `*` characters from the response
- (optional) you can extend formatting to handle headings, code blocks, etc.

---

## 7) Backend RAG pipeline (intermediate)

All backend logic lives in `Backend/main.py`.

### 7.1 Data files
- `DSAdataFaiss.faiss` is the FAISS index (vector search)
- `DSAdataPKL.pkl` contains metadata including `chunks`

### 7.2 Creating embeddings
Function: `make_embed(query: str)`
- sends your text to `Embedding_URL`
- expects JSON like:
  - `{"data": [[...vector...]]}`
- returns a `float32` numpy array shaped like `[1, dims]`

### 7.3 Similarity search
Function: `search_embed(query, top_k=5)`
- embeds the query
- does: `index.search(query_vector, top_k)`
- maps results to DSA chunks

### 7.4 LLM generation
Function: `llm_process(query: str, results: str)`
- builds a prompt with:
  - Question
  - Retrieved context
- posts to `LLM_URL`
- expects JSON containing `response` (string)

### 7.5 FastAPI endpoint
`POST /start`:
- runs search + LLM
- returns:
  - `decision`: model output
  - `time`: elapsed time

---

## 8) Common issues & fixes (troubleshooting)

### 8.1 Django says: 502 Backend unavailable
Cause:
- FastAPI backend not running
- wrong `DSA_BACKEND_START_URL`

Fix:
- confirm backend is up: `http://127.0.0.1:8001/`
- verify `project/settings.py` uses `http://127.0.0.1:8001/start`

### 8.2 FastAPI crashes: Missing Embedding URL / Missing LLM URL
Cause:
- `Backend/.env` not found, or variables missing

Fix:
- ensure `Backend/.env` exists
- ensure it contains `Embedding_URL` and `LLM_URL`

### 8.3 FAISS / pickle file not found
Cause:
- running backend from wrong working directory

Fix:
- start uvicorn from repo root, or from `Backend/` but ensure files are reachable
- simplest: run exactly:
  - `python -m uvicorn Backend.main:app --port 8001`

### 8.4 CORS problems
This project calls Django -> FastAPI server-side, so CORS usually won’t block.
If you call FastAPI directly from the browser, you may need stricter CORS settings.

---

## 9) Customization (advanced)

### 9.1 Change number of retrieved chunks
In `Backend/main.py`:
- `search_embed(query, top_k=5)`
Change `top_k` to 3, 8, etc.

### 9.2 Change model behavior
In `llm_process()`:
- edit the system prompt
- adjust `max_tokens`, `temperature`

### 9.3 Improve UI formatting
In `app/templates/index.html`:
- you can add formatting for:
  - headings
  - code blocks
  - numbered steps

Tip (safety):
- If you inject HTML into `output.innerHTML`, ensure you control/sanitize content.

### 9.4 Rebuild the FAISS index (power user)
There is a notebook:
- `Backend/Text_to_Embeddings.ipynb`

Typical workflow:
1. Prepare your DSA dataset / notes
2. Generate embeddings for each chunk using the same `Embedding_URL`
3. Build a FAISS index
4. Save:
   - `.faiss` index
   - `.pkl` metadata with `chunks`

Because notebooks can vary, follow the notebook cells in order and verify:
- chunking logic
- embedding dimensions match FAISS index dimensions

---

## 10) API reference (quick)

### Django
- `GET /` -> HTML terminal
- `POST /start/` -> expects form-data field: `question`

### FastAPI
- `GET /` -> `{ "status": "running" }`
- `POST /start` -> body:

```json
{ "query": "what is stack" }
```

Response:

```json
{ "decision": "...answer...", "time": "0.1234s" }
```

---
#   U p d a t e d   f o r   d e p l o y m e n t   f i x  
 