from fastapi import FastAPI
from dotenv import load_dotenv
import requests
import os

load_dotenv()

app = FastAPI()

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