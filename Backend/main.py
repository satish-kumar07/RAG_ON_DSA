#import requirements
import faiss
import pickle
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
import numpy as np
import time
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()
Embedding_URL = os.getenv("Embedding_URL")
LLM_URL = os.getenv("LLM_URL")

if not Embedding_URL:
    raise ValueError("Missing Embedding URL in env variables")
if not LLM_URL:
    raise ValueError("Missing LLM URL in env variables")

# Load constant file like faiss and pkl
faiss_file="DSAdataFaiss.faiss"
pkl_file="DSAdataPKL.pkl"

# Load FAISS index
index = faiss.read_index(faiss_file)

# Load metadata
with open(pkl_file, "rb") as f:
    metadata = pickle.load(f)

chunks = metadata["chunks"]

# Setup Embedding code function
def make_embed(query:str):

    payload={
        "text": query
    }
    headers={
        "Content-Type": "application/json"
    }

    response=requests.post(Embedding_URL,json=payload,headers=headers,timeout=30)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Embedding API Error: {response.text}"
        )

    try:
        res=response.json()
        embed=res["data"]
        embeddings=embed[0]

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Invalid response format from Embedding API"
        )

    return np.array([embeddings]).astype("float32")

# Search for match embeds
def search_embed(query,top_k=5):
    query_vector=make_embed(query)
    distance, indices=index.search(query_vector,top_k)

    results=[]
    for i in indices[0]:
        results.append({
            "DSA Points":chunks[i]
        })
    return results

def llm_process(query:str,results:str):
    prompt = f"""
    Question:
    {query}

    Context:
    {results}

    Give concise answer with steps and time complexity.
    """

    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a precise Data Structures and Algorithms expert. Always provide complete answers with full pseudo code and time complexity."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 300,
        "temperature": 0.3
    }

    headers={
        "Content-Type": "application/json"
    }

    response=requests.post(LLM_URL,json=payload,headers=headers,timeout=30)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"LLM API Error: {response.text}"
        )
    try:
        res=response.json()
        dec=res["response"]
        decision=dec

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Invalid response format from LLM API"
        )

    return decision

# FastAPI setup
app=FastAPI(title="DSA")

class Query(BaseModel):
    query: str


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change with frontend url
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "running"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)

@app.post("/start")
@app.post("/start/")
def start_process(query: Query):
    try:
        start = time.perf_counter()

        top_matchs=search_embed(query.query)
        retrieved="\n\n".join([item["DSA Points"] for item in top_matchs])
        decision_llm=llm_process(query.query,retrieved)

        t_time = time.perf_counter() - start

        return {
            
            "decision": decision_llm,
            "time": f"{t_time:.4f}s"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))