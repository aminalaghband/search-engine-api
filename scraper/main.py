from fastapi import FastAPI, Query, HTTPException
from playwright.sync_api import sync_playwright
from newspaper import Article
import logging
import time

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

def safe_close(resource):
    try:
        if resource:
            resource.close()
    except Exception as e:
        logger.warning(f"Cleanup warning: {str(e)}")

@app.get("/serp")
def serp(q: str = Query(..., min_length=2)):
    playwright = None
    browser = None
    context = None
    page = None
    
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--single-process"
            ],
            timeout=60000
        )
        
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1920, "height": 1080},
            java_script_enabled=True
        )
        
        page = context.new_page()
        logger.info(f"Searching DuckDuckGo for: {q}")
        
        # First try with standard wait
        try:
            page.goto(
                f"https://duckduckgo.com/?q={q}",
                wait_until="networkidle",
                timeout=60000
            )
        except:
            # Fallback to basic load
            page.goto(f"https://duckduckgo.com/?q={q}", timeout=60000)
            time.sleep(3)  # Allow time for JS execution

        # Multiple fallback selectors
        selectors = [
            '[data-testid="result"]',
            '.result',
            '.web-result',
            '#links',
            '#captcha'
        ]
        
        found = False
        for selector in selectors:
            try:
                page.wait_for_selector(
                    selector,
                    state="attached",
                    timeout=10000
                )
                found = True
                break
            except:
                continue
                
        if not found:
            raise Exception("No search results found")

        # Check for blocking
        if page.query_selector('#captcha, :text("DDoS"), :text("CAPTCHA")'):
            raise HTTPException(429, "Search blocked by provider")

        # Scroll and collect
        page.mouse.wheel(0, 500)
        time.sleep(1)
        
        links = page.eval_on_selector_all(
            'a[data-testid="result-title-a"], a.result__a, a.web-result__a',
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
            if page:
                page.screenshot(path="/app/error.png")
        except Exception as se:
            logger.error(f"Screenshot failed: {str(se)}")
        raise HTTPException(500, detail=f"Search failed: {str(e)}")
    finally:
        # Proper cleanup order
        if page:
            safe_close(page)
        if context:
            safe_close(context)
        if browser:
            safe_close(browser)
        if playwright:
            playwright.stop()

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