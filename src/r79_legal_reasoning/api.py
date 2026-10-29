from __future__ import annotations

import json
import urllib.error
import urllib.request

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .settings import Settings
from .wiki import SimilarCaseWiki
from .workflow import LegalWorkflow, Material


class MaterialInput(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=1)


class AssistInput(BaseModel):
    user_request: str = Field(min_length=1, max_length=20_000)
    raw_materials: list[MaterialInput] = Field(min_length=1, max_length=99)


class SearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=8000)


settings = Settings()
app = FastAPI(title="R79 legal reasoning", version="1.0.0")


def _backend_health() -> dict[str, object]:
    request = urllib.request.Request(f"{settings.vllm_url}/models", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            value = json.loads(response.read().decode("utf-8"))
            return {"reachable": response.status == 200, "status": response.status, "models": value}
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {"reachable": False, "error": type(exc).__name__}


@app.get("/health")
def health() -> dict[str, object]:
    wiki = SimilarCaseWiki(settings.wiki_db)
    errors = []
    try:
        settings.validate()
    except (ValueError, FileNotFoundError) as exc:
        errors.append(str(exc))
    backend = _backend_health()
    return {
        "status": "ok" if not errors and backend["reachable"] else "degraded",
        "model_repo": settings.model_repo,
        "model_revision": settings.model_revision,
        "vllm_url": settings.vllm_url,
        "backend": backend,
        "graph_verified": not errors,
        "wiki_available": wiki.available,
        "routes": ["facts_1949", "procedure_1978", "candidate_r79"],
        "excluded": ["2008", "2026"],
        "errors": errors,
    }


@app.post("/v1/legal/assist")
def assist(payload: AssistInput) -> dict[str, object]:
    try:
        workflow = LegalWorkflow(settings)
        return workflow.run(
            payload.user_request,
            [Material(title=item.title, text=item.text) for item in payload.raw_materials],
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/v1/wiki/similar-case/search")
def similar_case(payload: SearchInput) -> dict[str, object]:
    try:
        return SimilarCaseWiki(settings.wiki_db).search(payload.query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
