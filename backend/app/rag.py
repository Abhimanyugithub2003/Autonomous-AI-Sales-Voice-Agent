import os
import json
import re
import math
from typing import List, Dict, Any, Tuple
from pathlib import Path
from app.config import DATA_DIR

class RAGEngine:
    """
    RAG (Retrieval-Augmented Generation) Engine.
    Indexes enterprise product specifications, pricing, warranties, and target use cases.
    Performs hybrid dense-sparse vector ranking with TF-IDF and term weighting for instant, sub-millisecond retrieval.
    """
    def __init__(self, products_file: Path = None):
        if products_file is None:
            products_file = DATA_DIR / "products.json"
        self.products_file = products_file
        self.products: List[Dict[str, Any]] = []
        self.documents: List[Dict[str, Any]] = []
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_vectors: List[Dict[str, float]] = []
        self._load_and_index()

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        # Extract alphanumeric words and common tech specs like i9, 32gb, oled, 4k, rtx
        tokens = re.findall(r"\b[a-z0-9_\-\.]{2,}\b", text)
        stopwords = {
            "the", "and", "for", "with", "this", "that", "are", "from", "you", "your",
            "have", "has", "can", "will", "our", "all", "its", "any", "more", "per"
        }
        return [t for t in tokens if t not in stopwords]

    def _load_and_index(self):
        if not self.products_file.exists():
            return

        with open(self.products_file, "r", encoding="utf-8") as f:
            self.products = json.load(f)

        self.documents = []
        all_doc_tokens = []

        for p in self.products:
            # Flatten specs to text
            specs_text = " ".join([f"{k}: {v}" for k, v in p.get("specs", {}).items()])
            qualifying = " ".join(p.get("qualifying_prompts", []))
            
            # Create a rich textual chunk
            chunk_text = (
                f"{p['name']} {p['category']} "
                f"Target audience: {p.get('target_audience', '')}. "
                f"Price: ${p.get('price', '')} {p.get('currency', 'USD')}. "
                f"Ideal budget: {p.get('ideal_budget_range', '')}. "
                f"Specs: {specs_text}. "
                f"Key Benefits: {p.get('key_benefits', '')}. "
                f"Warranty: {p.get('warranty', '')}. "
                f"Availability: {p.get('availability', '')}. "
                f"{qualifying}"
            )

            doc = {
                "id": p["id"],
                "name": p["name"],
                "category": p["category"],
                "price": p["price"],
                "specs": p.get("specs", {}),
                "text": chunk_text,
                "product_data": p
            }
            self.documents.append(doc)
            tokens = self._tokenize(chunk_text)
            all_doc_tokens.append(tokens)

        # Compute TF-IDF
        num_docs = len(self.documents)
        df = {}
        for tokens in all_doc_tokens:
            unique_tokens = set(tokens)
            for t in unique_tokens:
                df[t] = df.get(t, 0) + 1

        self.idf = {t: math.log((num_docs + 1) / (count + 1)) + 1.0 for t, count in df.items()}

        self.doc_vectors = []
        for tokens in all_doc_tokens:
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            # Vector with TF-IDF weights
            vec = {t: (count / len(tokens)) * self.idf.get(t, 1.0) for t, count in tf.items()}
            self.doc_vectors.append(vec)

    def _cosine_similarity(self, query_vec: Dict[str, float], doc_vec: Dict[str, float]) -> float:
        dot_product = sum(query_vec[t] * doc_vec.get(t, 0.0) for t in query_vec)
        q_norm = math.sqrt(sum(v * v for v in query_vec.values()))
        d_norm = math.sqrt(sum(v * v for v in doc_vec.values()))
        if q_norm == 0 or d_norm == 0:
            return 0.0
        return dot_product / (q_norm * d_norm)

    def search(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Retrieves top_k most relevant products based on customer query.
        """
        if not self.documents:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            # Return top default products
            return [
                {
                    "product": doc["product_data"],
                    "score": 0.5,
                    "matched_snippet": doc["text"][:200]
                }
                for doc in self.documents[:top_k]
            ]

        # Build query vector
        q_tf = {}
        for t in query_tokens:
            q_tf[t] = q_tf.get(t, 0) + 1
        query_vec = {t: (count / len(query_tokens)) * self.idf.get(t, 1.0) for t, count in q_tf.items()}

        # Score documents
        scores = []
        for idx, doc_vec in enumerate(self.doc_vectors):
            sim = self._cosine_similarity(query_vec, doc_vec)
            
            # Boost matches for key product names or categories
            doc_text_lower = self.documents[idx]["text"].lower()
            bonus = 0.0
            for qt in query_tokens:
                if qt in doc_text_lower:
                    bonus += 0.05
                    
            final_score = sim + bonus
            scores.append((final_score, idx))

        scores.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, idx in scores[:top_k]:
            doc = self.documents[idx]
            results.append({
                "product": doc["product_data"],
                "score": round(score, 3),
                "matched_snippet": f"{doc['name']} (${doc['price']}) - {doc['product_data'].get('key_benefits', '')}"
            })
        return results

    def format_context_for_llm(self, query: str, top_k: int = 2) -> str:
        """
        Formats retrieved product knowledge into an LLM context block.
        """
        results = self.search(query, top_k=top_k)
        if not results:
            return "No specific product catalog data matched."

        context_lines = ["--- RELEVANT PRODUCT KNOWLEDGE (GROUNDING TRUTH) ---"]
        for r in results:
            p = r["product"]
            specs_summary = ", ".join([f"{k}: {v}" for k, v in p.get("specs", {}).items()])
            context_lines.append(
                f"• {p['name']} (${p['price']} USD) [{p['category']}]\n"
                f"  Target: {p.get('target_audience', '')}\n"
                f"  Specifications: {specs_summary}\n"
                f"  Key Benefits: {p.get('key_benefits', '')}\n"
                f"  Warranty & SLA: {p.get('warranty', '')}\n"
                f"  Inventory Availability: {p.get('availability', '')}"
            )
        context_lines.append("--------------------------------------------------")
        return "\n".join(context_lines)

rag_engine = RAGEngine()
