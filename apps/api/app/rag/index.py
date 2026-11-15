import math
import os
import re
from typing import Any


class LocalRAGIndex:
    """Zero-cost, local TF-IDF / BM25 lexical vector index for runbook retrieval.

    Guarantees deterministic Recall@k without requiring external APIs or heavy C-extensions.
    """

    def __init__(self, runbook_dir: str = "runbooks"):
        self.runbook_dir = runbook_dir
        self.documents: list[dict[str, Any]] = []
        self.vocab: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.doc_vectors: list[dict[str, float]] = []
        self._build_index()

    def _tokenize(self, text: str) -> list[str]:
        tokens = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())
        return tokens

    def _build_index(self) -> None:
        if not os.path.exists(self.runbook_dir):
            return

        doc_tokens_list: list[list[str]] = []
        files = sorted(os.listdir(self.runbook_dir))

        for fname in files:
            if not fname.endswith(".md"):
                continue
            path = os.path.join(self.runbook_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            tokens = self._tokenize(content)
            doc_tokens_list.append(tokens)
            self.documents.append({
                "id": fname,
                "path": path,
                "content": content,
                "title": content.splitlines()[0] if content else fname,
            })

        n_docs = len(self.documents)
        if n_docs == 0:
            return

        # Calculate Document Frequencies (DF)
        df: dict[str, int] = {}
        for tokens in doc_tokens_list:
            unique_tokens = set(tokens)
            for t in unique_tokens:
                df[t] = df.get(t, 0) + 1

        # Calculate Inverse Document Frequency (IDF)
        for t, freq in df.items():
            self.idf[t] = math.log((n_docs + 1) / (freq + 1)) + 1.0

        # Build TF-IDF vectors
        for tokens in doc_tokens_list:
            tf: dict[str, float] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            length = len(tokens) or 1
            vec: dict[str, float] = {}
            norm_sq = 0.0
            for t, count in tf.items():
                val = (count / length) * self.idf.get(t, 1.0)
                vec[t] = val
                norm_sq += val * val
            norm = math.sqrt(norm_sq) or 1.0
            self.doc_vectors.append({t: v / norm for t, v in vec.items()})

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        tokens = self._tokenize(query)
        if not tokens or not self.documents:
            return []

        # Build query vector
        q_tf: dict[str, float] = {}
        for t in tokens:
            q_tf[t] = q_tf.get(t, 0) + 1
        q_len = len(tokens) or 1
        q_vec: dict[str, float] = {}
        norm_sq = 0.0
        for t, count in q_tf.items():
            val = (count / q_len) * self.idf.get(t, 1.0)
            q_vec[t] = val
            norm_sq += val * val
        norm = math.sqrt(norm_sq) or 1.0
        q_norm_vec = {t: v / norm for t, v in q_vec.items()}

        # Compute Cosine Similarities
        scores: list[tuple[float, int]] = []
        for idx, doc_vec in enumerate(self.doc_vectors):
            score = 0.0
            for t, q_val in q_norm_vec.items():
                if t in doc_vec:
                    score += q_val * doc_vec[t]
            scores.append((score, idx))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, idx in scores[:top_k]:
            doc = self.documents[idx]
            results.append({
                "id": doc["id"],
                "title": doc["title"],
                "score": round(score, 4),
                "content": doc["content"],
            })
        return results

rag_index = LocalRAGIndex()
