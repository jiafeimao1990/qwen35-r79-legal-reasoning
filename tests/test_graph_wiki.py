from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from r79_legal_reasoning.graph import ReasoningGraph
from r79_legal_reasoning.wiki import SimilarCaseWiki
from r79_legal_reasoning.wiki_build import build_wiki_index


def _graph_db(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE patterns(id INTEGER PRIMARY KEY, pattern_id TEXT UNIQUE, cluster_hash TEXT, public_json TEXT);
        CREATE VIRTUAL TABLE logic_fts USING fts5(issue, logic, boundary, tokenize='unicode61');
        """
    )
    value = {
        "pattern_id": "GP1",
        "graph": {
            "abstract_issue": "送达日期不明时如何审查期限",
            "scope": "只审查期限",
            "nodes": [
                {
                    "id": "N1",
                    "kind": "condition",
                    "statement": "先核实送达日期",
                    "parents": [],
                    "operator": "ATOM",
                }
            ],
            "transfer_limits": ["日期未知时不得补写"],
        },
    }
    cursor = connection.execute(
        "INSERT INTO patterns(pattern_id,cluster_hash,public_json) VALUES(?,?,?)",
        ("GP1", "c1", json.dumps(value, ensure_ascii=False)),
    )
    connection.execute(
        "INSERT INTO logic_fts(rowid,issue,logic,boundary) VALUES(?,?,?,?)",
        (cursor.lastrowid, "送达日期 期限", "先核实送达日期", "日期未知不得补写"),
    )
    connection.commit()
    connection.close()


def test_graph_retrieval(tmp_path: Path) -> None:
    path = tmp_path / "graph.sqlite3"
    _graph_db(path)
    result = ReasoningGraph(path).retrieve("送达日期不明", "期限怎么算")
    assert result[0]["pattern_id"] == "GP1"
    assert result[0]["retrieval_score_kind"] == "weighted_rrf_not_confidence"


def test_wiki_is_retrieval_only(tmp_path: Path) -> None:
    source = tmp_path / "wiki.jsonl"
    source.write_text(
        json.dumps(
            {
                "source_id": "X1",
                "title": "送达期限",
                "source_type": "synthetic",
                "full_original": "送达日期缺失时不得补写期限起点。",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    database = tmp_path / "wiki.sqlite3"
    build_wiki_index(source, database)
    result = SimilarCaseWiki(database).search("送达期限")
    assert result["model_calls"] == 0
    assert result["automatic_inference_injection"] is False
    assert result["result"]["full_original"] == "送达日期缺失时不得补写期限起点。"


def test_missing_wiki_is_explicit(tmp_path: Path) -> None:
    result = SimilarCaseWiki(tmp_path / "absent.sqlite3").search("query")
    assert result["result"] is None
    assert "rights-cleared" in result["unavailable_reason"]
