from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path


def build_wiki_index(source_jsonl: Path, destination: Path) -> dict[str, object]:
    """Build a local retrieval-only index from a rights- and privacy-cleared JSONL corpus."""
    if destination.exists():
        raise FileExistsError(destination)
    rows = []
    for number, line in enumerate(source_jsonl.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        required = {"source_id", "title", "source_type", "full_original"}
        missing = required - value.keys()
        if missing:
            raise ValueError(f"line {number} missing {sorted(missing)}")
        text = str(value["full_original"])
        rows.append(
            (
                str(value["source_id"]),
                str(value["title"]),
                str(value["source_type"]),
                hashlib.sha256(text.encode("utf-8")).hexdigest(),
                text,
            )
        )
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError("duplicate source_id")
    destination.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(destination)
    try:
        connection.executescript(
            """
            PRAGMA journal_mode=DELETE;
            CREATE TABLE sources(
                id INTEGER PRIMARY KEY,
                source_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                source_type TEXT NOT NULL,
                text_sha256 TEXT NOT NULL,
                full_original TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE wiki_fts USING fts5(title, body, tokenize='unicode61');
            """
        )
        for row in rows:
            cursor = connection.execute(
                "INSERT INTO sources(source_id,title,source_type,text_sha256,full_original) VALUES(?,?,?,?,?)",
                row,
            )
            connection.execute(
                "INSERT INTO wiki_fts(rowid,title,body) VALUES(?,?,?)",
                (cursor.lastrowid, _search_tokens(row[1]), _search_tokens(row[4])),
            )
        connection.commit()
        connection.execute("PRAGMA query_only=ON")
        if connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0] != len(rows):
            raise RuntimeError("Wiki index count mismatch")
    finally:
        connection.close()
    return {"documents": len(rows), "path": str(destination)}


def _search_tokens(value: str) -> str:
    result = re.findall(r"[A-Za-z0-9_]{2,}", value.lower())
    for run in re.findall(r"[\u3400-\u9fff]+", value):
        result.extend(run[index : index + 2] for index in range(len(run) - 1))
    return " ".join(dict.fromkeys(result))
