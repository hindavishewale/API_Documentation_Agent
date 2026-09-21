from __future__ import annotations

class RAGRetriever:
    def __init__(self, documents: list[str] | None = None):
        self.documents = documents or []
        self.available = False
        try:
            import faiss  # noqa: F401
            from sentence_transformers import SentenceTransformer  # noqa: F401
            self.available = bool(self.documents)
        except ImportError:
            self.available = False

    def retrieve(self, query: str, limit: int = 3) -> list[str]:
        if not self.documents:
            return []
        terms = set(query.lower().split())
        ranked = sorted(self.documents, key=lambda doc: len(terms & set(doc.lower().split())), reverse=True)
        return ranked[:limit]
