from fastapi import FastAPI, Query, HTTPException
from playwright.sync_api import sync_playwright
from newspaper import Article
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

@app.get("/serp")
def serp(q: str = Query(..., min_length=2)):
    browser = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=USER_AGENT)
            page = context.new_page()
            
            logger.info(f"Searching DuckDuckGo for: {q}")
            page.goto(
                f"https://duckduckgo.com/?q={q}",
                wait_until="networkidle",
                timeout=60000
            )
            
            # Wait for search results to load
            page.wait_for_selector(
                'a[data-testid="result-title-a"]',
                state="attached",
                timeout=30000
            )
            
            # Extract all result links
            links = page.eval_on_selector_all(
                'a[data-testid="result-title-a"]',
                "els => els.map(e => ({"
                "  url: e.href,"
                "  title: e.innerText"
                "}))"
            )
            
            logger.info(f"Found {len(links)} results")
            return {"results": links[:10]}
            
    except Exception as e:
        logger.error(f"Error in SERP endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
    finally:
        if browser:
            browser.close()

@app.get("/extract")
def extract(url: str = Query(...)):
    try:
        logger.info(f"Extracting content from: {url}")
        article = Article(url)
        article.download()
        article.parse()
        
        if not article.text:
            raise HTTPException(
                status_code=400,
                detail="No text content found in article"
            )
            
        return {
            "url": url,
            "title": article.title,
            "text": article.text,
            "authors": article.authors,
            "publish_date": str(article.publish_date) if article.publish_date else None
        }
    except Exception as e:
        logger.error(f"Error in extraction endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )