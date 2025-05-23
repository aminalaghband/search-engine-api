from fastapi import FastAPI, Request
from sentence_transformers import SentenceTransformer, CrossEncoder
import torch
import numpy as np

app = FastAPI()
bi_encoder = SentenceTransformer("all-MiniLM-L6-v2", device="cuda")
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="cuda")

@app.post("/rank")
async def rank(request: Request):
    data = await request.json()
    query = data["query"]
    docs = data["docs"]

    # Step 1: Embed query and docs
    doc_texts = [d["text"] for d in docs]
    doc_embeddings = bi_encoder.encode(doc_texts, convert_to_tensor=True)
    query_embedding = bi_encoder.encode([query], convert_to_tensor=True)
    scores = torch.nn.functional.cosine_similarity(query_embedding, doc_embeddings)[0].cpu().numpy()

    # Step 2: Select top 5 for reranking
    top_idx = np.argsort(scores)[::-1][:5]
    top_docs = [docs[i] for i in top_idx]

    # Step 3: Cross-encoder reranking
    pairs = [[query, d["text"]] for d in top_docs]
    rerank_scores = cross_encoder.predict(pairs)
    reranked = sorted(zip(top_docs, rerank_scores), key=lambda x: x[1], reverse=True)

    return {"results": [{"url": d["url"], "score": float(s)} for d, s in reranked]}
