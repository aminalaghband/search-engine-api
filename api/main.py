from fastapi import FastAPI, Query, HTTPException
import requests
import logging
from typing import List, Dict

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCRAPER_URL = "http://scraper:9000"
EMBEDDER_URL = "http://embedder:9100"

@app.get("/search")
def search(q: str = Query(..., description="Search query")):
    try:
        # 1. Get SERP links with error handling
        try:
            serp_response = requests.get(
                f"{SCRAPER_URL}/serp",
                params={"q": q},
                timeout=10  # Fail fast if scraper is down
            )
            serp_response.raise_for_status()
            serp_data = serp_response.json()
            urls = serp_data.get("urls", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"SERP API error: {str(e)}")
            raise HTTPException(status_code=502, detail="Search results service unavailable")
        except KeyError:
            logger.error("Invalid SERP response format")
            raise HTTPException(status_code=502, detail="Invalid search results format")

        # 2. Content extraction with parallel processing
        contents: List[Dict] = []
        for url in urls[:5]:  # Limit to top 5 URLs for demo
            try:
                extract_response = requests.get(
                    f"{SCRAPER_URL}/extract",
                    params={"url": url},
                    timeout=15
                )
                extract_response.raise_for_status()
                content = extract_response.json()
                if content.get("text"):
                    contents.append({
                        "url": url,
                        "text": content["text"][:5000]  # Limit text length
                    })
            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to extract {url}: {str(e)}")
                continue

        if not contents:
            raise HTTPException(status_code=404, detail="No extractable content found")

        # 3. Ranking with error handling
        try:
            rank_response = requests.post(
                f"{EMBEDDER_URL}/rank",
                json={"query": q, "docs": contents},
                timeout=20
            )
            rank_response.raise_for_status()
            return rank_response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ranking API error: {str(e)}")
            raise HTTPException(status_code=503, detail="Ranking service unavailable")

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")