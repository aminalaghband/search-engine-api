from fastapi import FastAPI, Query
from playwright.sync_api import sync_playwright
from newspaper import Article

app = FastAPI()

@app.get("/serp")
def serp(q: str = Query(...)):
    # Use Playwright to get DuckDuckGo results
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://duckduckgo.com/?q={q}")
        page.wait_for_selector("a.result__a", timeout=60000)  # 60 seconds
        print(page.content())
        links = page.eval_on_selector_all('a[data-testid="result-title-a"]', "els => els.map(e => e.href)")
        browser.close()
    return {"urls": links[:10]}

@app.get("/extract")
def extract(url: str = Query(...)):
    article = Article(url)
    article.download()
    article.parse()
    return {"text": article.text}
