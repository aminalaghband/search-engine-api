from fastapi import FastAPI, Query, HTTPException
from playwright.sync_api import sync_playwright
from newspaper import Article
import logging
import time

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

@app.get("/serp")
def serp(q: str = Query(..., min_length=2)):
    browser = None
    context = None
    page = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )
            
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1920, "height": 1080}
            )
            
            page = context.new_page()
            
            logger.info(f"Searching DuckDuckGo for: {q}")
            page.goto(
                f"https://duckduckgo.com/?q={q}",
                wait_until="networkidle",
                timeout=60000
            )

            # Wait for main container
            page.wait_for_selector(
                '[data-testid="results"], #links, .results, #captcha',
                state="attached",
                timeout=45000
            )
            
            # Check for blocking pages
            if page.query_selector(':text("DDoS"), :text("CAPTCHA")'):
                raise HTTPException(429, "Search blocked by provider")

            # Scroll and collect results
            page.mouse.wheel(0, 2000)
            time.sleep(2)
            
            links = page.eval_on_selector_all(
                '[data-testid="result-title-a"], a.result__a',
                """els => els.map(e => ({
                    url: e.href,
                    title: e.innerText
                }))"""
            )
            
            return {"urls": [link["url"] for link in links[:10]]}
            
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        try:
            if page and not page.is_closed():
                page.screenshot(path="/app/error.png")
        except Exception as se:
            logger.error(f"Screenshot failed: {se}")
        raise HTTPException(500, detail=f"Search failed: {str(e)}")
    finally:
        cleanup_order = [page, context, browser]
        for resource in cleanup_order:
            try:
                if resource and not resource.is_closed():
                    resource.close()
            except Exception as ce:
                logger.warning(f"Cleanup error: {ce}")

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