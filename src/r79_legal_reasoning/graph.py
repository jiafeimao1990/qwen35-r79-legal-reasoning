from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any


def terms(text: str, limit: int = 96) -> list[str]:
    text = re.sub(r"\s+", " ", str(text))
    result = re.findall(r"[A-Za-z0-9_]{2,}", text.lower())
    for run in re.findall(r"[\u3400-\u9fff]+", text):
        result.extend(run[i : i + 2] for i in range(len(run) - 1))
    seen: set[str] = set()
    unique = []
    for term in result:
        if term not in seen:
            unique.append(term)
            seen.add(term)
        if len(unique) == limit:
            break
    return unique


def _fts_query(value: str) -> str:
    return " OR ".join('"' + term.replace('"', '""') + '"' for term in terms(value))


class ReasoningGraph:
    def __init__(self, path: Path):
        if not path.is_file():
            raise FileNotFoundError(path)
        self.path = path

    def _search(
        self, connection: sqlite3.Connection, query: str, limit: int = 40
    ) -> list[dict[str, Any]]:
        expression = _fts_query(query)
        if not expression:
            return []
        rows = connection.execute(
            """
            SELECT p.pattern_id, p.cluster_hash, p.public_json,
                   bm25(logic_fts, 4.0, 1.5, 1.0) AS score
            FROM logic_fts JOIN patterns p ON p.id = logic_fts.rowid
            WHERE logic_fts MATCH ? ORDER BY score LIMIT ?
            """,
            (expression, limit),
        ).fetchall()
        return [
            {
                "pattern_id": pattern_id,
                "cluster_hash": cluster_hash,
                "graph": json.loads(public_json)["graph"],
                "bm25": score,
            }
            for pattern_id, cluster_hash, public_json, score in rows
        ]

    def retrieve(self, full_input: str, question: str, limit: int = 3) -> list[dict[str, Any]]:
        if limit < 1 or limit > 3:
            raise ValueError("graph retrieval limit must be 1..3")
        connection = sqlite3.connect(f"file:{self.path.as_posix()}?mode=ro", uri=True)
        try:
            query_specs = [(full_input, 2.0), (question, 1.0)]
            fused: dict[str, dict[str, Any]] = {}
            for query, weight in query_specs:
                for rank, hit in enumerate(self._search(connection, query), start=1):
                    item = fused.setdefault(hit["pattern_id"], {**hit, "rrf": 0.0})
                    item["rrf"] += weight / (60 + rank)
            ranked = sorted(fused.values(), key=lambda row: (-row["rrf"], row["pattern_id"]))
            selected: list[dict[str, Any]] = []
            clusters: set[str] = set()
            for row in ranked:
                if row["cluster_hash"] in clusters:
                    continue
                clusters.add(row["cluster_hash"])
                selected.append(
                    {
                        "pattern_id": row["pattern_id"],
                        "graph": row["graph"],
                        "retrieval_score": row["rrf"],
                        "retrieval_score_kind": "weighted_rrf_not_confidence",
                    }
                )
                if len(selected) == limit:
                    break
            return selected
        finally:
            connection.close()
