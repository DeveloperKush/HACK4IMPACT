import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer # Added for query embedding
from rag.dataprep import get_collection

load_dotenv()

CONFIDENCE_THRESHOLD = 38
TOP_K = 4
MODEL = "llama-3.3-70b-versatile"

# Lazy-load embedding model for the query
_embed_model = None
def _get_embedder():
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model

def retrieve(query: str, n: int = TOP_K) -> list[dict]:
    collection = get_collection()
    if collection.count() == 0: return []

    # NEW: We must embed the query text into a vector first
    query_vector = _get_embedder().encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_vector, # Query by vector, not text
        n_results=min(n, collection.count()),
    )

    chunks = []
    if results and results["documents"]:
        for i in range(len(results["documents"][0])):
            dist = results["distances"][0][i]
            # Convert L2 distance to a rough confidence %
            conf = round(max(0, 100 * (1 / (1 + dist))), 1)
            if conf >= CONFIDENCE_THRESHOLD:
                chunks.append({
                    "text": results["documents"][0][i],
                    "source": results["metadatas"][0][i].get("source", "Unknown"),
                    "confidence": conf
                })
    return chunks

import groq

_groq_client = None
def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        _groq_client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"))
    return _groq_client

def answer_with_rag(query: str, chunks: list[dict]) -> str:
    if not chunks:
        system_prompt = (
            "You are Jan-Sahayak's AI assistant. "
            "You must answer user queries helpfully but since you cannot find relevant local context, "
            "start your reply with: '[Note: I couldn't find specific official data for this, but here is my general knowledge] '. "
            "Then proceed with the answer."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        response = _get_groq_client().chat.completions.create(
            messages=messages,
            model=MODEL,
            temperature=0.7,
            max_tokens=600
        )
        return response.choices[0].message.content

    context = "\n\n".join([f"Source ({c['source']}) Confidence: {c['confidence']}%\n{c['text']}" for c in chunks])
    system_prompt = (
        "You are Jan-Sahayak's Fact Check Assistant.\n"
        "You are provided with a user query and relevant excerpts from official documents/schemes.\n"
        "Your job is to answer the query *only* using the provided excerpts.\n"
        "If the excerpts do not contain the answer, say so.\n"
        "Cite the sources where possible."
    )
    user_prompt = f"Context:\n{context}\n\nQuery: {query}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    response = _get_groq_client().chat.completions.create(
        messages=messages,
        model=MODEL,
        temperature=0.0,
        max_tokens=600
    )
    return response.choices[0].message.content

def fact_check(query: str) -> dict:
    chunks = retrieve(query, n=TOP_K)
    answer = answer_with_rag(query, chunks)
    
    best_conf = 0.0
    if chunks:
        best_conf = max(c["confidence"] for c in chunks)
    
    mode = "retrieval" if chunks else "llm_fallback"
    
    return {
        "query": query,
        "mode": mode,
        "answer": answer,
        "sources": list(set(c["source"] for c in chunks)),
        "best_confidence": best_conf,
        "chunks_used": len(chunks)
    }
