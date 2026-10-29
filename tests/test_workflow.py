from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import jsonschema

from r79_legal_reasoning.settings import Settings
from r79_legal_reasoning.workflow import (
    FACT_SCHEMA,
    LegalWorkflow,
    Material,
    _normalize_final_graph_refs,
    _validate_facts,
)


class FakeClient:
    def __init__(self):
        self.native_requests = 0
        self.adapters = []

    def bounded_two_stage(self, *, adapter, label, **kwargs):
        self.native_requests += 2
        self.adapters.append(adapter)
        if label == "facts_1949":
            return {
                "actors": [
                    {
                        "actor_id": "A001",
                        "name_as_stated": "甲",
                        "role": "申请人",
                        "evidence_status": "asserted",
                        "source_refs": ["M001:P0001"],
                    }
                ],
                "events": [
                    {
                        "event_id": "E001",
                        "actor_ids": ["A001"],
                        "action": "提交",
                        "object": "材料",
                        "date_text": "",
                        "date_status": "unknown",
                        "evidence_status": "asserted",
                        "source_refs": ["M001:P0001"],
                    }
                ],
                "evidence": [
                    {
                        "evidence_id": "EV001",
                        "description": "材料A",
                        "supports_event_ids": ["E001"],
                        "status": "asserted",
                        "source_refs": ["M001:P0001"],
                    }
                ],
                "uncertainties": [
                    {"field": "日期", "reason": "未载明", "source_refs": ["M001:P0001"]}
                ],
            }
        if label == "procedure_1978":
            return {
                "actors": [
                    {
                        "actor_id": "A001",
                        "name_as_stated": "甲",
                        "role": "行为作出者",
                        "evidence_status": "asserted",
                        "source_refs": ["M001:P0001"],
                    }
                ],
                "decision_maker_actor_id": "A001",
                "challenged_action": {
                    "event_id": "E001",
                    "actor_id": "A001",
                    "description": "通知",
                    "evidence_status": "asserted",
                    "source_refs": ["M001:P0001"],
                },
                "steps": [],
                "deadlines": [],
                "unknowns": [{"field": "送达", "reason": "未知", "source_refs": ["M001:P0001"]}],
            }
        return {
            "conclusion": "待核实",
            "analysis": "日期未知。",
            "claims": [
                {
                    "claim": "日期未知",
                    "source_refs": ["M001:P0001"],
                    "graph_refs": [],
                    "evidence_status": "unknown",
                }
            ],
            "limitations": ["送达日期缺失"],
        }


def _empty_graph(path: Path, manifest: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE patterns(id INTEGER PRIMARY KEY, pattern_id TEXT UNIQUE, cluster_hash TEXT, public_json TEXT);
        CREATE VIRTUAL TABLE logic_fts USING fts5(issue, logic, boundary, tokenize='unicode61');
        """
    )
    connection.close()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest.write_text(json.dumps({"public_database_sha256": digest}), encoding="utf-8")


def test_three_routes_and_six_generation_requests(tmp_path: Path) -> None:
    graph = tmp_path / "graph.sqlite3"
    manifest = tmp_path / "GRAPH_MANIFEST.json"
    _empty_graph(graph, manifest)
    settings = Settings(
        graph_db=graph,
        graph_manifest=manifest,
        audit_dir=tmp_path / "audit",
    )
    fake = FakeClient()
    result = LegalWorkflow(settings, fake).run("是否合法", [Material("材料A", "日期残缺")])
    assert result["backend_generation_requests"] == 6
    assert fake.adapters == ["facts_1949", "procedure_1978", "candidate_r79"]
    assert result["routing"]["wiki_injected"] is False


def test_fact_foreign_keys_fail_closed() -> None:
    bad = {
        "actors": [
            {
                "actor_id": "A001",
                "name_as_stated": "甲",
                "role": "申请人",
                "evidence_status": "asserted",
                "source_refs": ["M001:P0001"],
            }
        ],
        "events": [
            {
                "event_id": "E001",
                "actor_ids": ["A999"],
                "action": "提交",
                "object": "材料",
                "date_text": "",
                "date_status": "unknown",
                "evidence_status": "asserted",
                "source_refs": ["M001:P0001"],
            }
        ],
        "evidence": [
            {
                "evidence_id": "EV001",
                "description": "材料",
                "supports_event_ids": ["E001"],
                "status": "asserted",
                "source_refs": ["M001:P0001"],
            }
        ],
        "uncertainties": [],
    }
    try:
        _validate_facts(bad)
    except RuntimeError as exc:
        assert "unknown actors" in str(exc)
    else:
        raise AssertionError("unknown actor foreign key was not rejected")


def test_fact_schema_rejects_malformed_ids() -> None:
    malformed_actor = {
        "actor_id": "],",
        "name_as_stated": "甲",
        "role": "申请人",
        "evidence_status": "asserted",
        "source_refs": ["M001:P0001"],
    }
    try:
        jsonschema.validate(malformed_actor, FACT_SCHEMA["properties"]["actors"]["items"])
    except jsonschema.ValidationError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("malformed actor ID was not rejected")


def test_graph_ref_prefix_is_restored_only_for_allowed_node() -> None:
    value = {
        "claims": [
            {
                "graph_refs": ["GP_001:N1", "G:GP_001:N1", "UNKNOWN:N9"],
            }
        ]
    }
    report = _normalize_final_graph_refs(value, {"G:GP_001:N1"})
    assert value["claims"][0]["graph_refs"] == ["G:GP_001:N1", "UNKNOWN:N9"]
    assert report == {
        "missing_graph_prefixes_restored": 1,
        "duplicate_graph_refs_removed": 1,
    }


def test_graph_sha_tamper_is_rejected(tmp_path: Path) -> None:
    graph = tmp_path / "graph.sqlite3"
    manifest = tmp_path / "GRAPH_MANIFEST.json"
    _empty_graph(graph, manifest)
    graph.write_bytes(graph.read_bytes() + b"tamper")
    settings = Settings(graph_db=graph, graph_manifest=manifest)
    try:
        settings.validate()
    except ValueError as exc:
        assert "SHA-256" in str(exc)
    else:
        raise AssertionError("tampered graph was not rejected")
