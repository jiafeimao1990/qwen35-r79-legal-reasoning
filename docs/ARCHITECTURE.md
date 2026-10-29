# Architecture

## Components

1. **vLLM backend** — one FP8 Qwen3.5-9B base, MTP3 speculative decoding and three independently selectable FP16 LoRAs.
2. **Role router** — fixed task-to-adapter map. It never chooses a retired or unspecified adapter.
3. **Bounded two-stage client** — every semantic stage performs one private-thinking draft and one non-thinking deterministic final call with the same adapter and full source material. A real backend tokenizer preflight precedes each generation and rejects rather than truncates over-context inputs.
4. **Reasoning graph** — a public-only SQLite FTS index of abstract legal conditions and transfer limits. Retrieval is deterministic weighted RRF; at most three distinct clusters are passed to R79.
5. **Similar-case Wiki** — a separate retrieval-only index returning one full original. Its output is never injected into the reasoning workflow.
6. **Local audit** — hashes, routing, usage and status are written below `R79_AUDIT_DIR` by default. Full requests/responses and private drafts are saved only with the explicit `R79_AUDIT_MODE=full` opt-in and are never returned by the API.

## Fixed routing

| Stage | Adapter / engine | Native requests |
|---|---|---:|
| Fact and evidence binding | `facts_1949` | 2 |
| Procedure and timeline | `procedure_1978` | 2 |
| Graph retrieval | local SQLite FTS | 0 |
| Legal application and final answer | `candidate_r79` | 2 |
| Similar-case lookup | local SQLite FTS, separate endpoint | 0 |

Total per legal workflow: 6 generation requests plus 6 tokenizer preflights. A process-wide semaphore limits concurrent backend traffic to eight. The hard public generation budget accepts 6–8 and rejects anything outside it.

## Evidence discipline

- Raw materials are preserved as exact paragraph text with immutable `Mxxx:Pxxxx` references and SHA-256 bindings.
- Dates, numbers and identities that are absent or OCR-damaged must remain unknown.
- Applicant, respondent, decision maker, delivery actor and third party are distinct roles.
- A party's assertion is not silently converted into a proved fact.
- Graph nodes are conditions, not evidence. Unsupported or unknown necessary premises block downstream application.
- Specialist and final outputs use strict structured schemas. All source and graph references are checked against the actual catalogs; unknown references fail closed.

## Model service

The backend command in `scripts/start_backend.sh` is the portable form of the tested launch:

- offline compressed-tensors FP8_DYNAMIC base;
- MTP tensors, embeddings, norms and other excluded tensors retained in BF16;
- LoRA tensors loaded as FP16;
- MTP speculative token count fixed at 3;
- adapters `facts_1949`, `procedure_1978`, `candidate_r79`;
- maximum three active LoRAs and rank 16.

The repository intentionally does not reuse the older internal 1949/1978/2026 router by renaming its legal adapter. This is a clean R79 implementation with its own tests and explicit route map.

The published 320-question semantic evaluation covered the R79 graph A/B path, not this new three-adapter orchestration as a whole. The public full-chain router has installation, schema, reference, context-budget and mock integration tests; it does not claim a separate three-adapter semantic acceptance.

