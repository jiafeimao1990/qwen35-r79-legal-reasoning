from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .client import OpenAIChatClient, new_workflow_id
from .graph import ReasoningGraph
from .settings import Settings

REF_ARRAY = {
    "type": "array",
    "items": {"type": "string"},
    "minItems": 1,
    "maxItems": 16,
    "uniqueItems": True,
}
EVIDENCE_STATUS = {"type": "string", "enum": ["proved", "asserted", "contradicted", "unknown"]}
DATE_STATUS = {"type": "string", "enum": ["exact", "partial", "unknown"]}
ACTOR_ID = {"type": "string", "pattern": "^A[0-9]{3,}$"}
EVENT_ID = {"type": "string", "pattern": "^E[0-9]{3,}$"}
EVIDENCE_ID = {"type": "string", "pattern": "^EV[0-9]{3,}$"}
STEP_ID = {"type": "string", "pattern": "^S[0-9]{3,}$"}

FACT_SCHEMA = {
    "type": "object",
    "properties": {
        "actors": {
            "type": "array",
            "minItems": 1,
            "maxItems": 12,
            "items": {
                "type": "object",
                "properties": {
                    "actor_id": ACTOR_ID,
                    "name_as_stated": {"type": "string"},
                    "role": {"type": "string"},
                    "evidence_status": EVIDENCE_STATUS,
                    "source_refs": REF_ARRAY,
                },
                "required": [
                    "actor_id",
                    "name_as_stated",
                    "role",
                    "evidence_status",
                    "source_refs",
                ],
                "additionalProperties": False,
            },
        },
        "events": {
            "type": "array",
            "minItems": 1,
            "maxItems": 24,
            "items": {
                "type": "object",
                "properties": {
                    "event_id": EVENT_ID,
                    "actor_ids": {
                        "type": "array",
                        "items": ACTOR_ID,
                        "minItems": 1,
                        "maxItems": 12,
                    },
                    "action": {"type": "string"},
                    "object": {"type": "string"},
                    "date_text": {"type": "string"},
                    "date_status": DATE_STATUS,
                    "evidence_status": EVIDENCE_STATUS,
                    "source_refs": REF_ARRAY,
                },
                "required": [
                    "event_id",
                    "actor_ids",
                    "action",
                    "object",
                    "date_text",
                    "date_status",
                    "evidence_status",
                    "source_refs",
                ],
                "additionalProperties": False,
            },
        },
        "evidence": {
            "type": "array",
            "minItems": 1,
            "maxItems": 24,
            "items": {
                "type": "object",
                "properties": {
                    "evidence_id": EVIDENCE_ID,
                    "description": {"type": "string"},
                    "supports_event_ids": {
                        "type": "array",
                        "items": EVENT_ID,
                        "maxItems": 24,
                    },
                    "status": EVIDENCE_STATUS,
                    "source_refs": REF_ARRAY,
                },
                "required": [
                    "evidence_id",
                    "description",
                    "supports_event_ids",
                    "status",
                    "source_refs",
                ],
                "additionalProperties": False,
            },
        },
        "uncertainties": {
            "type": "array",
            "maxItems": 16,
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "reason": {"type": "string"},
                    "source_refs": REF_ARRAY,
                },
                "required": ["field", "reason", "source_refs"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["actors", "events", "evidence", "uncertainties"],
    "additionalProperties": False,
}

PROCEDURE_SCHEMA = {
    "type": "object",
    "properties": {
        "actors": {
            "type": "array",
            "minItems": 1,
            "maxItems": 12,
            "items": {
                "type": "object",
                "properties": {
                    "actor_id": ACTOR_ID,
                    "name_as_stated": {"type": "string"},
                    "role": {"type": "string"},
                    "evidence_status": EVIDENCE_STATUS,
                    "source_refs": REF_ARRAY,
                },
                "required": [
                    "actor_id",
                    "name_as_stated",
                    "role",
                    "evidence_status",
                    "source_refs",
                ],
                "additionalProperties": False,
            },
        },
        "decision_maker_actor_id": ACTOR_ID,
        "challenged_action": {
            "type": "object",
            "properties": {
                "event_id": EVENT_ID,
                "actor_id": ACTOR_ID,
                "description": {"type": "string"},
                "evidence_status": EVIDENCE_STATUS,
                "source_refs": REF_ARRAY,
            },
            "required": [
                "event_id",
                "actor_id",
                "description",
                "evidence_status",
                "source_refs",
            ],
            "additionalProperties": False,
        },
        "steps": {
            "type": "array",
            "maxItems": 24,
            "items": {
                "type": "object",
                "properties": {
                    "step_id": STEP_ID,
                    "actor_id": ACTOR_ID,
                    "action": {"type": "string"},
                    "date_text": {"type": "string"},
                    "date_status": DATE_STATUS,
                    "evidence_status": EVIDENCE_STATUS,
                    "source_refs": REF_ARRAY,
                },
                "required": [
                    "step_id",
                    "actor_id",
                    "action",
                    "date_text",
                    "date_status",
                    "evidence_status",
                    "source_refs",
                ],
                "additionalProperties": False,
            },
        },
        "deadlines": {
            "type": "array",
            "maxItems": 16,
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "date_status": DATE_STATUS,
                    "source_refs": REF_ARRAY,
                },
                "required": ["description", "start_date", "end_date", "date_status", "source_refs"],
                "additionalProperties": False,
            },
        },
        "unknowns": {
            "type": "array",
            "maxItems": 16,
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "reason": {"type": "string"},
                    "source_refs": REF_ARRAY,
                },
                "required": ["field", "reason", "source_refs"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "actors",
        "decision_maker_actor_id",
        "challenged_action",
        "steps",
        "deadlines",
        "unknowns",
    ],
    "additionalProperties": False,
}

FINAL_SCHEMA = {
    "type": "object",
    "properties": {
        "conclusion": {"type": "string"},
        "analysis": {"type": "string"},
        "claims": {
            "type": "array",
            "minItems": 1,
            "maxItems": 24,
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "source_refs": REF_ARRAY,
                    "graph_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 16,
                        "uniqueItems": True,
                    },
                    "evidence_status": EVIDENCE_STATUS,
                },
                "required": ["claim", "source_refs", "graph_refs", "evidence_status"],
                "additionalProperties": False,
            },
        },
        "limitations": {"type": "array", "items": {"type": "string"}, "maxItems": 16},
    },
    "required": ["conclusion", "analysis", "claims", "limitations"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class Material:
    title: str
    text: str


def _source_catalog(materials: list[Material]) -> tuple[list[dict[str, Any]], set[str]]:
    catalog = []
    refs: set[str] = set()
    for material_index, material in enumerate(materials, start=1):
        material_id = f"M{material_index:03d}"
        pieces = material.text.splitlines(keepends=True) or [material.text]
        if not any(piece.strip() for piece in pieces):
            raise ValueError(f"material {material_index} contains no visible text")
        paragraphs = []
        for paragraph_index, piece in enumerate(pieces, start=1):
            ref = f"{material_id}:P{paragraph_index:04d}"
            refs.add(ref)
            paragraphs.append({"ref": ref, "text": piece, "visible": bool(piece.strip())})
        catalog.append(
            {
                "material_id": material_id,
                "title": material.title,
                "text_sha256": hashlib.sha256(material.text.encode("utf-8")).hexdigest(),
                "original_characters": len(material.text),
                "paragraphs": paragraphs,
            }
        )
    return catalog, refs


def _all_values(value: Any, key_name: str) -> list[str]:
    result = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == key_name:
                if not isinstance(child, list):
                    raise TypeError(f"{key_name} must be an array")
                result.extend(str(item) for item in child)
            else:
                result.extend(_all_values(child, key_name))
    elif isinstance(value, list):
        for child in value:
            result.extend(_all_values(child, key_name))
    return result


def _validate_refs(value: dict[str, Any], source_refs: set[str], graph_refs: set[str]) -> None:
    unknown_source = sorted(set(_all_values(value, "source_refs")) - source_refs)
    if unknown_source:
        raise RuntimeError(f"model returned unknown source refs: {unknown_source}")
    unknown_graph = sorted(set(_all_values(value, "graph_refs")) - graph_refs)
    if unknown_graph:
        raise RuntimeError(f"model returned unknown graph refs: {unknown_graph}")


def _unique_ids(rows: list[dict[str, Any]], field: str, label: str) -> set[str]:
    values = [str(row.get(field, "")).strip() for row in rows]
    if not values or any(not value for value in values) or len(set(values)) != len(values):
        raise RuntimeError(f"{label} IDs must be nonblank and unique")
    return set(values)


def _dedupe_rows(
    rows: list[dict[str, Any]], id_field: str | None = None
) -> tuple[list[dict[str, Any]], dict[str, str], int]:
    retained: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    aliases: dict[str, str] = {}
    for row in rows:
        semantic = {key: child for key, child in row.items() if key != id_field}
        key = json.dumps(semantic, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        row_id = str(row[id_field]) if id_field else ""
        if key in seen:
            if id_field:
                aliases[row_id] = seen[key]
            continue
        retained.append(row)
        if id_field:
            aliases[row_id] = row_id
            seen[key] = row_id
        else:
            seen[key] = key
    return retained, aliases, len(rows) - len(retained)


def _remap_unique(values: list[str], aliases: dict[str, str]) -> list[str]:
    result: list[str] = []
    for value in values:
        mapped = aliases.get(value, value)
        if mapped not in result:
            result.append(mapped)
    return result


def _normalize_facts(value: dict[str, Any]) -> dict[str, int]:
    value["actors"], actor_aliases, actor_removed = _dedupe_rows(value["actors"], "actor_id")
    for event in value["events"]:
        event["actor_ids"] = _remap_unique(event["actor_ids"], actor_aliases)
    value["events"], event_aliases, event_removed = _dedupe_rows(value["events"], "event_id")
    for evidence in value["evidence"]:
        evidence["supports_event_ids"] = _remap_unique(
            evidence["supports_event_ids"], event_aliases
        )
    value["evidence"], _, evidence_removed = _dedupe_rows(value["evidence"], "evidence_id")
    value["uncertainties"], _, uncertainty_removed = _dedupe_rows(value["uncertainties"])
    return {
        "duplicate_actors_removed": actor_removed,
        "duplicate_events_removed": event_removed,
        "duplicate_evidence_removed": evidence_removed,
        "duplicate_uncertainties_removed": uncertainty_removed,
    }


def _normalize_procedure(value: dict[str, Any]) -> dict[str, int | bool]:
    value["actors"], actor_aliases, actor_removed = _dedupe_rows(value["actors"], "actor_id")
    action_actor = actor_aliases.get(
        value["challenged_action"]["actor_id"], value["challenged_action"]["actor_id"]
    )
    value["challenged_action"]["actor_id"] = action_actor
    for step in value["steps"]:
        step["actor_id"] = actor_aliases.get(step["actor_id"], step["actor_id"])
    value["steps"], _, step_removed = _dedupe_rows(value["steps"], "step_id")
    value["deadlines"], _, deadline_removed = _dedupe_rows(value["deadlines"])
    value["unknowns"], _, unknown_removed = _dedupe_rows(value["unknowns"])
    value["decision_maker_actor_id"] = action_actor
    return {
        "duplicate_actors_removed": actor_removed,
        "duplicate_steps_removed": step_removed,
        "duplicate_deadlines_removed": deadline_removed,
        "duplicate_unknowns_removed": unknown_removed,
        "decision_maker_derived_from_challenged_action": True,
    }


def _validate_facts(value: dict[str, Any]) -> None:
    actor_ids = _unique_ids(value["actors"], "actor_id", "fact actor")
    event_ids = _unique_ids(value["events"], "event_id", "fact event")
    _unique_ids(value["evidence"], "evidence_id", "fact evidence")
    for event in value["events"]:
        unknown = set(event["actor_ids"]) - actor_ids
        if unknown:
            raise RuntimeError(
                f"event {event['event_id']} refers to unknown actors: {sorted(unknown)}"
            )
    for evidence in value["evidence"]:
        unknown = set(evidence["supports_event_ids"]) - event_ids
        if unknown:
            raise RuntimeError(
                f"evidence {evidence['evidence_id']} refers to unknown events: {sorted(unknown)}"
            )


def _validate_procedure(value: dict[str, Any]) -> None:
    actor_ids = _unique_ids(value["actors"], "actor_id", "procedure actor")
    _unique_ids(value["steps"], "step_id", "procedure step") if value["steps"] else set()
    decision_id = value["decision_maker_actor_id"]
    if decision_id not in actor_ids:
        raise RuntimeError("decision_maker_actor_id does not refer to a procedure actor")
    action_actor = value["challenged_action"]["actor_id"]
    if action_actor not in actor_ids or action_actor != decision_id:
        raise RuntimeError("challenged action is not bound to the decision-maker actor")
    for step in value["steps"]:
        if step["actor_id"] not in actor_ids:
            raise RuntimeError(f"procedure step {step['step_id']} refers to an unknown actor")


def _align_decision_maker(facts: dict[str, Any], procedure: dict[str, Any]) -> dict[str, Any]:
    procedure_actor = next(
        row
        for row in procedure["actors"]
        if row["actor_id"] == procedure["decision_maker_actor_id"]
    )
    normalized = "".join(str(procedure_actor["name_as_stated"]).split()).lower()
    name_matches = [
        row
        for row in facts["actors"]
        if "".join(str(row["name_as_stated"]).split()).lower() == normalized
    ]
    candidates = name_matches
    if len(name_matches) > 1:
        candidates = [
            row
            for row in name_matches
            if set(row["source_refs"]).intersection(procedure_actor["source_refs"])
        ]
    if len(candidates) > 1:

        def role_score(row: dict[str, Any]) -> int:
            role = str(row.get("role", ""))
            if "作出" in role:
                return 3
            if "被申请人" in role or "行政机关" in role:
                return 2
            if "复议机关" in role:
                return 0
            return 1

        best = max(role_score(row) for row in candidates)
        candidates = [row for row in candidates if role_score(row) == best]
    if len(candidates) != 1:
        raise RuntimeError(
            "decision maker could not be aligned uniquely between facts and procedure by name/source"
        )
    return {
        "fact_actor_id": candidates[0]["actor_id"],
        "procedure_actor_id": procedure_actor["actor_id"],
        "name_as_stated": procedure_actor["name_as_stated"],
        "shared_source_refs": sorted(
            set(candidates[0]["source_refs"]).intersection(procedure_actor["source_refs"])
        ),
        "match_basis": "name_and_source"
        if set(candidates[0]["source_refs"]).intersection(procedure_actor["source_refs"])
        else "unique_normalized_name",
    }


class LegalWorkflow:
    """Three-role, six-generation-request workflow with deterministic graph retrieval."""

    def __init__(self, settings: Settings | None = None, client: OpenAIChatClient | None = None):
        self.settings = settings or Settings()
        self.settings.validate()
        self.client = client or OpenAIChatClient(
            self.settings.vllm_url,
            self.settings.timeout_seconds,
            self.settings.audit_dir,
            audit_mode=self.settings.audit_mode,
            max_model_len=self.settings.max_model_len,
        )
        self.graph = ReasoningGraph(self.settings.graph_db)

    def run(self, user_request: str, materials: list[Material]) -> dict[str, Any]:
        if not user_request.strip():
            raise ValueError("user_request must not be blank")
        if not materials:
            raise ValueError("at least one raw material is required")
        if len(materials) > 99:
            raise ValueError("at most 99 raw materials are accepted")

        source_catalog, allowed_source_refs = _source_catalog(materials)
        original = {"user_request": user_request, "source_catalog": source_catalog}
        source_json = json.dumps(original, ensure_ascii=False, separators=(",", ":"))
        workflow_id = new_workflow_id()
        start_requests = self.client.native_requests

        facts = self.client.bounded_two_stage(
            adapter=self.settings.facts_adapter,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是事实与证据整理专员。只依据source_catalog，逐一绑定主体、事件、日期、"
                        "证据状态和实际段落ref。残缺日期、号码或身份不得补写；当事人主张与已证明事实"
                        "必须分开；actor_id/event_id/evidence_id须在本次输出内唯一；按JSON返回。"
                    ),
                },
                {"role": "user", "content": source_json},
            ],
            response_schema=FACT_SCHEMA,
            workflow_id=workflow_id,
            label="facts_1949",
            reasoning_budget=self.settings.reasoning_budget,
            final_budget=self.settings.final_budget,
        )
        facts_normalization = _normalize_facts(facts)
        _validate_refs(facts, allowed_source_refs, set())
        _validate_facts(facts)

        procedure = self.client.bounded_two_stage(
            adapter=self.settings.procedure_adapter,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是行政程序与时序专员。只依据source_catalog识别行为作出者、被复议行为、"
                        "程序步骤、日期状态和期限，每项绑定实际段落ref。先建立本阶段唯一actors表，"
                        "所有step和challenged_action只能引用表内actor_id；被挑战行为的actor_id必须等于"
                        "decision_maker_actor_id。不得从残缺OCR推算日期，不得混淆申请人、被申请人、"
                        "送达者和其他机关；按JSON返回。"
                    ),
                },
                {"role": "user", "content": source_json},
            ],
            response_schema=PROCEDURE_SCHEMA,
            workflow_id=workflow_id,
            label="procedure_1978",
            reasoning_budget=self.settings.reasoning_budget,
            final_budget=self.settings.final_budget,
        )
        procedure_normalization = _normalize_procedure(procedure)
        _validate_refs(procedure, allowed_source_refs, set())
        _validate_procedure(procedure)
        actor_alignment = _align_decision_maker(facts, procedure)

        # Retrieval is intentionally source-only. Specialist/model output never changes search terms.
        retrieval_text = "\n".join([user_request, *(material.text for material in materials)])
        graphs = self.graph.retrieve(retrieval_text, user_request, limit=3)
        allowed_graph_refs = {
            f"G:{row['pattern_id']}:{node['id']}"
            for row in graphs
            for node in row["graph"].get("nodes", [])
        }
        final_input = {
            **original,
            "fact_specialist": facts,
            "procedure_specialist": procedure,
            "cross_stage_decision_maker_alignment": actor_alignment,
            "abstract_reasoning_graphs": [
                {"pattern_id": row["pattern_id"], "graph": row["graph"]} for row in graphs
            ],
        }
        final = self.client.bounded_two_stage(
            adapter=self.settings.reasoning_adapter,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是最终法律分析专员。source_catalog是本案事实的唯一来源；专员输出须回到"
                        "段落ref核验。外挂图谱只是抽象条件，不是本案事实、法律金标准或预设结论。先绑定"
                        "主体—事件—日期—证据状态，再逐项检查必要前提；未知或不支持的必要前提阻断下游"
                        "结论。不得补写日期、号码、主体或救济路径。每个claims项必须引用真实source_refs；"
                        "使用图节点时graph_refs写G:pattern_id:node_id，不使用则空数组。仅按指定JSON返回。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(final_input, ensure_ascii=False, separators=(",", ":")),
                },
            ],
            response_schema=FINAL_SCHEMA,
            workflow_id=workflow_id,
            label="candidate_r79",
            reasoning_budget=self.settings.reasoning_budget,
            final_budget=self.settings.final_budget,
        )
        _validate_refs(final, allowed_source_refs, allowed_graph_refs)
        used = self.client.native_requests - start_requests
        if used > self.settings.max_backend_requests:
            raise RuntimeError(
                f"workflow exceeded generation request budget: {used}>"
                f"{self.settings.max_backend_requests}"
            )
        return {
            "workflow_id": workflow_id,
            "backend_generation_requests": used,
            "tokenizer_preflights": 6,
            "routing": {
                "facts": self.settings.facts_adapter,
                "procedure": self.settings.procedure_adapter,
                "final": self.settings.reasoning_adapter,
                "graph": "deterministic_local_fts_source_only",
                "wiki_injected": False,
            },
            "selected_graphs": graphs,
            "facts": facts,
            "procedure": procedure,
            "deterministic_normalization": {
                "facts": facts_normalization,
                "procedure": procedure_normalization,
            },
            "answer": final,
        }
