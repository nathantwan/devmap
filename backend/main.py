from fastapi import FastAPI
from dotenv import load_dotenv
import requests
import os
from fastapi.middleware.cors import CORSMiddleware

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