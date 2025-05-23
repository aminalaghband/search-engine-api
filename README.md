# Neural Web Search (DuckDuckGo + Neural Ranking)

A fully open-source neural web search engine that:
- Scrapes DuckDuckGo search results (no paid/closed APIs)
- Extracts content from web pages
- Embeds and ranks results using state-of-the-art neural models (bi-encoder + cross-encoder)
- Exposes everything via a FastAPI HTTP API
- Runs anywhere with Docker Compose and GPU support (NVIDIA)

---

## Features

- **DuckDuckGo Scraping**: Uses Playwright for robust, headless scraping.
- **Content Extraction**: Uses newspaper3k for main text extraction.
- **Neural Ranking**: Uses Sentence Transformers and Cross-Encoder models (GPU-accelerated).
- **API-First**: `/search` endpoint returns ranked web results.

---

## Quick Start

### 1. Prerequisites

- **NVIDIA GPU** (e.g. 4070) with [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) installed
- **Docker** and **Docker Compose** installed
- **Git** installed

### 2. Clone the Repository

```bash
git clone https://github.com/aminalaghband/search-engine-api.git
cd search-engine-api/neural-web-search
```

### 3. Install Playwright Browsers (one-time)

```bash
cd scraper
docker run --rm -v $(pwd):/app -w /app python:3.10 bash -c "pip install playwright && python -m playwright install chromium"
cd ..
```

### 4. Build and Run All Services

```bash
docker compose up --build
```

### 5. Test the API

curl:

```

---

## Project Structure

```
.
├── api/                # FastAPI API server
├── scraper/            # DuckDuckGo scraper & content extractor
├── embedder/           # Embedding & neural ranking service
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.scraper
├── Dockerfile.embedder
└── README.md
```

---

## API Usage

### `/search?q=QUERY`

- **Input:** Query string
- **Output:** Ranked list of URLs with neural scores

---

## Notes

- For best performance, use a machine with a modern NVIDIA GPU.
- You can customize models in `embedder/main.py` for even better results.

---

## License

MIT