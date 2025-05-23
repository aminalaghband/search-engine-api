from fastapi import FastAPI, Query, HTTPException
from playwright.sync_api import sync_playwright
from newspaper import Article
import logging
import time

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

def create_browser():
    return sync_playwright().start().chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--single-process"
        ],
        timeout=60000
    )

@app.get("/serp")
def serp(q: str = Query(..., min_length=2)):
    playwright = None
    browser = None
    context = None
    page = None
    
    try:
        playwright = sync_playwright().start()
        browser = create_browser()
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()

        logger.info(f"Searching DuckDuckGo for: {q}")
        page.goto(f"https://duckduckgo.com/?q={q}", timeout=90000)

        # Wait for either search results or captcha
        try:
            page.wait_for_selector('article:has(a[data-testid="result-title-a"])', timeout=30000)
        except:
            page.wait_for_selector('#captcha, :text("DDoS")', timeout=5000)
            raise HTTPException(429, "Search blocked")

        # Scroll to trigger lazy loading
        for _ in range(3):
            page.mouse.wheel(0, 1000)
            time.sleep(0.5)

        # Extract results using multiple selector strategies
        links = page.query_selector_all('a[data-testid="result-title-a"], a.result__a')
        results = [{
            "url": link.get_attribute("href"),
            "title": link.text_content().strip()
        } for link in links if link.get_attribute("href")]

        return {"urls": [result["url"] for result in results[:10]]}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        if page:
            page.screenshot(path="/app/error.png")
        raise HTTPException(500, detail="Search service unavailable")
    finally:
        # Reverse resource cleanup
        for resource in [page, context, browser, playwright]:
            try:
                if resource:
                    resource.close()
            except Exception as e:
                logger.warning(f"Cleanup warning: {str(e)}")

@app.get("/extract")
def extract(url: str = Query(...)):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return {
            "url": url,
            "text": article.text[:5000],  # Limit text length
            "title": article.title,
        }
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Content extraction failed: {str(e)}"
        )

@app.get("/health")
def health():
    return {"status": "ok"}