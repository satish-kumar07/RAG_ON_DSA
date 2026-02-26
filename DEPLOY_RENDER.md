# Deploy DSA Terminal Assistant on Render

This guide walks you through deploying both the FastAPI backend and Django frontend on Render using a single repository.

---

## Prerequisites

- A free Render account (https://render.com)
- Your code pushed to a GitHub/GitLab repository
- Your external API URLs ready:
  - Embedding API URL
  - LLM API URL

---

## 1) Repository structure (already done)

Your repo should now include:

```
.
├─ Backend/
│  ├─ main.py                 # FastAPI app (port configurable via $PORT)
│  ├─ requirements.txt        # FastAPI deps
│  ├─ .env                    # Local only; do NOT commit to repo
│  ├─ DSAdataFaiss.faiss
│  ├─ DSAdataPKL.pkl
│  └─ Text_to_Embeddings.ipynb
├─ project/
│  ├─ settings.py             # Now reads ALLOWED_HOSTS, DEBUG, DSA_BACKEND_START_URL from env
│  └─ urls.py
├─ app/
│  ├─ views.py
│  └─ templates/
│     └─ index.html
├─ requirements.txt           # Django deps for Render
├─ render.yaml                # Defines two services: backend + frontend
└─ .gitignore
```

---

## 2) Push your code to GitHub/GitLab

If you haven’t already:

```bash
git init
git add .
git commit -m "Prepare for Render deployment"
git branch -M main
git remote add origin <YOUR_REPO_URL>
git push -u origin main
```

---

## 3) Create Render services from repo

1. Log in to Render and click **New +** → **Web Service**
2. Choose your repository
3. Render will detect `render.yaml` and propose to create both services:
   - `dsa-backend`
   - `dsa-frontend`
4. Click **Create Web Services**

Render will build and deploy both services.

---

## 4) Set environment variables

### Backend (`dsa-backend`)
Go to your backend service → Environment → Add Environment Variable:

- `Embedding_URL`: your embedding endpoint
- `LLM_URL`: your LLM endpoint

### Frontend (`dsa-frontend`)
Render already set these via `render.yaml`, but verify:

- `DSA_BACKEND_START_URL`: should point to your backend URL, e.g.
  ```
  https://dsa-backend.onrender.com/start
  ```
- `ALLOWED_HOSTS`: should be the frontend URL, e.g.
  ```
  https://dsa-frontend.onrender.com
  ```
- `DEBUG`: `false`

---

## 5) Verify deployment

- Backend health: `https://dsa-backend.onrender.com/` → `{"status":"running"}`
- Frontend UI: `https://dsa-frontend.onrender.com/` → DSA Terminal UI

Try a question in the UI. You should see:
- “Thinking...” while it waits
- Answer + time

---

## 6) Common issues & fixes

### 6.1 Backend returns 500
- Check backend service logs (Render dashboard)
- Ensure `Embedding_URL` and `LLM_URL` are correct and reachable
- Ensure FAISS/PKL files are present in the repo (or switch to Render Disk if they are large)

### 6.2 Frontend 502 Bad Gateway
- Ensure `DSA_BACKEND_START_URL` is correct and points to the backend
- Ensure backend service is Running and not crashed

### 6.3 ALLOWED_HOSTS error
- Make sure `ALLOWED_HOSTS` env var includes the frontend URL
- Example value: `https://dsa-frontend.onrender.com`

### 6.4 FAISS/PKL too large for repo (> 100 MB)
- Use Render Disk to store them:
  - Add a Disk to your backend service
  - Modify `Backend/main.py` to load files from the disk path
  - Upload files via Render’s “SSH into service” or build step

---

## 7) Custom domains (optional)

- In Render dashboard, go to each service → Custom Domains
- Add your domain (e.g., `dsa.yourdomain.com`)
- Update DNS as instructed by Render
- Update `ALLOWED_HOSTS` and CORS origins if needed

---

## 8) Scaling beyond free tier

- If you need more CPU/memory, upgrade the service plans
- For high traffic, consider:
  - Adding caching (Redis on Render)
  - Using a managed vector DB instead of local FAISS
  - Adding a CDN for static assets

---

## 9) Summary of what Render does

- **Backend**: runs `uvicorn Backend.main:app` on $PORT, health at `/`
- **Frontend**: runs `gunicorn project.wsgi:application` on $PORT
- Environment variables are injected at runtime
- Zero-downtime deploys when you push to the main branch

---

## 10) After deployment

- Your app will be live at the frontend URL
- You can share the link; no local servers needed
- To update, just push new commits to your repo; Render will auto-deploy

---

### Need help?

- Check Render service logs
- Compare your repo to the structure above
- Make sure env vars match exactly (no extra spaces/quotes)

Happy deploying! 🚀
