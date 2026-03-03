# rag/embedder.py
from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str) -> list:
    if not text:
        return [0.0] * 384
    return _model.encode(text).tolist()
