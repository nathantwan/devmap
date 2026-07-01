from fastapi import FastAPI
from dotenv import load_dotenv
import requests
import os
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
import hdbscan
import numpy as np
import base64
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

@app.get("/")
def root():
    return {"message": "DevMap API is running"}

# store embeddings in memory after clustering so can be reused
repo_embeddings_cache = {}

@app.get("/search")
def search_repo(owner: str, repo: str, query: str):
    cache_key = f"{owner}/{repo}"
    
    if cache_key not in repo_embeddings_cache:
        return {"error": "Run /cluster first to build the embeddings cache"}
    
    cached = repo_embeddings_cache[cache_key]
    paths = cached["paths"]
    embeddings = cached["embeddings"]
    
    query_embedding = model.encode([query])
    similarities = cosine_similarity(query_embedding, embeddings)[0]
    
    top_indices = similarities.argsort()[::-1][:5]
    
    results = [
        {"path": paths[i], "score": float(similarities[i])}
        for i in top_indices
    ]
    
    return {"results": results}

@app.get("/repo")
def get_repo_tree(owner: str, repo: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    nodes = []
    edges = []
    seen = set()

    for item in data.get("tree", []):
        path = item["path"]
        parts = path.split("/")

        # create a node for the file or folder
        for i, part in enumerate(parts):
            node_id = "/".join(parts[:i+1])

            if node_id not in seen:
                seen.add(node_id)
                nodes.append({
                    "id": node_id,
                    "label": part,
                    "type": "file" if i == len(parts) - 1 else "folder"
                })

            # create an edge from parent to child
            if i > 0:
                parent_id = "/".join(parts[:i])
                edge = {"source": parent_id, "target": node_id}
                if edge not in edges:
                    edges.append(edge)

    return {"nodes": nodes, "edges": edges}

@app.get("/churn")
def get_churn(owner: str, repo: str):
    churn = {}

    for page in range(1, 6):
        url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=20&page={page}"
        response = requests.get(url, headers=HEADERS)
        commits = response.json()

        if not isinstance(commits, list):
            break

        for commit in commits:
            sha = commit["sha"]
            detail_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
            detail = requests.get(detail_url, headers=HEADERS).json()

            for file in detail.get("files", []):
                filename = file["filename"]
                churn[filename] = churn.get(filename, 0) + 1

    return {"churn": churn}

@app.get("/cluster")
def cluster_files(owner: str, repo: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    code_files = [
        item for item in data.get("tree", [])
        if item["type"] == "blob" and item["path"].endswith((".py", ".js", ".ts", ".tsx", ".jsx"))
    ][:80]  # cap it so we don't blow through rate limits

    contents = []
    paths = []

    for file in code_files:
        file_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file['path']}"
        file_res = requests.get(file_url, headers=HEADERS).json()

        if "content" in file_res:
            try:
                decoded = base64.b64decode(file_res["content"]).decode("utf-8", errors="ignore")
                contents.append(decoded[:2000])  # cap content length per file
                paths.append(file["path"])
            except Exception:
                continue

    if len(contents) < 5:
        return {"error": "not enough code files to cluster"}

    embeddings = model.encode(contents)
    repo_embeddings_cache[f"{owner}/{repo}"] = {
        "paths": paths,
        "embeddings": embeddings
    }

    clusterer = hdbscan.HDBSCAN(min_cluster_size=2)
    labels = clusterer.fit_predict(embeddings)

    result = {}
    for path, label in zip(paths, labels):
        result[path] = int(label)

    return {"clusters": result}