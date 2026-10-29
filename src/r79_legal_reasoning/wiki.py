from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .graph import _fts_query


class SimilarCaseWiki:
    """Retrieval-only sidecar. It never calls or feeds a model."""

    def __init__(self, path: Path):
        self.path = path

    @property
    def available(self) -> bool:
        return self.path.is_file()

    def search(self, query: str) -> dict[str, Any]:
        if not query or not query.strip():
            raise ValueError("query must not be blank")
        if len(query) > 8000:
            raise ValueError("query exceeds 8000 characters")
        if not self.available:
            return {
                "mode": "retrieval_only",
                "model_calls": 0,
                "result": None,
                "unavailable_reason": "No rights-cleared Wiki index is installed. See docs/DATA.md.",
            }
        expression = _fts_query(query)
        connection = sqlite3.connect(f"file:{self.path.as_posix()}?mode=ro", uri=True)
        try:
            row = connection.execute(
                """
                SELECT s.source_id, s.title, s.source_type, s.text_sha256, s.full_original,
                       bm25(wiki_fts, 4.0, 1.0) AS score
                FROM wiki_fts JOIN sources s ON s.id = wiki_fts.rowid
                WHERE wiki_fts MATCH ? ORDER BY score LIMIT 1
                """,
                (expression,),
            ).fetchone()
            if row is None:
                result = None
            else:
                source_id, title, source_type, text_sha256, full_original, score = row
                result = {
                    "source_id": source_id,
                    "title": title,
                    "source_type": source_type,
                    "text_sha256": text_sha256,
                    "full_original": full_original,
                    "complete": True,
                    "retrieval_score": score,
                    "retrieval_score_kind": "bm25_not_confidence",
                }
            return {
                "mode": "retrieval_only",
                "model_calls": 0,
                "reasoning_used": False,
                "automatic_inference_injection": False,
                "query": query,
                "result": result,
            }
        finally:
            connection.close()
