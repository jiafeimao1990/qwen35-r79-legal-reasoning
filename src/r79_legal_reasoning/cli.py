from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from huggingface_hub import snapshot_download

from .settings import Settings
from .wiki import SimilarCaseWiki
from .wiki_build import build_wiki_index
from .workflow import LegalWorkflow, Material


def _read_payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="r79-legal")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("health")
    bootstrap = sub.add_parser("download-model")
    bootstrap.add_argument("--repo", default=None)
    bootstrap.add_argument("--revision", default=None)
    bootstrap.add_argument("--destination", type=Path, default=None)
    assist = sub.add_parser("assist")
    assist.add_argument("--input", type=Path, required=True)
    search = sub.add_parser("wiki-search")
    search.add_argument("--query", required=True)
    build = sub.add_parser("build-wiki")
    build.add_argument("--input", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--privacy-reviewed", action="store_true")
    build.add_argument("--rights-confirmed", action="store_true")
    args = parser.parse_args(argv)
    settings = Settings()

    if args.command == "download-model":
        repo = args.repo or settings.model_repo
        if args.repo and not args.revision:
            parser.error("a custom --repo requires an explicit --revision")
        revision = args.revision or settings.model_revision
        destination = (args.destination or settings.model_dir).resolve()
        path = snapshot_download(
            repo_id=repo,
            revision=revision,
            local_dir=destination,
        )
        print(
            json.dumps(
                {"repo": repo, "revision": revision, "path": path},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "health":
        settings.validate()
        print(
            json.dumps(
                {
                    "status": "ok",
                    "model_repo": settings.model_repo,
                    "model_revision": settings.model_revision,
                    "model_dir": str(settings.model_dir),
                    "graph_db": str(settings.graph_db),
                    "wiki_available": settings.wiki_db.is_file(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "assist":
        payload = _read_payload(args.input)
        result = LegalWorkflow(settings).run(
            payload["user_request"],
            [Material(title=item["title"], text=item["text"]) for item in payload["raw_materials"]],
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "wiki-search":
        print(
            json.dumps(
                SimilarCaseWiki(settings.wiki_db).search(args.query), ensure_ascii=False, indent=2
            )
        )
        return 0
    if args.command == "build-wiki":
        if not args.privacy_reviewed or not args.rights_confirmed:
            parser.error("build-wiki requires --privacy-reviewed and --rights-confirmed")
        print(json.dumps(build_wiki_index(args.input, args.output), ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
