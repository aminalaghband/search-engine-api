from fastapi import FastAPI, Query
import requests

app = FastAPI()

SCRAPER_URL = "http://scraper:9990"
EMBEDDER_URL = "http://embedder:9190"

@app.get("/search")
def search(q: str = Query(..., description="Search query")):
    # 1. Get SERP links
    serp = requests.get(f"{SCRAPER_URL}/serp", params={"q": q}).json()
    urls = serp["urls"]

    # 2. Extract content
    contents = []
    for url in urls:
        r = requests.get(f"{SCRAPER_URL}/extract", params={"url": url})
        if r.status_code == 200:
            contents.append({"url": url, "text": r.json()["text"]})

    # 3. Rank with embedder
    ranked = requests.post(f"{EMBEDDER_URL}/rank", json={"query": q, "docs": contents}).json()
    return ranked
