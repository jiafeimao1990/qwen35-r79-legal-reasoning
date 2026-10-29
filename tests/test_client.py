from __future__ import annotations

import http.server
import json
import threading
from pathlib import Path
from typing import ClassVar

from r79_legal_reasoning.client import OpenAIChatClient


class Handler(http.server.BaseHTTPRequestHandler):
    generation_bodies: ClassVar[list[dict]] = []
    tokenize_bodies: ClassVar[list[dict]] = []
    token_count: ClassVar[int] = 16
    generation_error_status: ClassVar[int | None] = None

    def log_message(self, format, *args):
        return

    def do_POST(self):
        length = int(self.headers["content-length"])
        body = json.loads(self.rfile.read(length))
        if self.path == "/tokenize":
            self.tokenize_bodies.append(body)
            value = {"count": self.token_count, "max_model_len": 16384}
            status = 200
        else:
            self.generation_bodies.append(body)
            if self.generation_error_status is not None:
                status = self.generation_error_status
                value = {"error": {"message": "guided decoding unavailable"}}
            elif len(self.generation_bodies) == 1:
                status = 200
                message = {"content": "draft", "reasoning_content": "private reasoning"}
                value = {
                    "choices": [{"message": message, "finish_reason": "stop"}],
                    "usage": {"total_tokens": 1},
                }
            else:
                status = 200
                message = {"content": '{"answer":"ok"}', "reasoning_content": ""}
                value = {
                    "choices": [{"message": message, "finish_reason": "stop"}],
                    "usage": {"total_tokens": 1},
                }
        raw = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def test_bounded_two_stage_keeps_adapter_and_private_audit(tmp_path: Path) -> None:
    Handler.generation_bodies = []
    Handler.tokenize_bodies = []
    Handler.token_count = 16
    Handler.generation_error_status = None
    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = OpenAIChatClient(
            f"http://127.0.0.1:{server.server_port}/v1", 5, tmp_path / "audit"
        )
        value = client.bounded_two_stage(
            adapter="candidate_r79",
            messages=[{"role": "user", "content": "source"}],
            response_schema={
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "uniqueItems": True,
                    },
                },
                "required": ["answer"],
                "additionalProperties": False,
            },
            workflow_id="w1",
            label="test",
            reasoning_budget=32,
            final_budget=32,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert value == {"answer": "ok"}
    assert client.native_requests == 2
    assert client.tokenizer_preflights == 2
    assert [body["model"] for body in Handler.generation_bodies] == [
        "candidate_r79",
        "candidate_r79",
    ]
    assert Handler.generation_bodies[0]["chat_template_kwargs"]["enable_thinking"] is True
    assert "最多12条" in Handler.generation_bodies[0]["messages"][-1]["content"]
    assert Handler.generation_bodies[0]["repetition_penalty"] == 1.05
    assert Handler.generation_bodies[1]["chat_template_kwargs"]["enable_thinking"] is False
    assert Handler.generation_bodies[1]["repetition_penalty"] == 1.05
    guided = Handler.generation_bodies[1]["response_format"]["json_schema"]["schema"]
    assert "uniqueItems" not in guided["properties"]["tags"]
    assert "private reasoning" in Handler.generation_bodies[1]["messages"][-2]["content"]
    assert "只列一次" in Handler.generation_bodies[1]["messages"][-1]["content"]
    assert '"required":["answer"]' in Handler.generation_bodies[1]["messages"][-1]["content"]
    assert '"uniqueItems":true' in Handler.generation_bodies[1]["messages"][-1]["content"]
    assert len(list((tmp_path / "audit" / "w1").glob("*.json"))) == 4


def test_context_overflow_fails_before_generation(tmp_path: Path) -> None:
    Handler.generation_bodies = []
    Handler.tokenize_bodies = []
    Handler.token_count = 16380
    Handler.generation_error_status = None
    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = OpenAIChatClient(
            f"http://127.0.0.1:{server.server_port}/v1", 5, tmp_path / "audit"
        )
        try:
            client.bounded_two_stage(
                adapter="candidate_r79",
                messages=[{"role": "user", "content": "source"}],
                response_schema={"type": "object"},
                workflow_id="w2",
                label="overflow",
                reasoning_budget=32,
                final_budget=32,
            )
        except RuntimeError as exc:
            assert "context budget exceeded" in str(exc)
        else:
            raise AssertionError("overflow was not rejected")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert Handler.generation_bodies == []


def test_http_error_is_reported_without_choices_keyerror(tmp_path: Path) -> None:
    Handler.generation_bodies = []
    Handler.tokenize_bodies = []
    Handler.token_count = 16
    Handler.generation_error_status = 500
    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = OpenAIChatClient(
            f"http://127.0.0.1:{server.server_port}/v1", 5, tmp_path / "audit"
        )
        try:
            client.bounded_two_stage(
                adapter="candidate_r79",
                messages=[{"role": "user", "content": "source"}],
                response_schema={"type": "object"},
                workflow_id="w3",
                label="server_error",
                reasoning_budget=32,
                final_budget=32,
            )
        except RuntimeError as exc:
            assert "vLLM HTTP 500" in str(exc)
            assert "guided decoding unavailable" in str(exc)
        else:
            raise AssertionError("HTTP error was not surfaced")
    finally:
        Handler.generation_error_status = None
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert len(list((tmp_path / "audit" / "w3").glob("*.json"))) == 2
