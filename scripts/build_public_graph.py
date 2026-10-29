#!/usr/bin/env python3
"""Build the public-only reasoning-graph SQLite database."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

FORBIDDEN_KEYS = {
    "private_json",
    "private_provenance",
    "node_provenance",
    "reasoning_content",
    "source_path",
    "source_snapshot",
}


def walk(value, location="$") -> None:
    if isinstance(value, dict):
        leaked = FORBIDDEN_KEYS.intersection(value)
        if leaked:
            raise ValueError(f"private key at {location}: {sorted(leaked)}")
        for key, child in value.items():
            walk(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk(child, f"{location}[{index}]")


def tokens(value: str) -> str:
    result = re.findall(r"[A-Za-z0-9_]{2,}", value.lower())
    for run in re.findall(r"[\u3400-\u9fff]+", value):
        result.extend(run[index : index + 2] for index in range(len(run) - 1))
    return " ".join(dict.fromkeys(result))


def searchable(graph: dict) -> tuple[str, str, str]:
    issue = tokens(str(graph.get("abstract_issue", "")))
    nodes = tokens("\n".join(str(node.get("statement", "")) for node in graph.get("nodes", [])))
    boundary = tokens("\n".join(str(item) for item in graph.get("transfer_limits", [])))
    return issue, nodes, boundary


def build(source: Path, destination: Path) -> int:
    if destination.exists():
        raise FileExistsError(destination)
    rows = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if set(row) != {"pattern_id", "cluster_hash", "public"}:
            raise ValueError(f"unexpected keys at line {line_number}: {sorted(row)}")
        walk(row)
        public = row["public"]
        if public.get("pattern_id") != row["pattern_id"]:
            raise ValueError(f"pattern ID mismatch at line {line_number}")
        rows.append(row)
    if len({row["pattern_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate pattern ID")
    destination.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(destination)
    try:
        connection.executescript(
            """
            PRAGMA journal_mode=DELETE;
            CREATE TABLE patterns(
                id INTEGER PRIMARY KEY,
                pattern_id TEXT UNIQUE NOT NULL,
                cluster_hash TEXT NOT NULL,
                public_json TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE logic_fts USING fts5(issue, logic, boundary, tokenize='unicode61');
            """
        )
        for row in rows:
            public_json = json.dumps(row["public"], ensure_ascii=False, separators=(",", ":"))
            cursor = connection.execute(
                "INSERT INTO patterns(pattern_id,cluster_hash,public_json) VALUES(?,?,?)",
                (row["pattern_id"], row["cluster_hash"], public_json),
            )
            issue, logic, boundary = searchable(row["public"]["graph"])
            connection.execute(
                "INSERT INTO logic_fts(rowid,issue,logic,boundary) VALUES(?,?,?,?)",
                (cursor.lastrowid, issue, logic, boundary),
            )
        connection.commit()
        if connection.execute("SELECT COUNT(*) FROM patterns").fetchone()[0] != len(rows):
            raise RuntimeError("graph count mismatch")
        if connection.execute("SELECT COUNT(*) FROM logic_fts").fetchone()[0] != len(rows):
            raise RuntimeError("FTS count mismatch")
    finally:
        connection.close()
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps({"patterns": build(args.input, args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
