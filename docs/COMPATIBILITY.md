# Runtime compatibility

The public runtime was exercised end to end on an NVIDIA RTX PRO 4500 Blackwell with
vLLM 0.27.1. The smoke used the published FP8 base, the FP16 1949/1978/R79 adapters,
MTP speculative decoding with three draft tokens, and the bundled public graph.

One synthetic administrative-reconsideration input completed with:

- 3 logical stages: `facts_1949`, `procedure_1978`, `candidate_r79`;
- 6 native generation requests, all HTTP 200 with `finish_reason=stop`;
- 6 real `/tokenize` preflights before generation;
- 12 complete private audit events;
- deterministic duplicate removal, actor/action binding and graph-reference normalization;
- Wiki injection disabled, as required by the retrieval-only boundary.

The final smoke result SHA-256 was
`554eec8619220e69f5f6a6874b92d69345f5515de3596fd4f299cc2428548503`.
This is an engineering compatibility check, not a legal-quality score or production
acceptance. See `EVALUATION.md` for the separate historical evaluation and its limits.
