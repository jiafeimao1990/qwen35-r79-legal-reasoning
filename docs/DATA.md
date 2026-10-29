# Data card and privacy boundary

## Included

- `data/public_patterns.jsonl`: 1,030 abstract reasoning patterns.
- `src/r79_legal_reasoning/data/graph.sqlite3`: deterministic FTS index rebuilt exclusively from the public patterns and included in installed wheels.
- `src/r79_legal_reasoning/data/GRAPH_MANIFEST.json`: counts and SHA-256 bindings checked at runtime.
- `data/wiki_demo.jsonl`: two synthetic records used only to demonstrate the retrieval-only Wiki endpoint.

Each public pattern contains an abstract issue, scope, typed nodes, parent/operator relationships and transfer limits. Source-cluster identity is replaced by a one-way hash used only for retrieval deduplication. The release excludes case identities, local paths, private targets, source paragraphs, node provenance and model reasoning traces.

## Not included

The internal Wiki view contains 4,382 compiled full-text records, plus 68 `needs_review` and 53 `unusable` records. A release audit found many identity-card, telephone, account-number and detailed-address patterns and no complete per-source redistribution-license inventory. Publishing the raw originals would expose personal data and unverified rights.

For that reason the public repository does not distribute those originals or their 120+ MB index. This is an intentional safety boundary, not a missing download.

## Building your own Wiki

Prepare UTF-8 JSONL rows:

```json
{"source_id":"unique-id","title":"title","source_type":"decision","full_original":"complete text"}
```

After reviewing privacy and confirming redistribution/use rights:

```bash
r79-legal build-wiki \
  --input my_rights_cleared_sources.jsonl \
  --output runtime/wiki.sqlite3 \
  --privacy-reviewed --rights-confirmed
```

The generated index is local. The Wiki endpoint returns the most relevant complete original and reports a lexical retrieval score that is explicitly not a confidence probability. It makes zero model calls and never injects results into `/v1/legal/assist`.

